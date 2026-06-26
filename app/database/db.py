"""
Database connection utility for DatAInspire Task Command Center.
Provides a single point of access to the Turso (LibSQL) database with
row factory set for dict-like access.
"""
import os
import libsql_experimental as libsql
from contextlib import contextmanager
from pathlib import Path

TURSO_URL   = os.environ["TURSO_DATABASE_URL"]
TURSO_TOKEN = os.environ["TURSO_AUTH_TOKEN"]

# Keep these so other modules that import them don't break
BASE_DIR    = Path(__file__).resolve().parent.parent.parent
DB_DIR      = BASE_DIR / "data" / "db"
DB_PATH     = DB_DIR / "datainspire.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Return a new Turso/LibSQL connection."""
    return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)


class DictRow:
    """Wraps a Turso row so it behaves like sqlite3.Row (dict-like access)."""
    def __init__(self, row, description):
        self._data = {description[i][0]: row[i] for i in range(len(description))}

    def __getitem__(self, key):
        return self._data[key]

    def keys(self):
        return self._data.keys()

    def get(self, key, default=None):
        return self._data.get(key, default)


class DictCursor:
    """Wraps a Turso cursor to return DictRow objects."""
    def __init__(self, cursor, conn):
        self._cursor = cursor
        self._conn = conn

    def execute(self, sql, params=()):
        self._cursor.execute(sql, params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return DictRow(row, self._cursor.description)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [DictRow(r, self._cursor.description) for r in rows]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def description(self):
        return self._cursor.description


@contextmanager
def get_cursor(commit: bool = False):
    """
    Context manager yielding a DictCursor. Commits if commit=True.
    """
    conn = get_connection()
    try:
        raw_cursor = conn.cursor()
        cur = DictCursor(raw_cursor, conn)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(force: bool = False):
    """Initialize the database using schema.sql."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        # Execute each statement individually (Turso doesn't support executescript)
        statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
        cur = conn.cursor()
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception:
                pass  # skip PRAGMA and IF NOT EXISTS duplicates silently
        conn.commit()
    finally:
        conn.close()


def database_exists() -> bool:
    return True  # Turso DB always exists once created


def is_initialized() -> bool:
    """Check whether the core tables have been created."""
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            return cur.fetchone() is not None
    except Exception:
        return False
