-- DatAInspire Task Command Center
-- Database Schema (SQLite)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------
-- ROLES
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    role_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name   TEXT NOT NULL UNIQUE,           -- 'President' or 'EXCO'
    description TEXT
);

-- ----------------------------------------------------------------
-- DEPARTMENTS / TASK GROUPS
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL UNIQUE,
    description      TEXT,
    is_custom        INTEGER NOT NULL DEFAULT 0,   -- 0 = predefined, 1 = president-created
    created_by        INTEGER,                      -- user_id of creator (NULL for seed data)
    created_at         TEXT NOT NULL DEFAULT (datetime('now')),
    is_active           INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------
-- USERS
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name      TEXT NOT NULL,
    username       TEXT NOT NULL UNIQUE,
    email          TEXT UNIQUE,
    password_hash  TEXT NOT NULL,
    salt           TEXT NOT NULL,
    role_id        INTEGER NOT NULL,
    department_id  INTEGER,
    avatar_color   TEXT DEFAULT '#6C5CE7',
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    last_login     TEXT,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------
-- TASKS
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    task_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_code        TEXT NOT NULL UNIQUE,     -- e.g. TASK-0001
    title            TEXT NOT NULL,
    description      TEXT,
    department_id    INTEGER NOT NULL,
    assigned_to      INTEGER,                  -- user_id, nullable if assigned to whole dept
    created_by       INTEGER NOT NULL,         -- President's user_id
    priority         TEXT NOT NULL CHECK (priority IN ('High','Medium','Low')) DEFAULT 'Medium',
    status           TEXT NOT NULL CHECK (status IN (
                          'Not Started','In Progress','Submitted for Review',
                          'Approved','Returned for Revision'
                      )) DEFAULT 'Not Started',
    date_assigned    TEXT NOT NULL DEFAULT (datetime('now')),
    deadline         TEXT NOT NULL,
    submission_date  TEXT,
    approval_date    TEXT,
    approval_notes   TEXT,
    is_deleted       INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- ----------------------------------------------------------------
-- TASK STATUS HISTORY (audit trail)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_status_history (
    history_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        INTEGER NOT NULL,
    changed_by     INTEGER NOT NULL,
    old_status     TEXT,
    new_status     TEXT NOT NULL,
    note           TEXT,
    changed_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

-- ----------------------------------------------------------------
-- COMMENTS / DISCUSSION THREAD
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
    comment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id       INTEGER NOT NULL,
    user_id       INTEGER NOT NULL,
    message       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ----------------------------------------------------------------
-- ATTACHMENTS
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER NOT NULL,
    uploaded_by     INTEGER NOT NULL,
    file_name       TEXT NOT NULL,
    stored_path     TEXT NOT NULL,
    file_type       TEXT,
    file_size_kb    REAL,
    uploaded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
);

-- ----------------------------------------------------------------
-- PERFORMANCE RECORDS (cached/aggregated, recalculated periodically)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS performance_records (
    record_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL,
    period_label       TEXT NOT NULL,         -- e.g. '2026-06' for monthly snapshots
    tasks_assigned     INTEGER NOT NULL DEFAULT 0,
    tasks_completed    INTEGER NOT NULL DEFAULT 0,
    tasks_late         INTEGER NOT NULL DEFAULT 0,
    completion_rate    REAL NOT NULL DEFAULT 0,
    avg_completion_days REAL,
    generated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------
-- ACTIVITY LOG (system-wide audit log)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_log (
    log_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER,
    action        TEXT NOT NULL,
    details       TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------
-- INDEXES
-- ----------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_department ON tasks(department_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline);
CREATE INDEX IF NOT EXISTS idx_comments_task ON comments(task_id);
CREATE INDEX IF NOT EXISTS idx_attachments_task ON attachments(task_id);
CREATE INDEX IF NOT EXISTS idx_history_task ON task_status_history(task_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
