"""Separate, access-controlled administration page."""
import streamlit as st
from auth import require_login, is_admin, admin_panel

st.set_page_config(page_title="Chetan AI | Admin", page_icon=":material/admin_panel_settings:", layout="wide")
st.page_link("user_page.py", label="Chetan AI par wapas", icon=":material/arrow_back:")
st.caption("CHETAN AI / ADMINISTRATION")
require_login(allow_signup=False)
if not is_admin(st.session_state.auth_user):
    st.error("Yeh page sirf admin account ke liye hai.")
    st.stop()
admin_panel()
