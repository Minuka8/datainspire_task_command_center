"""
Reusable UI components for DatAInspire Task Command Center.
"""

import streamlit as st
from datetime import date, datetime
from app.components.theme import priority_badge_html, status_badge_html
from app.services.task_service import is_overdue


def kpi_card(label: str, value, color: str = "#6C5CE7", delta: str = ""):
    delta_html = f'<div class="dc-kpi-delta">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="dc-kpi" style="--kpi-color:{color}">
            <div class="dc-kpi-label">{label}</div>
            <div class="dc-kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str):
    st.markdown(f'<div class="dc-section-label">{text}</div>', unsafe_allow_html=True)


def brand_header():
    st.markdown(
        """
        <div class="dc-brand">
            <div class="dc-brand-mark">DI</div>
            <div>
                <div class="dc-brand-text">DatAInspire</div>
                <div class="dc-brand-sub">Task Command Center</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def task_card_summary(task: dict) -> str:
    """Returns HTML for a compact task card (used in lists)."""
    rail_colors = {"High": "var(--red)", "Medium": "var(--amber)", "Low": "var(--green)"}
    rail = rail_colors.get(task["priority"], "var(--accent)")
    overdue_flag = ""
    if is_overdue(task):
        overdue_flag = '<span class="dc-badge" style="--badge-color:var(--red)">⚠ Overdue</span>'

    assignee = task.get("assigned_to_name") or "Unassigned"
    dept = task.get("department_name") or "—"

    return f"""
    <div class="dc-task-card" style="--rail-color:{rail}">
        <div class="dc-task-code">{task['task_code']} · {dept}</div>
        <div class="dc-task-title">{task['title']}</div>
        <div class="dc-meta-row">
            {priority_badge_html(task['priority'])}
            {status_badge_html(task['status'])}
            {overdue_flag}
        </div>
        <div style="margin-top:8px; font-size:12.5px; color:var(--text-muted);">
            👤 {assignee} &nbsp;·&nbsp; 📅 Due {task['deadline']}
        </div>
    </div>
    """


def render_task_list(tasks: list, empty_message: str = "No tasks found."):
    if not tasks:
        st.info(empty_message)
        return
    for task in tasks:
        st.markdown(task_card_summary(task), unsafe_allow_html=True)


def days_until(deadline_str: str) -> int:
    try:
        d = datetime.fromisoformat(deadline_str).date()
    except ValueError:
        d = date.fromisoformat(deadline_str[:10])
    return (d - date.today()).days


def require_role(allowed_roles: list[str]):
    """Stop page execution if the current user's role isn't allowed."""
    user = st.session_state.get("user")
    if not user or user["role_name"] not in allowed_roles:
        st.error("🚫 You don't have permission to view this page.")
        st.stop()


def require_login():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.warning("Please log in to continue.")
        st.stop()
