"""
Analytics service: dashboard statistics, department performance,
individual performance tracking. Designed so that future integration
with the DatAInspire MERITRACK evaluation system can simply consume
these same aggregate functions (or the performance_records table).
"""

from datetime import date, datetime
from app.database.db import get_cursor


def overall_stats():
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM tasks WHERE is_deleted = 0")
        total = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM tasks WHERE is_deleted = 0 AND status = 'Approved'"
        )
        completed = cur.fetchone()["cnt"]

        cur.execute(
            """
            SELECT COUNT(*) AS cnt FROM tasks
            WHERE is_deleted = 0 AND status != 'Approved' AND deadline < ?
            """,
            (date.today().isoformat(),),
        )
        overdue = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM tasks WHERE is_deleted = 0 AND status = 'Submitted for Review'"
        )
        pending_review = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM tasks WHERE is_deleted = 0 AND status = 'In Progress'"
        )
        in_progress = cur.fetchone()["cnt"]

    active = total - completed
    return {
        "total_tasks": total,
        "active_tasks": active,
        "completed_tasks": completed,
        "overdue_tasks": overdue,
        "pending_review": pending_review,
        "in_progress": in_progress,
    }


def department_stats():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT d.department_id, d.department_name,
                   COUNT(t.task_id) AS total_tasks,
                   SUM(CASE WHEN t.status = 'Approved' THEN 1 ELSE 0 END) AS completed_tasks,
                   SUM(CASE WHEN t.status != 'Approved' AND t.deadline < ? THEN 1 ELSE 0 END) AS overdue_tasks
            FROM departments d
            LEFT JOIN tasks t ON d.department_id = t.department_id AND t.is_deleted = 0
            WHERE d.is_active = 1
            GROUP BY d.department_id, d.department_name
            ORDER BY total_tasks DESC
            """,
            (date.today().isoformat(),),
        )
        rows = cur.fetchall()

    results = []
    for r in rows:
        total = r["total_tasks"] or 0
        completed = r["completed_tasks"] or 0
        rate = round((completed / total) * 100, 1) if total else 0.0
        results.append(
            {
                "department_id": r["department_id"],
                "department_name": r["department_name"],
                "total_tasks": total,
                "completed_tasks": completed,
                "overdue_tasks": r["overdue_tasks"] or 0,
                "completion_rate": rate,
            }
        )
    return results


def individual_stats(user_id: int | None = None):
    """If user_id is None, returns stats for all users (President view)."""
    query = """
        SELECT u.user_id, u.full_name, u.username, d.department_name,
               COUNT(t.task_id) AS total_assigned,
               SUM(CASE WHEN t.status = 'Approved' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN t.status != 'Approved' AND t.deadline < ? THEN 1 ELSE 0 END) AS overdue,
               SUM(CASE WHEN t.status = 'Approved' AND t.submission_date > t.deadline THEN 1 ELSE 0 END) AS late_submissions
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.department_id
        LEFT JOIN tasks t ON u.user_id = t.assigned_to AND t.is_deleted = 0
        WHERE u.is_active = 1
    """
    params = [date.today().isoformat()]
    if user_id:
        query += " AND u.user_id = ?"
        params.append(user_id)
    query += " GROUP BY u.user_id ORDER BY completed DESC"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    results = []
    for r in rows:
        total = r["total_assigned"] or 0
        completed = r["completed"] or 0
        rate = round((completed / total) * 100, 1) if total else 0.0
        results.append(
            {
                "user_id": r["user_id"],
                "full_name": r["full_name"],
                "username": r["username"],
                "department_name": r["department_name"],
                "total_assigned": total,
                "completed": completed,
                "overdue": r["overdue"] or 0,
                "late_submissions": r["late_submissions"] or 0,
                "completion_rate": rate,
            }
        )
    return results


def avg_completion_time_days(user_id: int | None = None):
    """Average days between date_assigned and approval_date for completed tasks."""
    query = """
        SELECT date_assigned, approval_date FROM tasks
        WHERE is_deleted = 0 AND status = 'Approved' AND approval_date IS NOT NULL
    """
    params = []
    if user_id:
        query += " AND assigned_to = ?"
        params.append(user_id)

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    if not rows:
        return None

    total_days = 0
    count = 0
    for r in rows:
        try:
            assigned = datetime.fromisoformat(r["date_assigned"])
            approved = datetime.fromisoformat(r["approval_date"])
            total_days += (approved - assigned).total_seconds() / 86400
            count += 1
        except (ValueError, TypeError):
            continue

    return round(total_days / count, 1) if count else None


def tasks_by_priority_breakdown():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT priority, COUNT(*) AS cnt FROM tasks
            WHERE is_deleted = 0 AND status != 'Approved'
            GROUP BY priority
            """
        )
        rows = cur.fetchall()
    return {r["priority"]: r["cnt"] for r in rows}


def tasks_by_status_breakdown():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT status, COUNT(*) AS cnt FROM tasks
            WHERE is_deleted = 0
            GROUP BY status
            """
        )
        rows = cur.fetchall()
    return {r["status"]: r["cnt"] for r in rows}


def recent_activity(limit: int = 15):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT al.*, u.full_name, u.username
            FROM activity_log al
            LEFT JOIN users u ON al.user_id = u.user_id
            ORDER BY al.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def snapshot_performance_records(period_label: str | None = None):
    """
    Recalculate and persist a snapshot into performance_records for all
    active users. Intended to be called periodically (e.g. monthly) by
    the President, and forms the bridge to future MERITRACK integration.
    """
    if period_label is None:
        period_label = date.today().strftime("%Y-%m")

    stats = individual_stats()
    with get_cursor(commit=True) as cur:
        for s in stats:
            avg_days = avg_completion_time_days(s["user_id"])
            cur.execute(
                """
                INSERT INTO performance_records
                    (user_id, period_label, tasks_assigned, tasks_completed,
                     tasks_late, completion_rate, avg_completion_days)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    s["user_id"],
                    period_label,
                    s["total_assigned"],
                    s["completed"],
                    s["late_submissions"],
                    s["completion_rate"],
                    avg_days,
                ),
            )
    return True, f"Performance snapshot saved for {period_label}."
