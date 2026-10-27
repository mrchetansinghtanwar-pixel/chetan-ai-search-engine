"""Chetan AI page navigation."""
import streamlit as st

page = st.navigation([
    st.Page("user_page.py", title="Users", default=True),
])
page.run()
