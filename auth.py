"""Local multi-user authentication. No plaintext passwords are stored."""
from contextlib import contextmanager
import hashlib
import hmac
import secrets
import sqlite3
import time
import re
from pathlib import Path
import streamlit as st

DB = Path(__file__).resolve().parent / "private" / "users.sqlite3"


@contextmanager
def connect():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, salt BLOB NOT NULL, digest BLOB NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS attempts (username TEXT PRIMARY KEY, count INTEGER NOT NULL, until REAL NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS access (username TEXT PRIMARY KEY, admin INTEGER NOT NULL DEFAULT 0, enabled INTEGER NOT NULL DEFAULT 1)")
    try:
        with con:
            yield con
    finally:
        con.close()


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)


def signup(username, password):
    username = username.strip().lower()
    if not (re.fullmatch(r"[a-z0-9_]{3,32}", username) or (len(username) <= 254 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", username))):
        raise ValueError("Valid email ya 3-32 letters/numbers wali Login ID use karein.")
    if not 10 <= len(password) <= 128:
        raise ValueError("Password 10 se 128 characters ka rakhein.")
    salt = secrets.token_bytes(16)
    digest = password_hash(password, salt)
    with connect() as con:
        try:
            con.execute("INSERT INTO users VALUES (?, ?, ?)", (username, salt, digest))
        except sqlite3.IntegrityError:
            raise ValueError("Yeh Login ID available nahi hai. Doosri ID chunein.") from None
    return username


def login(username, password):
    username = username.strip().lower()[:254]
    if len(password) > 128:
        return False
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        previous = con.execute("SELECT count, until FROM attempts WHERE username=?", (username,)).fetchone()
        now = time.time()
        if previous and previous[0] >= 5 and previous[1] > now:
            raise ValueError("Bahut attempts hue. 5 minutes baad try karein.")
        row = con.execute("SELECT salt,digest FROM users WHERE username=?", (username,)).fetchone()
        digest = password_hash(password, row[0] if row else bytes(16))
        access = con.execute("SELECT enabled FROM access WHERE username=?", (username,)).fetchone()
        valid = bool(row and hmac.compare_digest(digest, row[1]) and (access is None or access[0]))
        if valid:
            con.execute("DELETE FROM attempts WHERE username=?", (username,))
            return True
        count = previous[0] + 1 if previous and previous[1] > now else 1
        con.execute("INSERT OR REPLACE INTO attempts VALUES (?, ?, ?)", (username, count, now + 300))
        return False


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def require_login(allow_signup=True):
    if st.session_state.get("auth_user"):
        if not account_enabled(st.session_state.auth_user):
            clear_session()
            st.warning("Account disabled hai. Admin se contact karein.")
            st.stop()
        with st.sidebar:
            st.caption("Signed in: " + st.session_state.auth_user)
            if st.button("Log out", key="logout", width="stretch"):
                clear_session()
                st.rerun()
        return
    st.html('<div class="brand">CHETAN AI</div>')
    st.title("Welcome to Chetan AI")
    st.caption("Apna account banaiye ya login karke continue karein." if allow_signup else "Apne admin account se login karein.")
    if allow_signup:
        tab_login, tab_signup = st.tabs(["Login", "Sign up"])
    else:
        tab_login = st.container()
    with tab_login:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Login ID", max_chars=254, key="login_id")
            password = st.text_input("Password", type="password", max_chars=128, key="login_password")
            submit = st.form_submit_button("Login", type="primary", width="stretch")
        if submit:
            try:
                if login(username, password):
                    clear_session()
                    st.session_state.auth_user = username.strip().lower()
                    st.rerun()
                else:
                    st.error("Login ID ya password sahi nahi hai.")
            except ValueError as error:
                st.error(str(error))
    if allow_signup:
        with tab_signup:
            with st.form("signup_form", clear_on_submit=True):
                username = st.text_input("Nayi Login ID", max_chars=254)
                password = st.text_input("Naya password (minimum 10 characters)", type="password", max_chars=128)
                confirm = st.text_input("Password dobara likhein", type="password", max_chars=128)
                submit = st.form_submit_button("Create account", type="primary", width="stretch")
            if submit:
                try:
                    if password != confirm:
                        raise ValueError("Dono passwords match nahi karte.")
                    signup(username, password)
                    st.success("Account ban gaya! Ab Login tab se sign in karein.")
                except ValueError as error:
                    st.error(str(error))
    st.caption("Is installation ke accounts local computer par save hote hain. Password reset abhi available nahi hai.")
    st.stop()


def account_enabled(username):
    with connect() as con:
        row = con.execute("SELECT COALESCE(a.enabled,1) FROM users u LEFT JOIN access a ON u.username=a.username WHERE u.username=?", (username,)).fetchone()
        return bool(row and row[0])


def is_admin(username):
    with connect() as con:
        row = con.execute("SELECT a.admin,a.enabled FROM access a JOIN users u ON u.username=a.username WHERE a.username=?", (username,)).fetchone()
        return bool(row and row[0] and row[1])


def set_enabled(actor, target, enabled):
    if not is_admin(actor):
        raise ValueError("Admin access required.")
    if actor == target:
        raise ValueError("Apna account disable nahi kar sakte.")
    with connect() as con:
        if not con.execute("SELECT 1 FROM users WHERE username=?", (target,)).fetchone():
            raise ValueError("User nahi mila.")
        if con.execute("SELECT 1 FROM access WHERE username=? AND admin=1", (target,)).fetchone():
            raise ValueError("Admin account ko is panel se disable nahi kar sakte.")
        con.execute("INSERT INTO access (username,enabled) VALUES (?,?) ON CONFLICT(username) DO UPDATE SET enabled=excluded.enabled", (target, int(enabled)))


def admin_panel():
    actor = st.session_state.get("auth_user", "")
    if not is_admin(actor):
        st.error("Admin access required.")
        st.stop()
    st.header("Admin Panel")
    with connect() as con:
        rows = con.execute("SELECT u.username,COALESCE(a.admin,0),COALESCE(a.enabled,1) FROM users u LEFT JOIN access a ON u.username=a.username ORDER BY u.username").fetchall()
    st.metric("Total users", len(rows))
    st.dataframe([{"Login ID": u, "Role": "Admin" if a else "User", "Status": "Active" if e else "Disabled"} for u,a,e in rows], hide_index=True)
    choices = [u for u,a,e in rows if not a and u != actor]
    if choices:
        with st.form("manage_user"):
            target = st.selectbox("User select karein", choices)
            action = st.selectbox("Account status", ["Enable", "Disable"])
            submit = st.form_submit_button("Save status", type="primary")
        if submit:
            try:
                set_enabled(actor,target,action=="Enable")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    else:
        st.info("Abhi manage karne ke liye koi normal user nahi hai.")
