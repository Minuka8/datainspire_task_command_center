"""
Analytics — performance tracking for individuals and departments.
President sees club-wide analytics; EXCO members see their own performance.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.page_init import init_page
init_page("Analytics", "📊")

import streamlit as st
import pandas as pd
from app.services import analytics_service as analytics
from app.components.widgets import kpi_card, section_label

user = st.session_state["user"]
is_president = user["role_name"] == "President"

st.title("📊 Performance Analytics")

if is_president:
    overall = analytics.overall_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Tasks", overall["total_tasks"], "#6C5CE7")
    with c2:
        completion_pct = round((overall["completed_tasks"] / overall["total_tasks"]) * 100, 1) if overall["total_tasks"] else 0
        kpi_card("Club-wide Completion", f"{completion_pct}%", "#2A9D8F")
    with c3:
        kpi_card("Overdue", overall["overdue_tasks"], "#E63946")
    with c4:
        avg_days = analytics.avg_completion_time_days()
        kpi_card("Avg. Completion Time", f"{avg_days} days" if avg_days else "—", "#F4A300")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_dept, tab_indiv, tab_priority, tab_snapshot = st.tabs(
        ["🏷️ Department Performance", "👤 Individual Performance", "🎯 Priority Breakdown", "📸 Snapshots"]
    )

    with tab_dept:
        dept_stats = analytics.department_stats()
        if dept_stats:
            df = pd.DataFrame(dept_stats)
            st.dataframe(
                df[["department_name", "total_tasks", "completed_tasks", "overdue_tasks", "completion_rate"]].rename(
                    columns={
                        "department_name": "Department", "total_tasks": "Total",
                        "completed_tasks": "Completed", "overdue_tasks": "Overdue",
                        "completion_rate": "Completion %",
                    }
                ),
                width='stretch', hide_index=True,
            )
            st.bar_chart(df.set_index("department_name")["completion_rate"], color="#6C5CE7", height=300)
        else:
            st.info("No department data available yet.")

    with tab_indiv:
        indiv_stats = analytics.individual_stats()
        if indiv_stats:
            df = pd.DataFrame(indiv_stats)
            st.dataframe(
                df[["full_name", "department_name", "total_assigned", "completed", "overdue", "late_submissions", "completion_rate"]].rename(
                    columns={
                        "full_name": "Name", "department_name": "Department",
                        "total_assigned": "Assigned", "completed": "Completed",
                        "overdue": "Overdue", "late_submissions": "Late Submissions",
                        "completion_rate": "Completion %",
                    }
                ),
                width='stretch', hide_index=True,
            )
            top = df.sort_values("completion_rate", ascending=False).head(10)
            st.bar_chart(top.set_index("full_name")["completion_rate"], color="#2A9D8F", height=300)
        else:
            st.info("No member performance data available yet.")

    with tab_priority:
        breakdown = analytics.tasks_by_priority_breakdown()
        if breakdown:
            df = pd.DataFrame(list(breakdown.items()), columns=["Priority", "Count"])
            st.bar_chart(df.set_index("Priority"), height=280)
        else:
            st.info("No active tasks to break down by priority.")

    with tab_snapshot:
        st.caption(
            "Save a point-in-time performance snapshot. These records form the foundation "
            "for future integration with the **DatAInspire MERITRACK** evaluation system."
        )
        period = st.text_input("Period label", value=pd.Timestamp.today().strftime("%Y-%m"))
        if st.button("📸 Save Performance Snapshot", type="primary"):
            ok, msg = analytics.snapshot_performance_records(period)
            st.success(msg)

else:
    # EXCO member: personal performance only
    my_stats_list = analytics.individual_stats(user_id=user["user_id"])
    my_stats = my_stats_list[0] if my_stats_list else None

    if my_stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_card("Assigned to Me", my_stats["total_assigned"], "#6C5CE7")
        with c2:
            kpi_card("Completed", my_stats["completed"], "#2A9D8F")
        with c3:
            kpi_card("Overdue", my_stats["overdue"], "#E63946")
        with c4:
            kpi_card("Completion Rate", f"{my_stats['completion_rate']}%", "#F4A300")

        st.markdown("<br>", unsafe_allow_html=True)
        avg_days = analytics.avg_completion_time_days(user["user_id"])
        section_label("My Performance Summary")
        st.write(f"**Late submissions:** {my_stats['late_submissions']}")
        st.write(f"**Average completion time:** {avg_days} days" if avg_days else "**Average completion time:** No completed tasks yet.")
    else:
        st.info("No tasks have been assigned to you yet.")
