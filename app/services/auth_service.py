"""
Authentication service for DatAInspire Task Command Center.
Handles login verification, session state management, and user creation.
"""

from datetime import datetime
from app.database.db import get_cursor
from app.utils.security import (
    create_password_record,
    verify_password,
    validate_password_strength,
)

ROLE_PRESIDENT = "President"
ROLE_EXCO = "EXCO"


def authenticate(username: str, password: str):
    """
    Verify credentials. Returns a dict with user info on success, or None.
    """
    username = username.strip()
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.email, u.password_hash,
                   u.salt, u.role_id, u.department_id, u.is_active,
                   u.avatar_color, u.must_change_password,
                   r.role_name, d.department_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE u.username = ? COLLATE NOCASE
            """,
            (username,),
        )
        row = cur.fetchone()

    if row is None:
        return None
    if not row["is_active"]:
        return None
    if not verify_password(password, row["salt"], row["password_hash"]):
        return None

    # update last_login
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET last_login = ? WHERE user_id = ?",
            (datetime.now().isoformat(timespec="seconds"), row["user_id"]),
        )
        log_activity(cur, row["user_id"], "LOGIN", f"User {row['username']} logged in")

    return {
        "user_id": row["user_id"],
        "full_name": row["full_name"],
        "username": row["username"],
        "email": row["email"],
        "role_id": row["role_id"],
        "role_name": row["role_name"],
        "department_id": row["department_id"],
        "department_name": row["department_name"],
        "avatar_color": row["avatar_color"],
        "must_change_password": bool(row["must_change_password"]),
    }


def log_activity(cur, user_id, action: str, details: str = ""):
    """Insert an activity log row using an existing cursor (caller commits)."""
    cur.execute(
        "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, action, details),
    )


def create_user(
    full_name: str,
    username: str,
    email: str,
    password: str,
    role_name: str,
    department_id: int | None,
    created_by_user_id: int | None = None,
    avatar_color: str = "#6C5CE7",
):
    """
    Create a new user account. Returns (success: bool, message: str, user_id|None).
    """
    full_name = full_name.strip()
    username = username.strip()
    email = email.strip() if email else None

    if not full_name or not username:
        return False, "Full name and username are required.", None

    is_valid, msg = validate_password_strength(password)
    if not is_valid:
        return False, msg, None

    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE username = ? COLLATE NOCASE", (username,))
        if cur.fetchone():
            return False, "That username is already taken.", None

        cur.execute("SELECT role_id FROM roles WHERE role_name = ?", (role_name,))
        role_row = cur.fetchone()
        if not role_row:
            return False, f"Role '{role_name}' does not exist.", None
        role_id = role_row["role_id"]

    pwd_hash, salt = create_password_record(password)

    with get_cursor(commit=True) as cur:
        try:
            cur.execute(
                """
                INSERT INTO users
                    (full_name, username, email, password_hash, salt,
                     role_id, department_id, avatar_color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (full_name, username, email, pwd_hash, salt, role_id, department_id, avatar_color),
            )
            new_id = cur.lastrowid
            log_activity(
                cur,
                created_by_user_id,
                "USER_CREATED",
                f"Created user '{username}' ({role_name})",
            )
            return True, "User created successfully.", new_id
        except Exception as e:
            return False, f"Could not create user: {e}", None


def change_password(user_id: int, new_password: str):
    is_valid, msg = validate_password_strength(new_password)
    if not is_valid:
        return False, msg

    pwd_hash, salt = create_password_record(new_password)
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET password_hash = ?, salt = ?, must_change_password = 0 WHERE user_id = ?",
            (pwd_hash, salt, user_id),
        )
        log_activity(cur, user_id, "PASSWORD_CHANGED", "User changed their password")
    return True, "Password updated successfully."


def get_user_by_id(user_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT u.*, r.role_name, d.department_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE u.user_id = ?
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def is_president(role_name: str) -> bool:
    return role_name == ROLE_PRESIDENT
