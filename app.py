"""Chetan AI page navigation."""
import streamlit as st

page = st.navigation([
    st.Page("user_page.py", title="Users", default=True),
    st.Page("pages/admin.py", title="Admin", url_path="admin"),
])
page.run()
