"""
Department and user management service (President-only operations
for managing the org structure and club roster).
"""

from app.database.db import get_cursor
from app.services.auth_service import log_activity


def list_departments(active_only: bool = True):
    query = "SELECT * FROM departments"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY is_custom ASC, department_name ASC"
    with get_cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def create_department(name: str, description: str, created_by: int):
    name = name.strip()
    if not name:
        return False, "Department name is required.", None
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM departments WHERE department_name = ? COLLATE NOCASE", (name,))
        if cur.fetchone():
            return False, "A department with that name already exists.", None

    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO departments (department_name, description, is_custom, created_by)
            VALUES (?, ?, 1, ?)
            """,
            (name, description, created_by),
        )
        dept_id = cur.lastrowid
        log_activity(cur, created_by, "DEPARTMENT_CREATED", f"Created department '{name}'")
    return True, "Department created.", dept_id


def deactivate_department(department_id: int, by_user: int):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE departments SET is_active = 0 WHERE department_id = ?", (department_id,))
        log_activity(cur, by_user, "DEPARTMENT_DEACTIVATED", f"Deactivated department #{department_id}")
    return True, "Department deactivated."


def list_users(active_only: bool = True, department_id: int | None = None):
    query = """
        SELECT u.user_id, u.full_name, u.username, u.email, u.is_active,
               u.avatar_color, u.last_login, u.created_at,
               r.role_name, d.department_name, d.department_id
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        LEFT JOIN departments d ON u.department_id = d.department_id
        WHERE 1=1
    """
    params = []
    if active_only:
        query += " AND u.is_active = 1"
    if department_id:
        query += " AND u.department_id = ?"
        params.append(department_id)
    query += " ORDER BY r.role_name ASC, u.full_name ASC"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def update_user(user_id: int, by_user: int, **fields):
    allowed = {"full_name", "email", "department_id", "role_id", "is_active", "avatar_color"}
    set_clauses = []
    values = []
    for key, val in fields.items():
        if key in allowed:
            set_clauses.append(f"{key} = ?")
            values.append(val)
    if not set_clauses:
        return False, "No valid fields to update."
    values.append(user_id)

    with get_cursor(commit=True) as cur:
        cur.execute(f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?", values)
        log_activity(cur, by_user, "USER_UPDATED", f"Updated user #{user_id}: {list(fields.keys())}")
    return True, "User updated."


def deactivate_user(user_id: int, by_user: int):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
        log_activity(cur, by_user, "USER_DEACTIVATED", f"Deactivated user #{user_id}")
    return True, "User deactivated."


def reactivate_user(user_id: int, by_user: int):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
        log_activity(cur, by_user, "USER_REACTIVATED", f"Reactivated user #{user_id}")
    return True, "User reactivated."


def count_presidents() -> int:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS cnt FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE r.role_name = 'President' AND u.is_active = 1
            """
        )
        row = cur.fetchone()
        if row is None:
            return 0
        try:
            return int(row["cnt"])
        except Exception:
            return 0
