# auth_guard.py
# ============================================================
# Streamlit auth guard (single-source login + single signout button)
# - ใช้ session เก็บสถานะผู้ใช้
# - ปุ่ม Sign out เรนเดอร์ครั้งเดียวต่อรอบรัน (กัน key ซ้ำ)
# - รองรับ DEV login form ในตัว (ปรับต่อกับ IdP จริงภายหลังได้)
# - ใช้ร่วมกับ streamlit_app.py ที่เรียก:
#     require_login(); user_email, role = current_user()
# ============================================================

from __future__ import annotations

import os
from typing import Optional, Tuple

import streamlit as st

# ---------------- Session keys ----------------
K_AUTHED = "is_authenticated"
K_USER_EMAIL = "user_email"
K_USER_ROLE = "user_role"

# ---------------- Roles ----------------
ADMIN_ROLE = "admin"
USER_ROLE = "user"


# ---------------- Utilities ----------------
def _init_session() -> None:
    """Ensure required session keys exist."""
    if K_AUTHED not in st.session_state:
        st.session_state[K_AUTHED] = False
    if K_USER_EMAIL not in st.session_state:
        st.session_state[K_USER_EMAIL] = None
    if K_USER_ROLE not in st.session_state:
        st.session_state[K_USER_ROLE] = None


def _set_user(email: str, role: str) -> None:
    """Set current user into session."""
    _init_session()
    st.session_state[K_AUTHED] = True
    st.session_state[K_USER_EMAIL] = email
    st.session_state[K_USER_ROLE] = role


def _clear_user(keep_keys: Tuple[str, ...] = ()) -> None:
    """Clear session state except some keep keys."""
    keep = set(keep_keys)
    for k in list(st.session_state.keys()):
        if k in keep:
            continue
        del st.session_state[k]
    _init_session()


def _get_allowed_admins() -> set[str]:
    """
    List allowed admin emails from secrets/env.
    - ALLOW_ADMIN_EMAILS: comma-separated emails
    - If not set -> no restriction (DEV mode)
    """
    allow_raw = None
    try:
        allow_raw = st.secrets.get("ALLOW_ADMIN_EMAILS", None)
    except Exception:
        pass
    if allow_raw is None:
        allow_raw = os.getenv("ALLOW_ADMIN_EMAILS")

    if not allow_raw:
        return set()

    return {e.strip() for e in str(allow_raw).split(",") if e.strip()}


# ---------------- Public API ----------------
def render_signout_once(location: str = "sidebar") -> None:
    """
    Render Sign out button exactly once per rerun.
    - location: "sidebar" or "main"
    """
    _init_session()

    flag_key = f"_logout_rendered_{location}"
    if st.session_state.get(flag_key):
        return
    st.session_state[flag_key] = True

    area = st.sidebar if location == "sidebar" else st
    with area:
        # ใช้ key เฉพาะที่ผูกกับ location เพื่อกันชนซ้ำ
        if st.button("Sign out", key=f"btn_logout_{location}", use_container_width=True):
            # TODO: ถ้ามี token/JWT ให้ revoke ที่นี่
            _clear_user()
            st.success("Signed out")
            st.rerun()


def is_authenticated() -> bool:
    _init_session()
    return bool(st.session_state.get(K_AUTHED))


def current_user() -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (email, role)
    """
    _init_session()
    return st.session_state.get(K_USER_EMAIL), st.session_state.get(K_USER_ROLE)


def _dev_login_ui() -> None:
    """
    Minimal DEV login form. Replace with real auth (Supabase/OAuth) เมื่อพร้อม.
    - เคารพ ALLOW_ADMIN_EMAILS ถ้ากำหนด
    - DEV_ADMIN_EMAIL ช่วยเติมค่าเริ่มต้นในช่อง Email
    """
    st.markdown("### Please sign in")
    default_email = None
    try:
        default_email = st.secrets.get("DEV_ADMIN_EMAIL", None)
    except Exception:
        pass
    if default_email is None:
        default_email = os.getenv("DEV_ADMIN_EMAIL", "")

    with st.form("dev_login_form", clear_on_submit=False):
        email = st.text_input("Email", value=default_email)
        role = st.selectbox("Role", [ADMIN_ROLE, USER_ROLE], index=0)
        submitted = st.form_submit_button("Sign in")

    if submitted:
        allowed_admins = _get_allowed_admins()
        if role == ADMIN_ROLE and allowed_admins and email not in allowed_admins:
            st.error("อีเมลนี้ไม่ได้รับสิทธิ์ผู้ดูแลระบบ")
            st.stop()

        _set_user(email=email, role=role)
        st.success(f"Welcome, {email}")
        st.rerun()

    # ยังไม่ล็อกอิน -> หยุดการเรนเดอร์ส่วนที่เหลือ
    st.stop()


def require_login(required_role: Optional[str] = None, signout_location: str = "sidebar") -> None:
    """
    Gatekeeper สำหรับทุกหน้า
    - เรียกครั้งเดียวที่ต้นหน้า (เช่นใน main())
    - ถ้ายังไม่ล็อกอิน จะโชว์ DEV login form
    - ถ้าล็อกอินแล้ว จะเรนเดอร์ปุ่ม Sign out 'ครั้งเดียว' ตามตำแหน่งที่กำหนด
    - required_role: None หรือ "admin"
    """
    _init_session()

    if not is_authenticated():
        _dev_login_ui()  # จะ st.stop() ภายในถ้ายังไม่สัมฤทธิ์ผล

    # ผ่านแล้ว: ตรวจสิทธิ์เพิ่มเติมถ้ากำหนด
    role = st.session_state.get(K_USER_ROLE)
    if required_role and role != required_role:
        st.error("คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        st.stop()

    # แสดงปุ่ม Sign out เพียงที่เดียว
    render_signout_once(location=signout_location)


def require_admin(signout_location: str = "sidebar") -> None:
    """Shortcut สำหรับหน้า admin เท่านั้น"""
    require_login(required_role=ADMIN_ROLE, signout_location=signout_location)
