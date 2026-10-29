import unittest
from unittest.mock import patch, Mock
from providers import chat_answer, list_models, GeminiError
from streamlit.testing.v1 import AppTest
from pathlib import Path

class Providers(unittest.TestCase):
    @patch('providers.requests.request')
    def test_routing_and_private_errors(self, call):
        for provider, host in [('OpenAI', 'api.openai.com'), ('Groq', 'api.groq.com'),
                               ('Meta / Llama (via Groq)', 'api.groq.com'), ('Claude', 'api.anthropic.com')]:
            body = {'content': [{'type': 'text', 'text': 'Hello'}]} if provider == 'Claude' else {'choices': [{'message': {'content': 'Hello'}}]}
            call.return_value = Mock(status_code=200, json=lambda: body)
            result = chat_answer(provider, 'test-only', 'model', [{'role': 'user', 'content': 'Hi'}], 'English')
            self.assertEqual(result['content'], 'Hello')
            self.assertIn(host, call.call_args.args[1])
            payload = call.call_args.kwargs['json']
            self.assertIn('messages', payload)
            self.assertNotIn('test-only', str(payload))
            call.return_value = Mock(status_code=429)
            with self.assertRaises(GeminiError) as error:
                chat_answer(provider, 'test-only', 'model', [], 'English')
            self.assertNotIn('test-only', str(error.exception))

    @patch('providers.requests.request')
    def test_no_key_no_request(self, call):
        with self.assertRaises(GeminiError):
            chat_answer('OpenAI', '', 'gpt-4.1-mini', [], 'English')
        call.assert_not_called()

    @patch('providers.request')
    def test_models_and_search(self, request):
        request.return_value = {'data': [{'id': 'llama-test'}, {'id': 'whisper'}]}
        self.assertEqual(list_models('Meta / Llama (via Groq)', 'fake'), ['llama-test'])
        request.return_value = {'choices': [{'message': {'content': 'Answer'}, 'finish_reason': 'length'}]}
        history = [{'role': 'user', 'content': 'Question'}]
        search = Mock(return_value={'sources': [], 'error': 'Search unavailable'})
        result = chat_answer('Groq', 'fake', 'model', history, 'Hindi', search)
        self.assertEqual(history[0]['content'], 'Question')
        self.assertEqual(len(result['warnings']), 2)

    def test_switch_provider_and_custom_model(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        self.assertFalse(app.exception)
        app.text_input(key='chat_key_Gemini').set_value('fake').run()
        self.assertFalse(app.chat_input[0].disabled)
        app.selectbox(key='chat_provider').select('OpenAI').run()
        self.assertFalse(app.exception)
        self.assertTrue(app.chat_input[0].disabled)
        app.text_input(key='chat_key_OpenAI').set_value('fake').run()
        app.selectbox(key='model_OpenAI').select('Custom model ID').run()
        self.assertTrue(app.chat_input[0].disabled)
        app.text_input(key='custom_model_OpenAI').set_value('gpt-4.1-mini').run()
        self.assertFalse(app.chat_input[0].disabled)
