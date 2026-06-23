"""
DatAInspire Task Command Center — Main Entry Point

Handles:
  - First-run database initialization
  - First-run "Create President Account" wizard
  - Login screen
  - Redirect to Dashboard once authenticated
"""

import sys
from pathlib import Path

# Ensure the project root is importable regardless of how Streamlit was launched
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from app.database.db import init_database, is_initialized
from app.database.seed import run_seed
from app.services.auth_service import authenticate, create_user
from app.services.admin_service import count_presidents
from app.components.theme import inject_css

st.set_page_config(
    page_title="DatAInspire Task Command Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"
if "user" not in st.session_state:
    st.session_state["user"] = None

inject_css()

# ---------------------------------------------------------------
# First-run bootstrap: create schema + seed roles/departments
# ---------------------------------------------------------------
if not is_initialized():
    init_database()
    run_seed()

needs_first_president = count_presidents() == 0


def render_brand_block():
    st.html(
        """
        <div style="text-align:center; margin-bottom: 8px;">
            <div class="dc-login-mark" style="margin:0 auto 14px auto;">DI</div>
            <h2 style="margin-bottom:2px;">DatAInspire</h2>
            <div style="color:var(--text-muted); font-size:13px; letter-spacing:0.04em; text-transform:uppercase;">
                Task Command Center · AI &amp; Data Science Club
            </div>
        </div>
        """
    )


# ---------------------------------------------------------------
# Already logged in -> bounce to dashboard
# ---------------------------------------------------------------
if st.session_state["user"] is not None:
    st.switch_page("pages/1_Dashboard.py")

st.html('<div class="dc-login-wrap">')
render_brand_block()

if needs_first_president:
    st.info(
        "👋 **Welcome!** No administrator account exists yet. "
        "Create the first **President** account to get started."
    )
    with st.form("first_president_form"):
        full_name = st.text_input("Full Name")
        username = st.text_input("Username")
        email = st.text_input("Email (optional)")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create President Account", use_container_width=True, type="primary")

        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                success, msg, user_id = create_user(
                    full_name=full_name,
                    username=username,
                    email=email,
                    password=password,
                    role_name="President",
                    department_id=None,
                )
                if success:
                    st.success(f"{msg} You can now log in below.")
                    st.balloons()
                    needs_first_president = False
                    st.rerun()
                else:
                    st.error(msg)
else:
    tabs = st.tabs(["Log In"])
    with tabs[0]:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    result = authenticate(username, password)
                    if result:
                        st.session_state["user"] = result
                        st.success(f"Welcome back, {result['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password, or your account is inactive.")

    st.html(
        """
        <div style="text-align:center; margin-top:14px; font-size:12px; color:var(--text-muted);">
            Forgot your password? Contact your President / club administrator.
        </div>
        """
    )

st.html("</div>")