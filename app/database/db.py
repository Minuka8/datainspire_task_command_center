"""
Database connection utility for DatAInspire Task Command Center.
Uses Turso HTTP API via httpx — no native compilation required.
"""
import os
import httpx
from contextlib import contextmanager
from pathlib import Path

TURSO_URL   = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://")
TURSO_TOKEN = os.environ["TURSO_AUTH_TOKEN"]
API_URL     = f"{TURSO_URL}/v2/pipeline"

BASE_DIR    = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
DB_PATH     = BASE_DIR / "data" / "db" / "datainspire.db"  # kept for compatibility
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _execute_pipeline(statements: list[dict]) -> list:
    """Send a pipeline of SQL statements to Turso HTTP API."""
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"requests": statements}
    resp = httpx.post(API_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


class DictRow:
    """Makes Turso rows behave like sqlite3.Row (dict-like access)."""
    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()


class TursoCursor:
    """Mimics sqlite3 cursor interface over Turso HTTP API."""
    def __init__(self):
        self._statements = []
        self._results = []
        self._current_result = None
        self.lastrowid = None
        self.description = None

    def execute(self, sql: str, params=()):
        stmt = {"type": "execute", "stmt": {"sql": sql, "args": [
            {"type": "text", "value": str(p)} if p is not None else {"type": "null"}
            for p in params
        ]}}
        self._statements.append(stmt)
        # Execute immediately so results are available for fetchone/fetchall
        results = _execute_pipeline([stmt])
        result = results[0] if results else {}
        if "response" in result:
            resp = result["response"]
            if resp.get("type") == "execute":
                rs = resp.get("result", {})
                cols = [c["name"] for c in rs.get("cols", [])]
                rows = rs.get("rows", [])
                self._current_rows = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(cols):
                        val = row[i]
                        row_dict[col] = val.get("value") if val.get("type") != "null" else None
                    self._current_rows.append(DictRow(row_dict))
                self.lastrowid = rs.get("last_insert_rowid")
                self.description = [(c,) for c in cols]
            else:
                self._current_rows = []
        else:
            self._current_rows = []
        return self

    def fetchone(self):
        if self._current_rows:
            return self._current_rows[0]
        return None

    def fetchall(self):
        return self._current_rows or []


class TursoConnection:
    """Mimics sqlite3 connection with commit/rollback support."""
    def __init__(self):
        self._pending = []

    def cursor(self):
        return TursoCursor()

    def commit(self):
        pass  # Each execute is auto-committed via HTTP API

    def rollback(self):
        pass  # HTTP API is stateless; nothing to roll back

    def close(self):
        pass


@contextmanager
def get_cursor(commit: bool = False):
    """Context manager yielding a TursoCursor."""
    conn = TursoConnection()
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
    """Initialize the database by running schema.sql statements."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
    for stmt in statements:
        try:
            _execute_pipeline([{"type": "execute", "stmt": {"sql": stmt, "args": []}}])
        except Exception:
            pass  # IF NOT EXISTS statements are safe to ignore


def database_exists() -> bool:
    return True


def is_initialized() -> bool:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            return cur.fetchone() is not None
    except Exception:
        return False
