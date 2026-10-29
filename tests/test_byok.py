import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import requests
from streamlit.testing.v1 import AppTest
from byok import disconnect, expire_credentials, redact
from chat_stream import stream_chat
from api_errors import error_message
from agent import GeminiError

class BYOK(unittest.TestCase):
    def test_disconnect_and_expiry(self):
        state = {'chat_key_Gemini': 'secret', 'credential_voice': 'voice', 'messages': [1],
                 'qa_document': 'private', 'credential_activity': 1}
        self.assertTrue(expire_credentials(state, 1802))
        self.assertEqual(state['chat_key_Gemini'], '')
        self.assertEqual(state['credential_voice'], '')
        self.assertNotIn('qa_document', state)
        self.assertEqual(state['messages'], [])
        self.assertEqual(redact('secret hello', {'chat_key_Gemini': 'secret'}), '[credential removed] hello')

    def test_sessions_and_clear_button(self):
        path = str(Path(__file__).resolve().parents[1] / 'app.py')
        first, second = AppTest.from_file(path).run(), AppTest.from_file(path).run()
        first.text_input(key='chat_key_Gemini').set_value('fake-session-one').run()
        first.text_input(key='credential_voice').set_value('voice-only').run()
        self.assertEqual(second.text_input(key='chat_key_Gemini').value, '')
        next(b for b in first.button if b.label == 'Disconnect / Clear credentials').click().run()
        self.assertFalse(first.exception)
        self.assertEqual(first.text_input(key='chat_key_Gemini').value, '')
        self.assertEqual(first.text_input(key='credential_voice').value, '')
        self.assertTrue(first.chat_input[0].disabled)

    def test_error_categories(self):
        for status, body, fragment in [(400, {'code': 'API_KEY_INVALID'}, 'Invalid API key'),
                (401, {}, 'Unauthorized'), (403, {}, 'forbidden'), (404, {}, 'unavailable'),
                (429, {}, 'Rate limit'), (429, {'code': 'insufficient_quota'}, 'Credits')]:
            response = Mock(status_code=status)
            response.json.return_value = {'error': {**body, 'message': 'secret-credential'}}
            message = error_message('OpenAI', response)
            self.assertIn(fragment, message)
            self.assertNotIn('secret-credential', message)

    @patch('chat_stream.requests.post')
    def test_streaming_providers(self, post):
        for provider in ['Gemini', 'OpenAI']:
            response = Mock(status_code=200)
            if provider == 'Gemini':
                events = [{'candidates': [{'content': {'parts': [{'text': 'Hi'}]}}]},
                          {'candidates': [{'content': {'parts': [{'text': '!'}]}, 'finishReason': 'STOP'}]}]
            else:
                events = [{'choices': [{'delta': {'content': 'Hi'}, 'finish_reason': None}]},
                          {'choices': [{'delta': {'content': '!'}, 'finish_reason': 'stop'}]}]
            response.iter_lines.return_value = [line for event in events for line in [('data: ' + json.dumps(event)).encode(), b'']]
            post.return_value.__enter__ = Mock(return_value=response)
            post.return_value.__exit__ = Mock(return_value=False)
            updates = []
            result = stream_chat(provider, 'private-test-key', 'test-model', [{'role': 'user', 'content': 'Hello'}], 'English', .8, 100, updates.append)
            self.assertEqual(updates, ['Hi', 'Hi!'])
            self.assertEqual(result['content'], 'Hi!')
            self.assertNotIn('private-test-key', post.call_args.args[0])
            self.assertNotIn('private-test-key', str(post.call_args.kwargs['json']))
            self.assertFalse(post.call_args.kwargs['allow_redirects'])

    @patch('chat_stream.requests.post')
    def test_timeout_and_network(self, post):
        for failure, word in [(requests.Timeout('secret'), 'timed out'), (requests.ConnectionError('secret'), 'Network')]:
            post.side_effect = failure
            with self.assertRaises(GeminiError) as caught:
                stream_chat('OpenAI', 'fake', 'model', [], 'English', .8, 100, lambda text: None)
            self.assertIn(word, str(caught.exception))
            self.assertNotIn('secret', str(caught.exception))
