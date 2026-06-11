"""Daily backup-on-launch (NFR-6): one copy per day via the sqlite3 backup API
(safe while WAL is active), keeping the most recent 30 copies."""

from __future__ import annotations

import datetime as dt
import sqlite3

from db import database

KEEP_COPIES = 30


def backup_if_needed() -> str | None:
    """Copy shop.db to data/backups/shop-YYYY-MM-DD.db once per day.
    Returns the backup path if a new backup was made."""
    if not database.DB_PATH.exists():
        return None
    backups_dir = database.DATA_DIR / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    dest = backups_dir / f"shop-{dt.date.today().isoformat()}.db"
    if dest.exists():
        return None

    src = sqlite3.connect(str(database.DB_PATH))
    dst = sqlite3.connect(str(dest))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    old = sorted(backups_dir.glob("shop-*.db"))
    for stale in old[:-KEEP_COPIES]:
        stale.unlink()
    return str(dest)
