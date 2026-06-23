"""
Sidebar navigation: shows brand header, user info, page links
(role-aware), theme toggle, and logout.
"""

import streamlit as st
from app.components.widgets import brand_header


def render_sidebar():
    user = st.session_state.get("user")

    with st.sidebar:
        brand_header()

        if user:
            initials = "".join([p[0] for p in user["full_name"].split()[:2]]).upper()
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:10px; padding:8px 0 16px 0;">
                    <div style="width:38px;height:38px;border-radius:50%;
                                background:{user.get('avatar_color','#6C5CE7')};
                                display:flex;align-items:center;justify-content:center;
                                color:white;font-weight:700;font-size:13px;">{initials}</div>
                    <div>
                        <div style="font-weight:600; font-size:13.5px;">{user['full_name']}</div>
                        <div style="font-size:11.5px; color:var(--text-muted);">{user['role_name']} · {user.get('department_name') or 'No dept'}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            nav_links = [
                ("pages/1_Dashboard.py", "Dashboard", "🏠"),
                ("pages/2_Tasks.py", "Tasks", "✅"),
                ("pages/3_Calendar.py", "Calendar", "📅"),
                ("pages/4_Analytics.py", "Analytics", "📊"),
            ]
            if user["role_name"] == "President":
                nav_links.append(("pages/5_User_Management.py", "User Management", "👥"))
                nav_links.append(("pages/6_Departments.py", "Departments", "🏷️"))
            nav_links.append(("pages/7_My_Profile.py", "My Profile", "⚙️"))

            for page_path, label, icon in nav_links:
                try:
                    st.page_link(page_path, label=label, icon=icon)
                except Exception:
                    # Falls back gracefully if the page registry isn't
                    # available in this execution context (e.g. a page
                    # was loaded standalone rather than via Home.py).
                    st.caption(f"{icon} {label}")

            st.markdown("<br>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                mode = st.session_state.get("theme_mode", "dark")
                label = "☀️ Light" if mode == "dark" else "🌙 Dark"
                if st.button(label, width='stretch', key="theme_toggle_btn"):
                    st.session_state["theme_mode"] = "light" if mode == "dark" else "dark"
                    st.rerun()
            with col2:
                if st.button("🚪 Logout", width='stretch', key="logout_btn"):
                    st.session_state["user"] = None
                    st.rerun()
