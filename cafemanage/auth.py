import streamlit as st
import sqlite3
from database import get_connection

def login(username, password):
    conn = get_connection()
    cur = conn.cursor()
    # WARNING: For prototyping only; never store passwords as plain text in real apps.
    cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cur.fetchone()
    conn.close()
    return user

def is_logged_in():
    return 'user' in st.session_state and st.session_state['user']

def logout():
    if 'user' in st.session_state:
        del st.session_state['user']

def require_login():
    if not is_logged_in():
        st.info("Please login to access this page.")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.session_state['user'] = dict(user)
                st.success(f"Welcome, {user['username']}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")
        st.stop()

