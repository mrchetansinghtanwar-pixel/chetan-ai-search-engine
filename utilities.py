"""Small local utilities; only voice text is sent to Google's TTS service."""
import ast
import operator
import io
import html
import streamlit as st
from download_names import pdf_filename


def calculate(expression):
    if len(expression) > 200:
        raise ValueError("The expression is too long.")
    tree = ast.parse(expression, mode="eval")
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in ops:
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(b) > 100:
                raise ValueError("The exponent must not exceed 100 in magnitude.")
            value = ops[type(node.op)](a, b)
        else:
            raise ValueError("Only numbers, parentheses and + - * / % ** are allowed.")
        if isinstance(value, complex) or abs(value) > 1e100:
            raise ValueError("The result is too large or unsupported.")
        return value
    return visit(tree.body)


def make_pdf(text):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    if any(ord(c)>255 for c in text):
        raise ValueError("Use English or Roman Hinglish text for PDF export.")
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    content = [Paragraph("Chetan AI document", styles["Title"]), Spacer(1, 16)]
    for line in text.splitlines():
        content.append(Paragraph(html.escape(line) or "<br/>", styles["BodyText"]))
        content.append(Spacer(1, 5))
    doc.build(content)
    return out.getvalue()


def show_tools(mode):
    if mode == "Calculator":
        st.subheader("Calculator")
        with st.form("calculator"):
            expression = st.text_input("Calculation", placeholder="(2500 * 18) / 100", max_chars=200)
            go = st.form_submit_button("Calculate", type="primary")
        if go:
            try: st.success(str(calculate(expression)))
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, RecursionError):
                st.error("Invalid calculation. Check numbers and operators, and avoid division by zero.")
        st.caption("+ add · - subtract · * multiply · / divide · % remainder · ** power")
    elif mode == "Text pad":
        st.subheader("Text copy / paste")
        text = st.text_area("Type or paste your text here", height=250, key="text_pad", max_chars=50000)
        st.caption(f"{len(text.split())} words · {len(text)} characters")
        if text:
            st.caption("Use the copy icon in the box below to copy all text.")
            st.code(text, language=None)
            st.download_button("Download TXT", text, "chetan-text.txt", "text/plain")
    elif mode == "Voice":
        st.subheader("Text to speech")
        st.caption("Creating audio sends your text to Google's speech service. Internet access is required; service limits may apply.")
        with st.form("voice"):
            text = st.text_area("Text to read aloud", height=150, max_chars=2000)
            lang = st.selectbox("Voice language", ["Hindi", "English"])
            slow = st.checkbox("Speak slowly")
            go = st.form_submit_button("Create audio", type="primary")
        if go and text.strip():
            try:
                from gtts import gTTS
                with st.spinner("Creating audio…"):
                    out = io.BytesIO()
                    gTTS(text=text, lang="hi" if lang == "Hindi" else "en", slow=slow, timeout=20).write_to_fp(out)
                    st.session_state.voice_audio = out.getvalue()
            except Exception:
                st.error("Could not connect to the voice service. Please try again later.")
        elif go:
            st.warning("Enter some text first.")
        if st.session_state.get("voice_audio"):
            st.audio(st.session_state.voice_audio, format="audio/mp3")
            st.download_button("Download MP3", st.session_state.voice_audio, "chetan-voice.mp3", "audio/mpeg")
    elif mode == "PDF tools":
        st.subheader("PDF converter")
        action = st.radio("Convert", ["Text to PDF", "PDF to text", "Word to PDF", "Excel to PDF"], horizontal=True)
        st.caption("PDF conversion runs locally. OCR for scanned PDFs is not supported.")
        if action in {"Word to PDF", "Excel to PDF"}:
            from office_pdf import office_pdf_ui
            office_pdf_ui(action)
            return
        if action == "Text to PDF":
            st.caption("Text to PDF supports English and Roman Hinglish. Hindi script export is not supported yet.")
            with st.form("text_pdf"):
                text = st.text_area("Text for your PDF", height=220, max_chars=50000)
                go = st.form_submit_button("Create PDF", type="primary")
            if go:
                if text.strip():
                    try: st.session_state.pdf_bytes = make_pdf(text)
                    except Exception: st.error("Could not create the PDF. Check text and font support.")
                else: st.warning("Enter some text first.")
            if st.session_state.get("pdf_bytes"):
                filename = pdf_filename("chetan-document", "text_pdf_filename")
                st.download_button("Download PDF", st.session_state.pdf_bytes, filename, "application/pdf")
        else:
            upload = st.file_uploader("Upload a PDF (maximum 10 MB, 100 pages)", type=["pdf"])
            if st.button("Extract text", disabled=upload is None):
                try:
                    from pypdf import PdfReader
                    if upload.size > 10*1024*1024: raise ValueError()
                    reader = PdfReader(io.BytesIO(upload.getvalue()))
                    if reader.is_encrypted or len(reader.pages)>100: raise ValueError()
                    extracted = "\n\n".join(page.extract_text() or "" for page in reader.pages)
                    st.session_state.pdf_text = extracted[:200000]
                    if not extracted.strip(): st.warning("No text found. This may be a scanned PDF that requires OCR.")
                except Exception: st.error("Could not read the PDF. Use an unlocked file within 10 MB and 100 pages.")
            if st.session_state.get("pdf_text"):
                st.text_area("Extracted text — select to copy", value=st.session_state.pdf_text, height=250)
                st.download_button("Download text", st.session_state.pdf_text, "pdf-text.txt", "text/plain")
