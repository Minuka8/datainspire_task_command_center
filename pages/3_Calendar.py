"""
Calendar — Monthly Calendar, Weekly Timeline, and Deadline Monitoring views.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.page_init import init_page
init_page("Calendar", "📅")

import streamlit as st
import calendar as pycal
from datetime import date, timedelta
from app.services.task_service import list_tasks, is_overdue, PRIORITY_COLORS
from app.components.widgets import section_label

user = st.session_state["user"]
is_president = user["role_name"] == "President"

st.title("📅 Calendar & Timeline")

scope = st.radio(
    "Scope", ["My Tasks", "All Tasks"] if is_president else ["My Tasks"],
    horizontal=True, label_visibility="collapsed",
)
assigned_filter = None if (is_president and scope == "All Tasks") else user["user_id"]
all_tasks = list_tasks(assigned_to=assigned_filter)

tab_month, tab_week, tab_overdue = st.tabs(["🗓️ Monthly Calendar", "📈 Weekly Timeline", "⏰ Deadline Monitoring"])

# =====================================================================
# MONTHLY CALENDAR
# =====================================================================
with tab_month:
    today = date.today()
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    if "cal_year" not in st.session_state:
        st.session_state["cal_year"] = today.year
        st.session_state["cal_month"] = today.month

    with col_nav1:
        if st.button("← Previous"):
            m = st.session_state["cal_month"] - 1
            y = st.session_state["cal_year"]
            if m < 1:
                m, y = 12, y - 1
            st.session_state["cal_month"], st.session_state["cal_year"] = m, y
    with col_nav3:
        if st.button("Next →"):
            m = st.session_state["cal_month"] + 1
            y = st.session_state["cal_year"]
            if m > 12:
                m, y = 1, y + 1
            st.session_state["cal_month"], st.session_state["cal_year"] = m, y

    year, month = st.session_state["cal_year"], st.session_state["cal_month"]
    with col_nav2:
        st.markdown(f"<h4 style='text-align:center;'>{pycal.month_name[month]} {year}</h4>", unsafe_allow_html=True)

    # Build map of day -> tasks due that day
    tasks_by_day = {}
    for t in all_tasks:
        try:
            d = date.fromisoformat(t["deadline"][:10])
        except ValueError:
            continue
        if d.year == year and d.month == month:
            tasks_by_day.setdefault(d.day, []).append(t)

    cal = pycal.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)

    header_cols = st.columns(7)
    for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        header_cols[i].markdown(f"**{day_name}**")

    for week in weeks:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            with cols[i]:
                if day_num == 0:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    continue
                is_today = (day_num == today.day and month == today.month and year == today.year)
                border_style = "2px solid var(--accent)" if is_today else "1px solid var(--border)"
                day_tasks = tasks_by_day.get(day_num, [])

                dots = ""
                for dt in day_tasks[:4]:
                    color = PRIORITY_COLORS.get(dt["priority"], "#6C5CE7")
                    dots += f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{color};margin:1px;"></span>'

                st.markdown(
                    f"""
                    <div style="border:{border_style}; border-radius:8px; padding:6px 8px; min-height:64px; margin-bottom:6px;">
                        <div style="font-size:12px; font-weight:600; color:var(--text-muted);">{day_num}</div>
                        <div style="margin-top:4px;">{dots}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if day_tasks:
                    with st.popover(f"{len(day_tasks)} task(s)", width='stretch'):
                        for dt in day_tasks:
                            st.markdown(f"**{dt['title']}** — {dt['priority']} priority")
                            st.caption(f"{dt['task_code']} · {dt['status']}")

# =====================================================================
# WEEKLY TIMELINE
# =====================================================================
with tab_week:
    week_start = today - timedelta(days=today.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]

    section_label(f"Week of {week_start.strftime('%b %d, %Y')}")

    for d in week_days:
        day_tasks = [t for t in all_tasks if t["deadline"][:10] == d.isoformat()]
        is_today = d == today
        label = f"**{d.strftime('%A, %b %d')}**" + (" — Today" if is_today else "")
        with st.container(border=True):
            st.markdown(label)
            if day_tasks:
                for t in sorted(day_tasks, key=lambda x: {"High": 0, "Medium": 1, "Low": 2}[x["priority"]]):
                    color = PRIORITY_COLORS.get(t["priority"], "#6C5CE7")
                    overdue_txt = " ⚠️ Overdue" if is_overdue(t) else ""
                    st.markdown(
                        f"""<div style="border-left:3px solid {color}; padding-left:10px; margin:6px 0;">
                        <b>{t['title']}</b> <span style="color:var(--text-muted); font-size:12px;">({t['task_code']} · {t['status']}{overdue_txt})</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No deadlines.")

# =====================================================================
# DEADLINE MONITORING (overdue + upcoming)
# =====================================================================
with tab_overdue:
    overdue_tasks = [t for t in all_tasks if is_overdue(t)]
    upcoming = [
        t for t in all_tasks
        if not is_overdue(t) and t["status"] != "Approved"
        and 0 <= (date.fromisoformat(t["deadline"][:10]) - today).days <= 3
    ]

    section_label(f"⚠️ Overdue ({len(overdue_tasks)})")
    if overdue_tasks:
        for t in overdue_tasks:
            days_late = (today - date.fromisoformat(t["deadline"][:10])).days
            st.error(f"**{t['title']}** ({t['task_code']}) — {days_late} day(s) overdue · {t['assigned_to_name'] or 'Unassigned'} · {t['department_name']}")
    else:
        st.success("No overdue tasks. 🎉")

    st.markdown("<br>", unsafe_allow_html=True)
    section_label(f"🔔 Due Within 3 Days ({len(upcoming)})")
    if upcoming:
        for t in upcoming:
            d_left = (date.fromisoformat(t["deadline"][:10]) - today).days
            st.warning(f"**{t['title']}** ({t['task_code']}) — due in {d_left} day(s) · {t['assigned_to_name'] or 'Unassigned'}")
    else:
        st.info("Nothing urgent in the next 3 days.")
