"""
Shared bootstrap for every Streamlit subpage: sets page config,
ensures sys.path is correct, injects CSS, enforces login, and
renders the sidebar. Import and call init_page() at the top of
every page module.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from app.components.theme import inject_css
from app.components.sidebar import render_sidebar
from app.components.widgets import require_login


def init_page(title: str, icon: str = "🛰️"):
    st.set_page_config(page_title=f"{title} · DatAInspire", page_icon=icon, layout="wide")

    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "dark"
    if "user" not in st.session_state:
        st.session_state["user"] = None

    inject_css()
    require_login()
    render_sidebar()
