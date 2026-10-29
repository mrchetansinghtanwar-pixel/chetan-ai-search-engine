"""Editable download names shared by PDF tools."""
import re
import streamlit as st


def pdf_filename(default, key):
    name = st.text_input("PDF file name", value=default, max_chars=120, key=key).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    while name.lower().endswith(".pdf"):
        name = name[:-4].rstrip(" .")
    if not name:
        name = "document"
    if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1,10)], *[f"LPT{i}" for i in range(1,10)]}:
        name = "document_" + name
    return name + ".pdf"
