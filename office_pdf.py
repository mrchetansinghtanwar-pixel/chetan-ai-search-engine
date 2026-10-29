"""Local Word and Excel PDF export using LibreOffice."""
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
import hashlib
import streamlit as st
from download_names import pdf_filename


def office_binary():
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for folder in (os.environ.get("ProgramFiles", "C:/Program Files"), os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")):
        candidate = Path(folder) / "LibreOffice/program/soffice.com"
        if candidate.is_file():
            return str(candidate)
    return None


def convert_office(data, extension):
    if extension not in {".docx", ".xlsx"}:
        raise ValueError("Use a DOCX or XLSX file. Save older DOC/XLS files in the newer format first.")
    if not data or len(data) > 20 * 1024 * 1024:
        raise ValueError("Upload a file up to 20 MB.")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 10000 or sum(e.file_size for e in entries) > 100 * 1024 * 1024:
                raise ValueError("The document is too large when unpacked.")
            required = "word/document.xml" if extension == ".docx" else "xl/workbook.xml"
            if required not in archive.namelist() or any("vbaproject" in e.filename.lower() for e in entries):
                raise ValueError("Use a valid, macro-free Word or Excel file.")
    except zipfile.BadZipFile:
        raise ValueError("The document is damaged, password-protected or not a valid Office file.") from None
    binary = office_binary()
    if not binary:
        raise ValueError("LibreOffice is required on the computer running this app.")
    with tempfile.TemporaryDirectory(prefix="chetan-office-") as folder:
        root = Path(folder)
        source = root / ("document" + extension)
        source.write_bytes(data)
        profile = root / "profile"
        user = profile / "user"
        user.mkdir(parents=True)
        (user / "registrymodifications.xcu").write_text(
            '<oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item></oor:items>', encoding="utf-8")
        try:
            result = subprocess.run([
                binary, "-env:UserInstallation=" + profile.as_uri(), "--headless", "--nologo", "--nodefault", "--norestore",
                "--convert-to", "pdf:writer_pdf_Export" if extension == ".docx" else "pdf:calc_pdf_Export",
                "--outdir", str(root), str(source)
            ], capture_output=True, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except subprocess.TimeoutExpired:
            raise ValueError("Conversion timed out. Try a smaller document.") from None
        except OSError:
            raise ValueError("Could not start LibreOffice. Check the installation.") from None
        output = root / "document.pdf"
        if result.returncode or not output.is_file():
            raise ValueError("Could not convert this file. Check that it opens correctly and is not password-protected.")
        pdf = output.read_bytes()
        if not pdf.startswith(b"%PDF-"):
            raise ValueError("The converter did not return a valid PDF.")
        return pdf


def office_pdf_ui(action):
    extension = ".docx" if action == "Word to PDF" else ".xlsx"
    st.caption("Files are converted locally with LibreOffice. Maximum 20 MB. Fonts and complex layouts may vary; check the PDF before sharing.")
    if extension == ".xlsx":
        st.info("Excel export follows the workbook print areas and page settings. Set the print area and fit-to-page in Excel for wide sheets.")
    upload = st.file_uploader("Upload a Word document" if extension == ".docx" else "Upload an Excel workbook", type=[extension[1:]], key="office_upload_" + extension)
    ready = bool(office_binary())
    if not ready:
        st.warning("LibreOffice is not installed on the app server. Install it to enable conversion.")
    data = upload.getvalue() if upload else b""
    fingerprint = hashlib.sha256(data).hexdigest() + extension
    if st.button("Convert to PDF", disabled=not ready or upload is None, key="office_convert_" + extension, type="primary"):
        st.session_state.pop("office_pdf_result", None)
        try:
            with st.spinner("Converting your file to PDF…"):
                pdf = convert_office(data, extension)
            st.session_state.office_pdf_result = (fingerprint, pdf)
        except ValueError as error:
            st.error(str(error))
        except Exception:
            st.error("Conversion failed. Please try a smaller, unlocked file.")
    result = st.session_state.get("office_pdf_result")
    if upload and result and result[0] == fingerprint:
        st.success("Your PDF is ready.")
        filename = pdf_filename(Path(upload.name).stem, "office_name_" + fingerprint)
        st.download_button("Download PDF", result[1], file_name=filename, mime="application/pdf")
