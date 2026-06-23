"""
My Profile — change password, view personal account info.
Available to both Presidents and EXCO members.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.page_init import init_page
init_page("My Profile", "⚙️")

import streamlit as st
from app.services.auth_service import change_password, get_user_by_id

user = st.session_state["user"]

st.title("⚙️ My Profile")

fresh = get_user_by_id(user["user_id"])

col1, col2 = st.columns([1, 2])
with col1:
    initials = "".join([p[0] for p in user["full_name"].split()[:2]]).upper()
    st.markdown(
        f"""
        <div style="width:90px;height:90px;border-radius:50%;
                    background:{user.get('avatar_color','#6C5CE7')};
                    display:flex;align-items:center;justify-content:center;
                    color:white;font-weight:700;font-size:32px; margin-bottom:14px;">{initials}</div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(f"### {fresh['full_name']}")
    st.write(f"**Username:** `{fresh['username']}`")
    st.write(f"**Role:** {fresh['role_name']}")
    st.write(f"**Department:** {fresh['department_name'] or '—'}")
    st.write(f"**Email:** {fresh['email'] or '—'}")
    st.write(f"**Member since:** {fresh['created_at'][:10]}")
    if fresh["last_login"]:
        st.write(f"**Last login:** {fresh['last_login']}")

st.divider()
st.subheader("🔒 Change Password")

with st.form("change_password_form", clear_on_submit=True):
    new_pw = st.text_input("New Password", type="password", help="At least 8 characters with a letter and a number.")
    confirm_pw = st.text_input("Confirm New Password", type="password")
    submitted = st.form_submit_button("Update Password", type="primary")

    if submitted:
        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
        else:
            ok, msg = change_password(user["user_id"], new_pw)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
