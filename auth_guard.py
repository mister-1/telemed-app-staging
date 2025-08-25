# auth_guard.py
# ============================================================
# Single-source auth guard for Streamlit (avoid duplicate keys)
# - Render "Sign out" exactly once (sidebar by default)
# - Provide lightweight session-based login (dev)
# - Ready for plugging real auth (e.g., Supabase) in check_login()
# ============================================================

from __future__ import annotations
import os
import streamlit as st
from typing import Optional, Tuple

# --- Session keys (centralized to avoid typos) ----------------
K_USER_EMAIL = "user_email"
K_USER_ROLE  = "user_role"
K_AUTHED     = "is_authenticated"

# --- Roles ----------------------------------------------------
ADMIN_ROLE = "admin"
USER_ROLE  = "user"


# =============================================================
# Internal helpers
# =============================================================
def _init_session():
    """Initialize essential session keys."""
    if K_AUTHED not in st.session_state:
        st.session_state[K_AUTHED] = False
    if K_USER_EMAIL not in st.session_state:
        st.session_state[K_USER_EMAIL] = None
    if K_USER_ROLE not in st.session_state:
        st.session_state[K_USER_ROLE] = None


def _set_user(email: str, role: str):
    """Set current user into session."""
    st.session_state[K_AUTHED] = True
    st.session_state[K_USER_EMAIL] = email
    st.session_state[K_USER_ROLE] = role


def _clear_user(keep_keys: Tuple[str, ...] = ()):
    """Clear almost all session state (keep some keys if needed)."""
    keep = set(keep_keys)
    for k in list(st.session_state.keys()):
        if k in keep:
            continue
        del st.session_state[k]
    # Re-init minimal keys
    _init_session()


# =============================================================
# Public API
# =============================================================
def render_signout_once(location: str = "sidebar"):
    """
    Render Sign out button exactly once per rerun.
    - location: "sidebar" or "main"
    """
    _init_session()

    flag_key = f"_logout_rendered_{location}"
    if st.session_state.get(flag_key):
        return
    st.session_state[flag_key] = True  # prevent duplicate rendering this run

    area = st.sidebar if location == "sidebar" else st
    with area:
        # Unique key per location so it never collides with other places
        if st.button("Sign out", use_container_width=True, key=f"btn_logout_{location}"):
            # NOTE: Add your token revocation here if you use a real IdP.
            _clear_user(keep_keys=())  # wipe everything for safety
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


def require_login(required_role: Optional[str] = None, signout_location: str = "sidebar"):
    """
    Gatekeeper for every page.
    - Call this ONCE at top-level (e.g., in streamlit_app.main()).
    - It will show a minimal login (dev) if user not logged-in.
    - If logged-in, it will render a single Sign out button (sidebar by default).
    - required_role: None | "admin"
    """
    _init_session()

    # 1) Check existing session first
    if is_authenticated():
        # Optional: enforce role
        if required_role and st.session_state.get(K_USER_ROLE) != required_role:
            st.error("คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
            st.stop()

        # Render a single Sign out button (avoid duplicates)
        render_signout_once(location=signout_location)
        return

    # 2) Not logged in yet -> show login UI (DEV MODE)
    #    Replace this block with your real auth (Supabase, OAuth, etc.)
    st.markdown("### Please sign in")
    with st.form("dev_login_form", clear_on_submit=False):
        email = st.text_input("Email", value=os.getenv("DEV_ADMIN_EMAIL", ""))
        role  = st.selectbox("Role", [ADMIN_ROLE, USER_ROLE], index=0)
        submitted = st.form_submit_button("Sign in")

    if submitted:
        # --- Real-world place to verify email/token against backend ---
        # e.g., verify JWT from st.experimental_user, or Supabase auth user, etc.
        allowed_admins = set(
            (os.getenv("ALLOW_ADMIN_EMAILS", "")).replace(" ", "").split(",")
        ) if os.getenv("ALLOW_ADMIN_EMAILS") else set()

        if role == ADMIN_ROLE and allowed_admins and email not in allowed_admins:
            st.error("อีเมลนี้ไม่ได้รับสิทธิ์ผู้ดูแลระบบ")
            st.stop()

        _set_user(email=email, role=role)
        st.success(f"Welcome, {email}")
        st.rerun()

    # If we reach here, user has not logged in yet
    st.stop()


# =============================================================
# Optional: convenience checks for pages
# =============================================================
def require_admin(signout_location: str = "sidebar"):
    """Shortcut for admin-only pages."""
    require_login(required_role=ADMIN_ROLE, signout_location=signout_location)
