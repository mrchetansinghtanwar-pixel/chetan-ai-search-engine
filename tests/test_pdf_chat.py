import io
import unittest
from unittest.mock import patch
from reportlab.pdfgen import canvas
from pypdf import PdfWriter
from langchain_core.documents import Document
from pdf_chat import load_pdf, retrieve, answer_pdf
from agent import GeminiError
from streamlit.testing.v1 import AppTest
from pathlib import Path

def sample_pdf():
    out = io.BytesIO()
    c = canvas.Canvas(out)
    c.drawString(40, 700, 'Apples are red. This page describes fruit.')
    c.showPage()
    c.drawString(40, 700, 'The payment deadline is 30 November 2026.')
    c.save()
    return out.getvalue()

class PDFChat(unittest.TestCase):
    def test_page_retrieval(self):
        chunks, pages, empty = load_pdf(sample_pdf())
        self.assertEqual((pages, empty), (2, 0))
        self.assertEqual(retrieve(chunks, 'payment deadline')[0].metadata['page'], 2)
        self.assertEqual(retrieve(chunks, 'astronaut'), [])

    def test_invalid_and_scanned(self):
        for raw in [b'invalid', b'x' * (10 * 1024 * 1024 + 1)]:
            with self.assertRaises(ValueError):
                load_pdf(raw)
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        out = io.BytesIO()
        writer.write(out)
        with self.assertRaisesRegex(ValueError, 'OCR'):
            load_pdf(out.getvalue())
        writer.encrypt('test')
        out = io.BytesIO()
        writer.write(out)
        with self.assertRaisesRegex(ValueError, 'unlocked'):
            load_pdf(out.getvalue())

    @patch('pdf_chat.chat_answer')
    def test_grounding_and_no_key(self, chat):
        chunks, _, _ = load_pdf(sample_pdf())
        chat.return_value = {'content': '30 November [Page 2]', 'warnings': []}
        result = answer_pdf(chunks, 'payment deadline', 'OpenAI', 'fake', 'model', 'English', .2, 100)
        self.assertEqual(result['passages'][0]['page'], 2)
        prompt = chat.call_args.args[3][0]['content']
        self.assertIn('[Page 2]', prompt)
        self.assertNotIn('Apples', prompt)
        chat.reset_mock()
        answer_pdf(chunks, 'astronaut', 'OpenAI', 'fake', 'model', 'English', .2, 100)
        chat.assert_not_called()
        with self.assertRaises(GeminiError):
            answer_pdf(chunks, 'payment', 'OpenAI', '', 'model', 'English', .2, 100)
        chat.assert_not_called()

    def test_pdf_workspace(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        app.selectbox(key='workspace_mode').select('Chat with PDF').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.subheader[0].value, 'Chat with PDF')
