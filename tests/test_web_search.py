import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from web_search import search_document, sync_home


class WebSearchTests(unittest.TestCase):
    def test_isolated_document_and_invalid_ids(self):
        html = search_document('test-engine-123', 'hello')
        self.assertIn('sandbox="allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"', html)
        self.assertNotIn('allow-same-origin', html)
        self.assertIn('https://cse.google.com/cse.js?cx=test-engine-123', html)
        self.assertNotIn('api_key', html)
        self.assertNotIn('parent.', html)
        for value in ['', None, '"><script>alert(1)</script>', 'id&key=secret']:
            with self.assertRaises(ValueError):
                search_document(value, 'hello')
        for value in ['', 'x' * 501, None]:
            with self.assertRaises(ValueError):
                search_document('test-engine-123', value)
        html = search_document('test-engine-123', '</script><script>alert(1)</script>')
        self.assertNotIn('&lt;/script&gt;&lt;script&gt;alert', html)

    def test_home_transitions_preserve_manual_navigation(self):
        state = {}
        sync_home(state, False)
        self.assertEqual(state['workspace_mode'], 'Web search')
        sync_home(state, True)
        self.assertEqual(state['workspace_mode'], 'Chat')
        state['workspace_mode'] = 'Web search'
        sync_home(state, True)
        self.assertEqual(state['workspace_mode'], 'Web search')
        state['workspace_mode'] = 'PDF tools'
        sync_home(state, False)
        sync_home(state, True)
        self.assertEqual(state['workspace_mode'], 'PDF tools')
        state['workspace_mode'] = 'Chat'
        sync_home(state, False)
        self.assertEqual(state['workspace_mode'], 'Web search')

    @patch('providers.requests.request')
    def test_search_key_chat_disconnect_flow(self, request):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key='workspace_mode').value, 'Web search')
        self.assertFalse(app.chat_input)
        app.text_input(key='chat_key_auto').set_value('sk-proj-' + 'x' * 24).run()
        self.assertEqual(app.selectbox(key='workspace_mode').value, 'Chat')
        self.assertFalse(app.chat_input[0].disabled)
        app.selectbox(key='workspace_mode').select('Web search').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key='workspace_mode').value, 'Web search')
        app.selectbox(key='workspace_mode').select('Chat').run()
        next(b for b in app.button if b.label == 'Disconnect / Clear credentials').click().run()
        self.assertEqual(app.selectbox(key='workspace_mode').value, 'Web search')
        self.assertEqual(app.text_input(key='chat_key_auto').value, '')
        request.assert_not_called()
