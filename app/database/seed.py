"""
Seed script: populates roles and the predefined departments required by
the AI & Data Science Club. Run once after init_database(). Idempotent —
safe to run multiple times (uses INSERT OR IGNORE).
"""

from app.database.db import get_cursor

DEFAULT_ROLES = [
    ("President", "Full administrative access to the system."),
    ("EXCO", "Executive committee member / general user with task-level access."),
]

DEFAULT_DEPARTMENTS = [
    ("PR", "Public Relations"),
    ("Secretary", "Secretarial and documentation duties"),
    ("Treasury", "Finance and budgeting"),
    ("Sergeant-at-Arms", "Discipline and order"),
    ("Membership", "Membership growth and engagement"),
    ("Webmaster", "Website and digital infrastructure"),
    ("Events", "Event planning and execution"),
    ("Project Committees", "General project-based committees"),
]


def seed_roles():
    with get_cursor(commit=True) as cur:
        for role_name, description in DEFAULT_ROLES:
            cur.execute(
                "INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)",
                (role_name, description),
            )


def seed_departments():
    with get_cursor(commit=True) as cur:
        for dept_name, description in DEFAULT_DEPARTMENTS:
            cur.execute(
                """
                INSERT OR IGNORE INTO departments (department_name, description, is_custom)
                VALUES (?, ?, 0)
                """,
                (dept_name, description),
            )


def run_seed():
    seed_roles()
    seed_departments()
