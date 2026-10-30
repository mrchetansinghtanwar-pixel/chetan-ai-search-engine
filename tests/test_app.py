import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent import answer, generate, google_search, GeminiError
from streamlit.testing.v1 import AppTest

def reply(parts):
    return {'candidates': [{'content': {'role': 'model', 'parts': parts}, 'finishReason': 'STOP'}]}

class Tests(unittest.TestCase):
    @patch('agent.generate')
    def test_search_roundtrip(self, gen):
        gen.side_effect = [reply([{'functionCall': {'name': 'google_search', 'args': {'query': 'q'}, 'id': 'c1'}, 'thoughtSignature': 'opaque'}]), reply([{'text': 'Done'}])]
        source = {'url': 'https://example.com', 'title': 'Example', 'snippet': 'Evidence'}
        search = Mock(return_value={'sources': [source]})
        result = answer('fake', 'test', [{'role': 'user', 'content': 'q'}], 'Hindi', search)
        self.assertEqual(result['sources'], [source])
        self.assertEqual(result['content'], 'Done')
        contents = gen.call_args.args[2]['contents']
        self.assertEqual(contents[1]['parts'][0]['thoughtSignature'], 'opaque')
        self.assertEqual(contents[2]['parts'][0]['functionResponse']['id'], 'c1')
        search.assert_called_once_with('q')

    @patch('agent.generate')
    def test_budget(self, gen):
        gen.return_value = reply([{'functionCall': {'name': 'google_search', 'args': {'query': 'q'}}}])
        search = Mock(return_value={'sources': []})
        with self.assertRaises(GeminiError):
            answer('fake', 'test', [], 'Hindi', search)
        self.assertEqual(search.call_count, 3)
        self.assertEqual(gen.call_count, 4)
        self.assertEqual(gen.call_args.args[2]['toolConfig']['functionCallingConfig']['mode'], 'NONE')

    @patch('agent.requests.post')
    def test_errors_are_sanitized(self, post):
        for code in [400, 401, 403, 404, 429, 500]:
            post.return_value.status_code = code
            post.return_value.text = 'private-key'
            with self.assertRaises(GeminiError) as error:
                generate('private-key', 'test', {})
            self.assertNotIn('private-key', str(error.exception))

    @patch('agent.generate', return_value={'promptFeedback': {'blockReason': 'SAFETY'}})
    def test_blocked(self, gen):
        with self.assertRaises(GeminiError):
            answer('fake', 'test', [], 'Hindi')

    @patch('agent.generate')
    def test_plain_chat(self, gen):
        gen.return_value = reply([{'text': 'Hi'}])
        self.assertEqual(answer('fake', 'test', [], 'Hindi')['content'], 'Hi')
        self.assertNotIn('tools', gen.call_args.args[2])

    def app(self, key=''):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=15)
        app.secrets['GEMINI_API_KEY'] = key
        app.run()
        if key:
            app.selectbox(key='chat_provider').select('Gemini').run()
            app.text_input(key='chat_key_Gemini').set_value(key).run()
        return app

    def test_missing_key(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertTrue(app.chat_input[0].disabled)

    @patch('providers.answer')
    def test_retry_and_reset(self, mocked):
        mocked.side_effect = [GeminiError('Quota limit'), {'content': 'Done', 'sources': [], 'warnings': []}]
        app = self.app('fake')
        next(t for t in app.toggle if t.label == 'Stream responses').set_value(False).run()
        app.chat_input[0].set_value('Hi').run()
        self.assertEqual(len(app.session_state['messages']), 1)
        next(b for b in app.button if b.label == 'Try again').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state['messages']), 2)
        next(b for b in app.button if b.label == 'Clear Chat').click().run()
        self.assertEqual(app.session_state['messages'], [])

if __name__ == '__main__':
    unittest.main()
