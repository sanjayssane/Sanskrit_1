"""Inventory: current stock view, per-book ledger, manual adjustments (FR-6)."""

from __future__ import annotations

from db import database


def current_stock(include_inactive: bool = False) -> list[dict]:
    """Per-book stock, last purchase price, and stock value (FR-6.1/6.2)."""
    conn = database.get_connection()
    try:
        sql = ("SELECT *, stock * last_purchase_price AS stock_value,"
               " (stock <= low_stock_threshold) AS is_low FROM v_current_stock")
        if not include_inactive:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY title_roman"
        return [dict(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def low_stock_books() -> list[dict]:
    return [b for b in current_stock() if b["is_low"]]


def stock_ledger(book_id: int) -> list[dict]:
    """Chronological movements with running balance (FR-6.5)."""
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT l.*, u.full_name AS created_by_name FROM v_stock_ledger l"
            " JOIN users u ON u.id = l.created_by"
            " WHERE l.book_id = ? ORDER BY l.movement_date, l.created_at, l.reference_id",
            (book_id,),
        ).fetchall()
        ledger, balance = [], 0
        for row in rows:
            entry = dict(row)
            balance += entry["quantity_delta"]
            entry["balance"] = balance
            ledger.append(entry)
        return ledger
    finally:
        conn.close()


def add_adjustment(book_id: int, adjustment_date: str, quantity_delta: int,
                   reason: str, user_id: int) -> int:
    """Owner-only manual adjustment with mandatory reason (FR-6.4)."""
    if quantity_delta == 0:
        raise ValueError("Adjustment quantity cannot be zero.")
    if not reason.strip():
        raise ValueError("A reason is required for every adjustment.")
    conn = database.get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO stock_adjustments"
                " (adjustment_date, book_id, quantity_delta, reason, created_by)"
                " VALUES (?, ?, ?, ?, ?)",
                (adjustment_date, book_id, quantity_delta, reason.strip(), user_id),
            )
        return cur.lastrowid
    finally:
        conn.close()
