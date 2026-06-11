"""Suppliers and wholesale customers (FR-3). Both tables share one shape."""

from __future__ import annotations

from db import database

_TABLES = {"supplier": "suppliers", "customer": "wholesale_customers"}

FIELDS = ("name", "contact_person", "phone", "address", "notes")


def _table(kind: str) -> str:
    return _TABLES[kind]


def list_contacts(kind: str, include_inactive: bool = False) -> list[dict]:
    conn = database.get_connection()
    try:
        sql = f"SELECT * FROM {_table(kind)}"
        if not include_inactive:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY name"
        return [dict(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def add_contact(kind: str, fields: dict) -> int:
    conn = database.get_connection()
    try:
        with conn:
            cur = conn.execute(
                f"INSERT INTO {_table(kind)} ({', '.join(FIELDS)})"
                f" VALUES ({', '.join('?' for _ in FIELDS)})",
                [fields.get(f) for f in FIELDS],
            )
        return cur.lastrowid
    finally:
        conn.close()


def update_contact(kind: str, contact_id: int, fields: dict) -> None:
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                f"UPDATE {_table(kind)} SET {', '.join(f'{f} = ?' for f in FIELDS)}"
                " WHERE id = ?",
                [fields.get(f) for f in FIELDS] + [contact_id],
            )
    finally:
        conn.close()


def set_active(kind: str, contact_id: int, active: bool) -> None:
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                f"UPDATE {_table(kind)} SET is_active = ? WHERE id = ?",
                (1 if active else 0, contact_id),
            )
    finally:
        conn.close()
