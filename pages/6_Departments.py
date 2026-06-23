"""
Departments — President-only page for managing predefined and
custom task groups (departments / committees).
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.page_init import init_page
init_page("Departments", "🏷️")

import streamlit as st
from app.components.widgets import require_role, section_label
from app.services.admin_service import list_departments, create_department, deactivate_department
from app.services.analytics_service import department_stats

require_role(["President"])
user = st.session_state["user"]

st.title("🏷️ Departments & Task Groups")
st.caption("Predefined departments cover the club's standing committees. Create custom groups for special projects like Data Odyssey 2026 or Project APEX.")

with st.expander("➕ Create New Department / Task Group"):
    with st.form("create_dept_form", clear_on_submit=True):
        name = st.text_input("Group Name *", placeholder="e.g. Data Odyssey 2026 Committee")
        description = st.text_area("Description", placeholder="What is this group responsible for?")
        submitted = st.form_submit_button("Create Group", type="primary")
        if submitted:
            ok, msg, dept_id = create_department(name, description, user["user_id"])
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

st.markdown("<br>", unsafe_allow_html=True)
section_label("All Departments / Task Groups")

depts = list_departments()
stats_by_id = {d["department_id"]: d for d in department_stats()}

for d in depts:
    stat = stats_by_id.get(d["department_id"], {})
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            badge = " 🔧 Custom" if d["is_custom"] else " 📌 Standing"
            st.markdown(f"**{d['department_name']}**{badge}")
            st.caption(d["description"] or "No description.")
        with c2:
            st.write(f"Tasks: **{stat.get('total_tasks', 0)}** · Completed: **{stat.get('completed_tasks', 0)}** · Rate: **{stat.get('completion_rate', 0)}%**")
        with c3:
            if d["is_custom"]:
                if st.button("Archive", key=f"arch_{d['department_id']}"):
                    deactivate_department(d["department_id"], user["user_id"])
                    st.success("Department archived.")
                    st.rerun()
            else:
                st.caption("Standing dept.")
