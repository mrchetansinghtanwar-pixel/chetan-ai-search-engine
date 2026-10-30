import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from provider_detection import detect_provider


class AutoProviderTests(unittest.TestCase):
    def test_conservative_hints(self):
        for prefix, provider in [('AIza', 'Gemini'), ('gsk_', 'Groq'),
                                  ('sk-proj-', 'OpenAI'), ('sk-svcacct-', 'OpenAI'),
                                  ('sk-ant-', 'Claude')]:
            self.assertEqual(detect_provider('  ' + prefix + 'x' * 24 + '  '), provider)
        for key in ['', None, 'sk-' + 'x' * 30, 'sk-proj-short', 'unknown-key',
                    'gsk_' + 'x' * 20 + '\nother']:
            self.assertIsNone(detect_provider(key))

    @patch('providers.requests.request')
    @patch('chat_stream.stream_chat', return_value={'content': 'Hello', 'sources': [], 'warnings': []})
    def test_auto_routing_is_local_isolated_and_clearable(self, stream, request):
        path = str(Path(__file__).resolve().parents[1] / 'app.py')
        app = AppTest.from_file(path).run()
        self.assertTrue(not app.chat_input or app.chat_input[0].disabled)
        key = 'sk-proj-' + 'x' * 24
        app.text_input(key='chat_key_auto').set_value(key).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.chat_input[0].disabled)
        request.assert_not_called()
        app.chat_input[0].set_value('Hello').run()
        self.assertEqual(stream.call_args.args[:2], ('OpenAI', key))
        other = AppTest.from_file(path).run()
        self.assertEqual(other.text_input(key='chat_key_auto').value, '')
        next(b for b in app.button if b.label == 'Disconnect / Clear credentials').click().run()
        self.assertEqual(app.text_input(key='chat_key_auto').value, '')
        self.assertTrue(not app.chat_input or app.chat_input[0].disabled)
        app.text_input(key='chat_key_auto').set_value('unrecognized-key').run()
        self.assertTrue(not app.chat_input or app.chat_input[0].disabled)
        request.assert_not_called()

    @patch('providers.requests.request')
    def test_changing_key_reselects_provider_and_model(self, request):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        for prefix, provider in [('AIza', 'Gemini'), ('gsk_', 'Groq'), ('sk-ant-', 'Claude')]:
            app.text_input(key='chat_key_auto').set_value(prefix + 'x' * 24).run()
            self.assertFalse(app.exception)
            self.assertTrue(app.selectbox(key='model_' + provider).value)
            self.assertFalse(app.chat_input[0].disabled)
        request.assert_not_called()
