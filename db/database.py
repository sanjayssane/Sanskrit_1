"""Connection management, versioned migrations, and initial user seeding.

Migration mechanism (DATABASE_PLAN.md §3): plain .sql files in db/migrations/
named NNNN_description.sql, applied in numeric order. SQLite's
``PRAGMA user_version`` tracks the last applied number. Each migration runs
inside a single transaction so a failure leaves the database untouched.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import bcrypt

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "shop.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

DEFAULT_PASSWORD = "change@123"

INITIAL_USERS = [
    ("owner", "Shop Owner", "owner"),
    ("employee1", "Employee One", "employee"),
    ("employee2", "Employee Two", "employee"),
]


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with FK enforcement, WAL mode, and Row factory."""
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrate(conn: sqlite3.Connection) -> int:
    """Apply pending migrations in order. Idempotent. Returns final version."""
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = int(path.name.split("_", 1)[0])
        if version <= current:
            continue
        sql = path.read_text(encoding="utf-8")
        script = f"BEGIN;\n{sql}\nPRAGMA user_version = {version};\nCOMMIT;"
        try:
            conn.executescript(script)
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        current = version
    return current


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_initial_users(conn: sqlite3.Connection) -> None:
    """Seed owner/employee1/employee2 on an empty users table (PRD §3.3)."""
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count:
        return
    with conn:
        for username, full_name, role in INITIAL_USERS:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role, must_change_pw)"
                " VALUES (?, ?, ?, ?, 1)",
                (username, hash_password(DEFAULT_PASSWORD), full_name, role),
            )


def init_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open + migrate + seed. Safe to call at every app startup."""
    conn = get_connection(db_path)
    migrate(conn)
    seed_initial_users(conn)
    return conn
