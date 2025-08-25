import streamlit as st
from supabase_client import supabase_readonly

def login_box():
    st.subheader("Sign in")
    email = st.text_input("Email")
    pwd   = st.text_input("Password", type="password")
    if st.button("Sign in", use_container_width=True):
        try:
            res = supabase_readonly().auth.sign_in_with_password({"email": email, "password": pwd})
            st.session_state.session = res.session
            st.success("Signed in")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def require_login():
    sess = st.session_state.get("session")
    if not sess or not sess.user:
        login_box(); st.stop()
