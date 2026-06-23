"""
Database connection utility for DatAInspire Task Command Center.
Provides a single point of access to the SQLite database with
foreign keys enabled and row factory set for dict-like access.
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager

# Resolve paths relative to this file so the app works regardless of
# the current working directory it's launched from.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = BASE_DIR / "data" / "db"
DB_PATH = DB_DIR / "datainspire.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"

DB_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Return a new SQLite connection with sane defaults."""
    conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_cursor(commit: bool = False):
    """
    Context manager yielding a cursor. Commits automatically if
    commit=True and no exception was raised; always closes the
    connection afterward.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(force: bool = False):
    """
    Initialize the database using schema.sql.
    If force=True, deletes the existing database file first
    (used only by the reset-database admin utility, never automatically).
    """
    if force and DB_PATH.exists():
        os.remove(DB_PATH)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def database_exists() -> bool:
    return DB_PATH.exists()


def is_initialized() -> bool:
    """Check whether the core tables have been created."""
    if not database_exists():
        return False
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        return cur.fetchone() is not None
    finally:
        conn.close()
