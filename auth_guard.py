# auth_guard.py
from __future__ import annotations
import os
import re
import streamlit as st
from typing import Iterable, Set

from supabase_client import supabase_readonly, supabase_admin

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ----------------------------
# Session helpers (token store)
# ----------------------------

def _attach_tokens_to_client():
    """
    ใส่ access/refresh token กลับเข้า client ทุกครั้งที่แอป re-run
    (Streamlit re-run บ่อย ถ้าไม่ set ใหม่จะมองว่าไม่ล็อกอิน)
    """
    toks = st.session_state.get("sb_tokens")
    if toks:
        try:
            supabase_readonly().auth.set_session(
                toks["access_token"], toks["refresh_token"]
            )
        except Exception:
            # ถ้าตั้งไม่ได้จะไปเข้าสู่ flow login ปกติ
            pass


def _save_session(session):
    """เก็บโทเคนใน session_state ให้คงอยู่ทุกครั้งที่ re-run"""
    if not session:
        return
    st.session_state["sb_tokens"] = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }
    st.session_state["session"] = session


# ----------------------------
# Roles
# ----------------------------

def _load_roles(user_id: str) -> Set[str]:
    """
    อ่าน role จากตาราง public.user_roles
    เริ่มด้วย readonly; ถ้า RLS กั้นไว้ ค่อย fallback เป็น admin (service key)
    """
    roles: Set[str] = set()
    q = {"user_id": user_id}
    try:
        res = supabase_readonly().table("user_roles").select("role").match(q).execute()
        roles = {r["role"] for r in res.data or []}
    except Exception:
        # บางที่อาจตั้ง RLS เข้ม: ลองด้วย service key เฉพาะจุดนี้
        try:
            res = supabase_admin().table("user_roles").select("role").match(q).execute()
            roles = {r["role"] for r in res.data or []}
        except Exception:
            roles = set()
    return roles


# ----------------------------
# UI pieces
# ----------------------------

def login_box():
    st.subheader("Sign in")

    # ใส่ placeholder กันกรอกผิด
    email = st.text_input("Email", placeholder="you@example.com")
    pwd   = st.text_input("Password", type="password", placeholder="• • • • • • • •")

    col1, col2 = st.columns([1, 1])
    with col1:
        signin = st.button("Sign in", use_container_width=True)
    with col2:
        clear  = st.button("Clear", use_container_width=True)

    if clear:
        st.experimental_rerun()

    if signin:
        # ตรวจรูปแบบอีเมลอย่างง่ายก่อน
        if not EMAIL_RE.match(email):
            st.warning("กรุณากรอกเป็นอีเมล เช่น you@example.com")
            st.stop()

        try:
            # sign-in ด้วย anon key (ฝั่ง server)
            res = supabase_readonly().auth.sign_in_with_password(
                {"email": email, "password": pwd}
            )
            _save_session(res.session)
            # โหลด roles เก็บไว้
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


# ----------------------------
# Public API
# ----------------------------

def require_login(roles: Iterable[str] | None = None):
    """
    เรียกฟังก์ชันนี้ที่บนสุดของทุกหน้า:
      - บังคับล็อกอิน
      - ถ้ากำหนด roles → จะตรวจบทบาทด้วย (เช่น require_login({'admin'}))
    """
    _attach_tokens_to_client()

    sess = st.session_state.get("session")
    if not sess:
        # เผื่อโทเคนเพิ่งถูกตั้งใน _attach_tokens_to_client()
        try:
            sess = supabase_readonly().auth.get_session()
            if sess and sess.user:
                _save_session(sess)
        except Exception:
            sess = None

    if not sess or not getattr(sess, "user", None):
        login_box()
        st.stop()

    # โหลด roles (ถ้ายังไม่โหลด)
    if "roles" not in st.session_state:
        st.session_state["roles"] = _load_roles(sess.user.id)

    # ถ้ากำหนด roles ที่ต้องการไว้ → ตรวจสิทธิ์
    if roles:
        need = set(roles)
        have = set(st.session_state.get("roles", set()))
        if need.isdisjoint(have):
            st.error("คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
            st.stop()

    # แสดงเมนู logout เล็ก ๆ ใน sidebar
    with st.sidebar.expander("Account", expanded=False):
        st.caption(f"Signed in as: **{sess.user.email}**")
        st.caption(f"Roles: `{', '.join(st.session_state.get('roles', [])) or '-'} `")
        if st.button("Sign out", use_container_width=True):
            logout()
