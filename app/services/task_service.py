"""
Task service: all business logic for creating, assigning, updating,
submitting, approving and querying tasks. This is the heart of the
workflow enforcement described in the system spec.
"""

from datetime import datetime, date
from app.database.db import get_cursor
from app.services.auth_service import log_activity

STATUS_NOT_STARTED = "Not Started"
STATUS_IN_PROGRESS = "In Progress"
STATUS_SUBMITTED = "Submitted for Review"
STATUS_APPROVED = "Approved"
STATUS_RETURNED = "Returned for Revision"

ALL_STATUSES = [
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_SUBMITTED,
    STATUS_APPROVED,
    STATUS_RETURNED,
]

PRIORITIES = ["High", "Medium", "Low"]

PRIORITY_COLORS = {
    "High": "#E63946",    # red - urgent
    "Medium": "#F4A300",  # yellow/amber - medium
    "Low": "#2A9D8F",     # green - low
}

STATUS_COLORS = {
    STATUS_NOT_STARTED: "#94A3B8",
    STATUS_IN_PROGRESS: "#3B82F6",
    STATUS_SUBMITTED: "#A855F7",
    STATUS_APPROVED: "#22C55E",
    STATUS_RETURNED: "#F97316",
}

# Statuses a regular EXCO member is allowed to set themselves
EXCO_ALLOWED_STATUS_TRANSITIONS = {
    STATUS_NOT_STARTED: [STATUS_IN_PROGRESS],
    STATUS_IN_PROGRESS: [STATUS_SUBMITTED],
    STATUS_RETURNED: [STATUS_IN_PROGRESS, STATUS_SUBMITTED],
}


def _generate_task_code(cur) -> str:
    cur.execute("SELECT SELECT COUNT(*) AS cnt FROM tasks WHERE is_deleted = 0")
    row = cur.fetchone()

    # Handle None / string safely
    count = int(row["cnt"]) if row and row["cnt"] is not None else 0

    return f"TASK-{count + 1:04d}"


def create_task(
    title: str,
    description: str,
    department_id: int,
    assigned_to: int | None,
    created_by: int,
    priority: str,
    deadline: str,  # ISO date string YYYY-MM-DD
):
    if not title.strip():
        return False, "Task title is required.", None
    if priority not in PRIORITIES:
        return False, "Invalid priority level.", None

    with get_cursor(commit=True) as cur:
        task_code = _generate_task_code(cur)
        cur.execute(
            """
            INSERT INTO tasks
                (task_code, title, description, department_id, assigned_to,
                 created_by, priority, status, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_code,
                title.strip(),
                description.strip() if description else "",
                department_id,
                assigned_to,
                created_by,
                priority,
                STATUS_NOT_STARTED,
                deadline,
            ),
        )
        task_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO task_status_history (task_id, changed_by, old_status, new_status, note)
            VALUES (?, ?, NULL, ?, 'Task created')
            """,
            (task_id, created_by, STATUS_NOT_STARTED),
        )
        log_activity(cur, created_by, "TASK_CREATED", f"Created {task_code}: {title}")

    return True, f"Task {task_code} created successfully.", task_id


def update_task_details(task_id: int, updated_by: int, **fields):
    """
    President-only: update title, description, department, assigned_to,
    priority, deadline. Pass only the fields you want to change as kwargs.
    """
    allowed_fields = {"title", "description", "department_id", "assigned_to", "priority", "deadline"}
    set_clauses = []
    values = []
    for key, val in fields.items():
        if key in allowed_fields:
            set_clauses.append(f"{key} = ?")
            values.append(val)

    if not set_clauses:
        return False, "No valid fields to update."

    set_clauses.append("updated_at = ?")
    values.append(datetime.now().isoformat(timespec="seconds"))
    values.append(task_id)

    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = ?",
            values,
        )
        log_activity(cur, updated_by, "TASK_UPDATED", f"Updated task #{task_id}: fields {list(fields.keys())}")

    return True, "Task updated."


