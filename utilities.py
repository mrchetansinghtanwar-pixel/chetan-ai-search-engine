"""Small local utilities; only voice text is sent to Google's TTS service."""
import ast
import operator
import io
import html
import streamlit as st


def calculate(expression):
    if len(expression) > 200:
        raise ValueError("Expression bahut lamba hai.")
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
                raise ValueError("Power maximum 100 rakhein.")
            value = ops[type(node.op)](a, b)
        else:
            raise ValueError("Sirf numbers, brackets aur + - * / % ** allowed hain.")
        if isinstance(value, complex) or abs(value) > 1e100:
            raise ValueError("Result bahut bada ya unsupported hai.")
        return value
    return visit(tree.body)


def make_pdf(text):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    if any(ord(c)>255 for c in text):
        raise ValueError("Is PDF version mein English/Hinglish Latin text use karein.")
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
                st.error("Calculation valid nahi hai. Numbers aur operators check karein; zero se divide na karein.")
        st.caption("+ add · - subtract · * multiply · / divide · % remainder · ** power")
    elif mode == "Text pad":
        st.subheader("Text copy / paste")
        text = st.text_area("Yahan text paste ya type karein", height=250, key="text_pad", max_chars=50000)
        st.caption(f"{len(text.split())} words · {len(text)} characters")
        if text:
            st.caption("Neeche code box ke copy icon se poora text copy karein.")
            st.code(text, language=None)
            st.download_button("TXT download", text, "chetan-text.txt", "text/plain")
    elif mode == "Voice":
        st.subheader("Text se voice")
        st.caption("Audio banane par yeh text Google ki speech service ko bheja jayega. Internet chahiye; service limits ho sakti hain.")
        with st.form("voice"):
            text = st.text_area("Bolne ke liye text", height=150, max_chars=2000)
            lang = st.selectbox("Voice language", ["Hindi", "English"])
            slow = st.checkbox("Dheere bolein")
            go = st.form_submit_button("Audio banao", type="primary")
        if go and text.strip():
            try:
                from gtts import gTTS
                with st.spinner("Audio ban raha hai…"):
                    out = io.BytesIO()
                    gTTS(text=text, lang="hi" if lang == "Hindi" else "en", slow=slow, timeout=20).write_to_fp(out)
                    st.session_state.voice_audio = out.getvalue()
            except Exception:
                st.error("Voice service se connection nahi hua. Baad mein retry karein.")
        elif go:
            st.warning("Pehle text likhiye.")
        if st.session_state.get("voice_audio"):
            st.audio(st.session_state.voice_audio, format="audio/mp3")
            st.download_button("MP3 download", st.session_state.voice_audio, "chetan-voice.mp3", "audio/mpeg")
    elif mode == "PDF tools":
        st.subheader("PDF converter")
        action = st.radio("Convert", ["Text to PDF", "PDF to text"], horizontal=True)
        st.caption("PDF conversion local hai. Scanned PDF ke liye OCR is version mein nahi hai.")
        if action == "Text to PDF":
            st.caption("Text to PDF: English / Roman Hinglish supported. Hindi script export abhi supported nahi hai.")
            with st.form("text_pdf"):
                text = st.text_area("PDF ka text", height=220, max_chars=50000)
                go = st.form_submit_button("PDF banao", type="primary")
            if go:
                if text.strip():
                    try: st.session_state.pdf_bytes = make_pdf(text)
                    except Exception: st.error("PDF create nahi hui. Text ya font support check karein.")
                else: st.warning("Pehle text likhiye.")
            if st.session_state.get("pdf_bytes"):
                st.download_button("PDF download", st.session_state.pdf_bytes, "chetan-document.pdf", "application/pdf")
        else:
            upload = st.file_uploader("PDF upload karein (max 10 MB, 100 pages)", type=["pdf"])
            if st.button("Text nikalo", disabled=upload is None):
                try:
                    from pypdf import PdfReader
                    if upload.size > 10*1024*1024: raise ValueError()
                    reader = PdfReader(io.BytesIO(upload.getvalue()))
                    if reader.is_encrypted or len(reader.pages)>100: raise ValueError()
                    extracted = "\n\n".join(page.extract_text() or "" for page in reader.pages)
                    st.session_state.pdf_text = extracted[:200000]
                    if not extracted.strip(): st.warning("Text nahi mila. Yeh scanned PDF ho sakti hai; OCR chahiye.")
                except Exception: st.error("PDF read nahi hui. Unlocked PDF, 10 MB aur 100-page limit check karein.")
            if st.session_state.get("pdf_text"):
                st.text_area("Extracted text — select karke copy karein", value=st.session_state.pdf_text, height=250)
                st.download_button("Text download", st.session_state.pdf_text, "pdf-text.txt", "text/plain")
