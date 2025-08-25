# auth_guard.py  (v2) — single-source Sign-in (main only)
from __future__ import annotations
import re
import streamlit as st
from typing import Iterable, Set, Tuple, Optional
from supabase_client import supabase_readonly, supabase_admin

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ----------------------------
# Internal: session helpers
# ----------------------------
def _attach_tokens_to_client():
    toks = st.session_state.get("sb_tokens")
    if toks:
        try:
            supabase_readonly().auth.set_session(
                toks["access_token"], toks["refresh_token"]
            )
        except Exception:
            pass

def _save_session(session):
    if not session:
        return
    st.session_state["sb_tokens"] = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }
    st.session_state["session"] = session

def _load_roles(user_id: str) -> Set[str]:
    roles: Set[str] = set()
    q = {"user_id": user_id}
    try:
        res = supabase_readonly().table("user_roles").select("role").match(q).execute()
        roles = {r["role"] for r in res.data or []}
    except Exception:
        try:
            res = supabase_admin().table("user_roles").select("role").match(q).execute()
            roles = {r["role"] for r in res.data or []}
        except Exception:
            roles = set()
    return roles

# ----------------------------
# Public UI
# ----------------------------
def _login_box(title: str = "Sign in") -> None:
    st.subheader(title)
    email = st.text_input("Email", placeholder="you@example.com", key="lg_email")
    pwd   = st.text_input("Password", type="password", placeholder="• • • • • • • •", key="lg_pwd")
    if st.button("Sign in", use_container_width=True, key="lg_submit"):
        if not EMAIL_RE.match(email):
            st.warning("กรุณากรอกเป็นอีเมล เช่น you@example.com")
            st.stop()
        try:
            res = supabase_readonly().auth.sign_in_with_password(
                {"email": email, "password": pwd}
            )
            _save_session(res.session)
            st.session_state["roles"] = _load_roles(res.user.id)
            st.success("Signed in")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def logout():
    try:
        supabase_readonly().auth.sign_out()
    except Exception:
        pass
    for k in ("sb_tokens", "session", "roles"):
        st.session_state.pop(k, None)
    st.success("Signed out")
    st.rerun()

def require_login(roles: Iterable[str] | None = None,
                  title: str = "Sign in") -> Tuple[object, Set[str]]:
    """
    เรียกบนสุดของทุกหน้า:
      user, roles = require_login()            # ต้องล็อกอิน
      user, roles = require_login({'admin'})   # ต้องเป็นแอดมิน
    - แสดงฟอร์มล็อกอินใน main เท่านั้น
    - Sidebar จะมีเฉพาะข้อมูลผู้ใช้ + Sign out หลังล็อกอินแล้ว
    """
    _attach_tokens_to_client()

    # 1) มี session แล้วหรือยัง
    sess = st.session_state.get("session")
    if not sess or not getattr(sess, "user", None):
        try:
            sess = supabase_readonly().auth.get_session()
            if sess and sess.user:
                _save_session(sess)
        except Exception:
            sess = None

    # 2) ถ้ายังไม่ล็อกอิน → โชว์ฟอร์มที่ "main" เท่านั้น แล้ว stop
    if not sess or not getattr(sess, "user", None):
        _login_box(title)
        st.stop()

    # 3) เติม roles ไว้ใน state (ครั้งแรก)
    if "roles" not in st.session_state:
        st.session_state["roles"] = _load_roles(sess.user.id)

    have = set(st.session_state.get("roles", set()))
    if roles:
        need = set(roles)
        if need.isdisjoint(have):
            st.error("คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
            st.stop()

    # 4) Sidebar: แสดงข้อมูล (ไม่มีฟอร์มล็อกอิน)
    with st.sidebar.expander("Account", expanded=False):
        st.caption(f"Signed in as: **{sess.user.email}**")
        st.caption(f"Roles: `{', '.join(have) or '-'}`")
        if st.button("Sign out", use_container_width=True, key="btn_logout"):
            logout()

    return sess.user, have
