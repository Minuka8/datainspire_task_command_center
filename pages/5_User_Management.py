"""
User Management — President-only page for creating and managing
club member accounts, roles, and departments.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.page_init import init_page
init_page("User Management", "👥")

import streamlit as st
from app.components.widgets import require_role, section_label
from app.services.auth_service import create_user, ROLE_PRESIDENT, ROLE_EXCO
from app.services.admin_service import (
    list_users, list_departments, update_user, deactivate_user,
    reactivate_user, count_presidents,
)

require_role(["President"])
user = st.session_state["user"]

st.title("👥 User Management")

tab_list, tab_create = st.tabs(["📇 Club Members", "➕ Add Member"])

# =====================================================================
# CREATE NEW USER
# =====================================================================
with tab_create:
    depts = list_departments()
    dept_options = {"— No department —": None}
    dept_options.update({d["department_name"]: d["department_id"] for d in depts})

    with st.form("create_member_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *")
            username = st.text_input("Username *")
            email = st.text_input("Email")
        with col2:
            role = st.selectbox("Role *", [ROLE_EXCO, ROLE_PRESIDENT])
            dept_name = st.selectbox("Department", list(dept_options.keys()))
            password = st.text_input("Temporary Password *", type="password", help="At least 8 characters with a letter and a number.")

        submitted = st.form_submit_button("Create Account", type="primary", width='stretch')

        if submitted:
            success, msg, new_id = create_user(
                full_name=full_name,
                username=username,
                email=email,
                password=password,
                role_name=role,
                department_id=dept_options[dept_name],
                created_by_user_id=user["user_id"],
            )
            if success:
                st.success(f"{msg} Share the username and temporary password with {full_name} securely.")
            else:
                st.error(msg)

# =====================================================================
# LIST / MANAGE USERS
# =====================================================================
with tab_list:
    show_inactive = st.checkbox("Show deactivated members")
    members = list_users(active_only=not show_inactive)

    depts = list_departments()
    dept_options = {"— No department —": None}
    dept_options.update({d["department_name"]: d["department_id"] for d in depts})

    section_label(f"{len(members)} Member(s)")

    for m in members:
        status_text = "🟢 Active" if m["is_active"] else "🔴 Deactivated"
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{m['full_name']}** (`{m['username']}`) — {m['role_name']}")
                st.caption(f"{m['department_name'] or 'No department'} · {status_text} · Joined {m['created_at'][:10]}")
                if m["last_login"]:
                    st.caption(f"Last login: {m['last_login']}")
            with c2:
                with st.popover("Manage", width='stretch'):
                    new_dept = st.selectbox(
                        "Department", list(dept_options.keys()),
                        index=list(dept_options.keys()).index(m["department_name"]) if m["department_name"] in dept_options else 0,
                        key=f"dept_{m['user_id']}",
                    )
                    if st.button("Update Department", key=f"upd_dept_{m['user_id']}"):
                        update_user(m["user_id"], user["user_id"], department_id=dept_options[new_dept])
                        st.success("Department updated.")
                        st.rerun()

                    st.divider()
                    if m["is_active"]:
                        is_last_president = (m["role_name"] == "President" and count_presidents() <= 1)
                        if is_last_president:
                            st.caption("⚠️ Cannot deactivate the last remaining President.")
                        else:
                            if st.button("🚫 Deactivate", key=f"deact_{m['user_id']}"):
                                deactivate_user(m["user_id"], user["user_id"])
                                st.success("Member deactivated.")
                                st.rerun()
                    else:
                        if st.button("✅ Reactivate", key=f"react_{m['user_id']}"):
                            reactivate_user(m["user_id"], user["user_id"])
                            st.success("Member reactivated.")
                            st.rerun()
