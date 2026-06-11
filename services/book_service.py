"""Book catalog: CRUD, code generation, dual-script search (FR-2)."""

from __future__ import annotations

import re
import sqlite3

from db import database

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

EDITABLE_FIELDS = (
    "title_devanagari", "title_roman", "author_roman", "author_devanagari",
    "publisher", "category", "language", "isbn",
    "retail_price", "wholesale_price", "low_stock_threshold",
)


def contains_devanagari(text: str) -> bool:
    return bool(_DEVANAGARI_RE.search(text or ""))


def generate_code(conn: sqlite3.Connection) -> str:
    """Auto book code BK-0001 (FR-2.1)."""
    next_id = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM books").fetchone()[0]
    return f"BK-{next_id:04d}"


def search_books(term: str = "", include_inactive: bool = False) -> list[dict]:
    """Single search box across both scripts, authors, and code (TDD §5.3)."""
    conn = database.get_connection()
    try:
        where = [] if include_inactive else ["is_active = 1"]
        params: list = []
        if term.strip():
            like = f"%{term.strip()}%"
            where.append(
                "(title_roman LIKE ? COLLATE NOCASE OR title_devanagari LIKE ?"
                " OR author_roman LIKE ? COLLATE NOCASE OR author_devanagari LIKE ?"
                " OR code LIKE ? COLLATE NOCASE)"
            )
            params += [like] * 5
            # Weight title matches of the typed script first (TDD §5.3).
            if contains_devanagari(term):
                order = ("CASE WHEN title_devanagari LIKE ? THEN 0"
                         " WHEN title_roman LIKE ? THEN 1 ELSE 2 END, title_roman")
            else:
                order = ("CASE WHEN title_roman LIKE ? THEN 0"
                         " WHEN title_devanagari LIKE ? THEN 1 ELSE 2 END, title_roman")
            params += [like, like]
        else:
            order = "title_roman"
        sql = "SELECT * FROM books"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {order}"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def find_duplicates(title_roman: str, title_devanagari: str, publisher: str,
                    exclude_id: int | None = None) -> list[dict]:
    """Same title (either script) + same publisher → possible duplicate (FR-2.4)."""
    conn = database.get_connection()
    try:
        sql = ("SELECT * FROM books WHERE COALESCE(publisher,'') = COALESCE(?, '')"
               " AND (title_roman = ? COLLATE NOCASE OR title_devanagari = ?)")
        params: list = [publisher or "", title_roman.strip(), title_devanagari.strip()]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def add_book(fields: dict) -> int:
    conn = database.get_connection()
    try:
        with conn:
            code = generate_code(conn)
            cols = ", ".join(EDITABLE_FIELDS)
            placeholders = ", ".join("?" for _ in EDITABLE_FIELDS)
            cur = conn.execute(
                f"INSERT INTO books (code, {cols}) VALUES (?, {placeholders})",
                [code] + [fields.get(f) for f in EDITABLE_FIELDS],
            )
        return cur.lastrowid
    finally:
        conn.close()


def update_book(book_id: int, fields: dict) -> None:
    conn = database.get_connection()
    try:
        assignments = ", ".join(f"{f} = ?" for f in EDITABLE_FIELDS)
        with conn:
            conn.execute(
                f"UPDATE books SET {assignments} WHERE id = ?",
                [fields.get(f) for f in EDITABLE_FIELDS] + [book_id],
            )
    finally:
        conn.close()


def set_active(book_id: int, active: bool) -> None:
    """Deactivate instead of delete once a book has history (FR-2.5)."""
    conn = database.get_connection()
    try:
        with conn:
            conn.execute("UPDATE books SET is_active = ? WHERE id = ?",
                         (1 if active else 0, book_id))
    finally:
        conn.close()


def get_book(book_id: int) -> dict | None:
    conn = database.get_connection()
    try:
        row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_active_books() -> list[dict]:
    """Active books with current stock — used by sale/purchase entry screens."""
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT b.*, v.stock FROM books b"
            " JOIN v_current_stock v ON v.book_id = b.id"
            " WHERE b.is_active = 1 ORDER BY b.title_roman"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
