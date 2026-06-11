"""Purchases: atomic header + line items, history filters, owner cancel (FR-4)."""

from __future__ import annotations

from db import database


def create_purchase(purchase_date: str, supplier_id: int, items: list[dict],
                    user_id: int, invoice_ref: str | None = None,
                    notes: str | None = None) -> int:
    """Record a purchase in one transaction (NFR-4). Stock increases implicitly
    because v_current_stock derives from purchase_items (FR-4.2).

    items: [{"book_id": int, "quantity": int, "unit_price": int paise}, ...]
    """
    if not items:
        raise ValueError("A purchase needs at least one line item.")
    for item in items:
        if item["quantity"] <= 0:
            raise ValueError("Quantities must be positive.")
        if item["unit_price"] < 0:
            raise ValueError("Unit prices cannot be negative.")
    total = sum(i["quantity"] * i["unit_price"] for i in items)

    conn = database.get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO purchases (purchase_date, supplier_id, invoice_ref, notes,"
                " total_amount, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                (purchase_date, supplier_id, invoice_ref, notes, total, user_id),
            )
            purchase_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO purchase_items (purchase_id, book_id, quantity, unit_price)"
                " VALUES (?, ?, ?, ?)",
                [(purchase_id, i["book_id"], i["quantity"], i["unit_price"]) for i in items],
            )
        return purchase_id
    finally:
        conn.close()


def list_purchases(start: str | None = None, end: str | None = None,
                   supplier_id: int | None = None, book_id: int | None = None,
                   include_cancelled: bool = True) -> list[dict]:
    """Purchase headers with supplier/user names, filterable (FR-4.4)."""
    conn = database.get_connection()
    try:
        where, params = [], []
        if start:
            where.append("p.purchase_date >= ?")
            params.append(start)
        if end:
            where.append("p.purchase_date <= ?")
            params.append(end)
        if supplier_id:
            where.append("p.supplier_id = ?")
            params.append(supplier_id)
        if book_id:
            where.append(
                "EXISTS (SELECT 1 FROM purchase_items pi"
                " WHERE pi.purchase_id = p.id AND pi.book_id = ?)")
            params.append(book_id)
        if not include_cancelled:
            where.append("p.is_cancelled = 0")
        sql = (
            "SELECT p.*, s.name AS supplier_name, u.full_name AS created_by_name,"
            " (SELECT COUNT(*) FROM purchase_items pi WHERE pi.purchase_id = p.id) AS line_count,"
            " (SELECT SUM(pi.quantity) FROM purchase_items pi WHERE pi.purchase_id = p.id) AS total_qty"
            " FROM purchases p"
            " JOIN suppliers s ON s.id = p.supplier_id"
            " JOIN users u ON u.id = p.created_by"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY p.purchase_date DESC, p.id DESC"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_purchase_items(purchase_id: int) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT pi.*, b.code, b.title_devanagari, b.title_roman,"
            " pi.quantity * pi.unit_price AS line_total"
            " FROM purchase_items pi JOIN books b ON b.id = pi.book_id"
            " WHERE pi.purchase_id = ? ORDER BY pi.id",
            (purchase_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def cancel_purchase(purchase_id: int, owner_id: int, reason: str) -> None:
    """Owner-only soft cancel (FR-4.5): stock reverses via the derived views."""
    if not reason.strip():
        raise ValueError("A cancellation reason is required.")
    conn = database.get_connection()
    try:
        with conn:
            cur = conn.execute(
                "UPDATE purchases SET is_cancelled = 1, cancelled_by = ?, cancel_reason = ?"
                " WHERE id = ? AND is_cancelled = 0",
                (owner_id, reason.strip(), purchase_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Purchase not found or already cancelled.")
    finally:
        conn.close()
