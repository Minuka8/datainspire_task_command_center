"""
Dashboard — the executive command center.
Shows overall stats, department performance, individual stats,
and a recent activity feed.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.page_init import init_page
init_page("Dashboard", "🏠")

import streamlit as st
import pandas as pd
from app.services import analytics_service as analytics
from app.services.task_service import list_tasks, is_overdue
from app.components.widgets import kpi_card, section_label, render_task_list

user = st.session_state["user"]
is_president = user["role_name"] == "President"

st.title("🛰️ Command Center")
st.caption(f"Welcome back, **{user['full_name']}** — here's what's happening across the club today.")

# -----------------------------------------------------------------
# OVERALL KPIs
# -----------------------------------------------------------------
stats = analytics.overall_stats()

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Active Tasks", stats["active_tasks"], color="#6C5CE7")
with c2:
    kpi_card("Completed", stats["completed_tasks"], color="#2A9D8F")
with c3:
    kpi_card("Overdue", stats["overdue_tasks"], color="#E63946")
with c4:
    kpi_card("Awaiting Approval", stats["pending_review"], color="#F4A300")

st.markdown("<br>", unsafe_allow_html=True)

left, right = st.columns([1.4, 1])

# -----------------------------------------------------------------
# LEFT: Department performance + status breakdown
# -----------------------------------------------------------------
with left:
    section_label("Department Performance")
    dept_stats = analytics.department_stats()
    if dept_stats:
        df = pd.DataFrame(dept_stats)
        df_display = df[["department_name", "total_tasks", "completed_tasks", "overdue_tasks", "completion_rate"]]
        df_display.columns = ["Department", "Total", "Completed", "Overdue", "Completion %"]
        st.dataframe(df_display, width='stretch', hide_index=True)

        st.bar_chart(df.set_index("department_name")["completion_rate"], height=240, color="#6C5CE7")
    else:
        st.info("No department data yet.")

    section_label("Task Status Breakdown")
    status_breakdown = analytics.tasks_by_status_breakdown()
    if status_breakdown:
        sdf = pd.DataFrame(list(status_breakdown.items()), columns=["Status", "Count"])
        st.bar_chart(sdf.set_index("Status"), height=220, color="#8E7CFF")
    else:
        st.info("No tasks recorded yet.")

# -----------------------------------------------------------------
# RIGHT: My tasks / urgent tasks + recent activity
# -----------------------------------------------------------------
with right:
    if is_president:
        section_label("⚠️ Needs Your Attention")
        pending = list_tasks(status="Submitted for Review")
        render_task_list(pending, "Nothing awaiting your review right now.")
    else:
        section_label("📋 My Tasks")
        my_tasks = list_tasks(assigned_to=user["user_id"])
        urgent = [t for t in my_tasks if t["status"] != "Approved"]
        urgent_sorted = sorted(urgent, key=lambda t: (not is_overdue(t), t["deadline"]))
        render_task_list(urgent_sorted[:5], "You have no active tasks. 🎉")

    section_label("🕓 Recent Activity")
    activity = analytics.recent_activity(limit=10)
    if activity:
        for a in activity:
            name = a.get("full_name") or "System"
            st.markdown(
                f"""
                <div style="padding:8px 0; border-bottom:1px solid var(--border); font-size:13px;">
                    <span style="font-weight:600;">{name}</span>
                    <span style="color:var(--text-muted);"> · {a['action'].replace('_',' ').title()}</span>
                    <div style="color:var(--text-muted); font-size:11.5px;">{a['details'] or ''} &nbsp;·&nbsp; {a['created_at']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No activity recorded yet.")

# -----------------------------------------------------------------
# Quick add task (President only) — fast path from the dashboard
# -----------------------------------------------------------------
if is_president:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ Quick Create Task"):
        st.caption("For full task creation options, visit the **Tasks** page.")
        if st.button("Go to Tasks page to create a task →"):
            st.switch_page("pages/2_Tasks.py")
