"""Database connection and lifecycle management for Kandezhuthu AI.

Uses Python standard library sqlite3 with WAL mode and FTS5 full-text indexing.
"""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

# Default DB file location: data/kandezhuthu.db relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "kandezhuthu.db"
DB_PATH = Path(os.environ.get("KANDEZ_DB_PATH", str(DEFAULT_DB_PATH)))
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_db_path() -> Path:
    """Returns the configured database file path, ensuring parent dir exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections with foreign keys and dict row access."""
    db_file = get_db_path()
    conn = sqlite3.connect(str(db_file), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(force_recreate: bool = False) -> None:
    """Initializes the database schema if not already present."""
    db_file = get_db_path()

    if force_recreate and db_file.exists():
        db_file.unlink()

    with get_db_connection() as conn:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)


if __name__ == "__main__":
    init_db()
    print(f"✅ Initialized Kandezhuthu database at: {get_db_path()}")