def change_status(task_id: int, new_status: str, changed_by: int, note: str = "", is_president: bool = False):
    """
    Enforces the workflow:
      Not Started -> In Progress -> Submitted for Review -> Approved
                                                          -> Returned for Revision -> In Progress -> ...
    EXCO members can only move through EXCO_ALLOWED_STATUS_TRANSITIONS.
    Only the President can set Approved or Returned for Revision.
    """
    if new_status not in ALL_STATUSES:
        return False, "Invalid status."

    with get_cursor() as cur:
        cur.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            return False, "Task not found."
        old_status = row["status"]

    if new_status in (STATUS_APPROVED, STATUS_RETURNED) and not is_president:
        return False, "Only the President can approve or return tasks."

    if not is_president:
        allowed = EXCO_ALLOWED_STATUS_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            return False, f"You cannot move a task from '{old_status}' to '{new_status}'."

    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_cursor(commit=True) as cur:
        update_sql = "UPDATE tasks SET status = ?, updated_at = ?"
        params = [new_status, now_iso]

        if new_status == STATUS_SUBMITTED:
            update_sql += ", submission_date = ?"
            params.append(now_iso)
        if new_status == STATUS_APPROVED:
            update_sql += ", approval_date = ?, approval_notes = ?"
            params.extend([now_iso, note])
        if new_status == STATUS_RETURNED:
            update_sql += ", approval_notes = ?"
            params.append(note)

        update_sql += " WHERE task_id = ?"
        params.append(task_id)
        cur.execute(update_sql, params)

        cur.execute(
            """
            INSERT INTO task_status_history (task_id, changed_by, old_status, new_status, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, changed_by, old_status, new_status, note),
        )
        log_activity(cur, changed_by, "STATUS_CHANGE", f"Task #{task_id}: {old_status} -> {new_status}")

    return True, f"Task status changed to '{new_status}'."


def delete_task(task_id: int, deleted_by: int):
    """Soft delete — President only (enforced at the page layer)."""
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE tasks SET is_deleted = 1 WHERE task_id = ?", (task_id,))
        log_activity(cur, deleted_by, "TASK_DELETED", f"Task #{task_id} deleted")
    return True, "Task deleted."


def get_task(task_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT t.*, d.department_name,
                   u1.full_name AS assigned_to_name, u1.username AS assigned_to_username,
                   u2.full_name AS created_by_name
            FROM tasks t
            LEFT JOIN departments d ON t.department_id = d.department_id
            LEFT JOIN users u1 ON t.assigned_to = u1.user_id
            LEFT JOIN users u2 ON t.created_by = u2.user_id
            WHERE t.task_id = ?
            """,
            (task_id,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def list_tasks(
    department_id: int | None = None,
    assigned_to: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    include_deleted: bool = False,
):
    query = """
        SELECT t.*, d.department_name,
               u1.full_name AS assigned_to_name,
               u2.full_name AS created_by_name
        FROM tasks t
        LEFT JOIN departments d ON t.department_id = d.department_id
        LEFT JOIN users u1 ON t.assigned_to = u1.user_id
        LEFT JOIN users u2 ON t.created_by = u2.user_id
        WHERE 1=1
    """
    params = []
    if not include_deleted:
        query += " AND t.is_deleted = 0"
    if department_id:
        query += " AND t.department_id = ?"
        params.append(department_id)
    if assigned_to:
        query += " AND t.assigned_to = ?"
        params.append(assigned_to)
    if status:
        query += " AND t.status = ?"
        params.append(status)
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)
    if search:
        query += " AND (t.title LIKE ? OR t.description LIKE ? OR t.task_code LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])

    query += " ORDER BY t.deadline ASC"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def is_overdue(task: dict) -> bool:
    if task["status"] == STATUS_APPROVED:
        return False
    try:
        deadline_date = datetime.fromisoformat(task["deadline"]).date()
    except ValueError:
        deadline_date = date.fromisoformat(task["deadline"][:10])
    return deadline_date < date.today()


def add_comment(task_id: int, user_id: int, message: str):
    if not message.strip():
        return False, "Comment cannot be empty."
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO comments (task_id, user_id, message) VALUES (?, ?, ?)",
            (task_id, user_id, message.strip()),
        )
        log_activity(cur, user_id, "COMMENT_ADDED", f"Comment on task #{task_id}")
    return True, "Comment added."


def get_comments(task_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT c.*, u.full_name, u.username, r.role_name
            FROM comments c
            JOIN users u ON c.user_id = u.user_id
            JOIN roles r ON u.role_id = r.role_id
            WHERE c.task_id = ?
            ORDER BY c.created_at ASC
            """,
            (task_id,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_status_history(task_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT h.*, u.full_name, u.username
            FROM task_status_history h
            JOIN users u ON h.changed_by = u.user_id
            WHERE h.task_id = ?
            ORDER BY h.changed_at ASC
            """,
            (task_id,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def add_attachment(task_id: int, uploaded_by: int, file_name: str, stored_path: str, file_type: str, file_size_kb: float):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO attachments (task_id, uploaded_by, file_name, stored_path, file_type, file_size_kb)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, uploaded_by, file_name, stored_path, file_type, file_size_kb),
        )
        log_activity(cur, uploaded_by, "FILE_UPLOADED", f"Uploaded '{file_name}' to task #{task_id}")
    return True, "File uploaded."


def get_attachments(task_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT a.*, u.full_name AS uploaded_by_name
            FROM attachments a
            JOIN users u ON a.uploaded_by = u.user_id
            WHERE a.task_id = ?
            ORDER BY a.uploaded_at DESC
            """,
            (task_id,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]
