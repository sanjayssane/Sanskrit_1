"""Sales: retail/wholesale, atomic write with in-transaction stock re-check
to block overselling (FR-5.5, TDD §5.2), history filters, owner cancel."""

from __future__ import annotations

from collections import defaultdict

from db import database

PAYMENT_METHODS = ("cash", "upi", "card", "cheque")


class InsufficientStockError(ValueError):
    pass


def create_sale(sale_date: str, sale_type: str, items: list[dict], user_id: int,
                customer_id: int | None = None, discount: int = 0,
                payment_method: str = "cash", notes: str | None = None) -> int:
    """Record a sale in one transaction. Stock is re-checked inside the
    transaction so two simultaneous counter sales cannot oversell.

    items: [{"book_id": int, "quantity": int, "unit_price": int paise}, ...]
    """
    if not items:
        raise ValueError("A sale needs at least one line item.")
    if sale_type not in ("retail", "wholesale"):
        raise ValueError("Sale type must be retail or wholesale.")
    if sale_type == "wholesale" and customer_id is None:
        raise ValueError("Wholesale sales require a registered customer (FR-3.3).")
    if sale_type == "retail":
        customer_id = None
    if payment_method not in PAYMENT_METHODS:
        raise ValueError(f"Payment method must be one of {PAYMENT_METHODS}.")
    for item in items:
        if item["quantity"] <= 0:
            raise ValueError("Quantities must be positive.")
        if item["unit_price"] < 0:
            raise ValueError("Unit prices cannot be negative.")

    subtotal = sum(i["quantity"] * i["unit_price"] for i in items)
    if discount < 0 or discount > subtotal:
        raise ValueError("Discount must be between 0 and the bill subtotal.")
    total = subtotal - discount

    needed: dict[int, int] = defaultdict(int)
    for item in items:
        needed[item["book_id"]] += item["quantity"]

    conn = database.get_connection()
    try:
        with conn:
            # Stock re-check INSIDE the transaction (FR-5.5 / NFR-4).
            shortages = []
            for book_id, qty in needed.items():
                row = conn.execute(
                    "SELECT title_roman, title_devanagari, stock FROM v_current_stock"
                    " WHERE book_id = ?", (book_id,)).fetchone()
                if row is None:
                    raise ValueError(f"Book id {book_id} does not exist.")
                if row["stock"] < qty:
                    shortages.append(
                        f"{row['title_roman']} ({row['title_devanagari']}):"
                        f" requested {qty}, in stock {row['stock']}")
            if shortages:
                raise InsufficientStockError(
                    "Not enough stock — " + "; ".join(shortages))

            cur = conn.execute(
                "INSERT INTO sales (sale_date, sale_type, customer_id, discount, notes,"
                " total_amount, payment_method, created_by)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sale_date, sale_type, customer_id, discount, notes, total,
                 payment_method, user_id),
            )
            sale_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO sale_items (sale_id, book_id, quantity, unit_price)"
                " VALUES (?, ?, ?, ?)",
                [(sale_id, i["book_id"], i["quantity"], i["unit_price"]) for i in items],
            )
        return sale_id
    finally:
        conn.close()


def list_sales(start: str | None = None, end: str | None = None,
               sale_type: str | None = None, customer_id: int | None = None,
               book_id: int | None = None, user_id: int | None = None,
               include_cancelled: bool = True) -> list[dict]:
    """Sale headers with customer/user names, filterable (FR-5.7)."""
    conn = database.get_connection()
    try:
        where, params = [], []
        if start:
            where.append("s.sale_date >= ?")
            params.append(start)
        if end:
            where.append("s.sale_date <= ?")
            params.append(end)
        if sale_type:
            where.append("s.sale_type = ?")
            params.append(sale_type)
        if customer_id:
            where.append("s.customer_id = ?")
            params.append(customer_id)
        if user_id:
            where.append("s.created_by = ?")
            params.append(user_id)
        if book_id:
            where.append(
                "EXISTS (SELECT 1 FROM sale_items si"
                " WHERE si.sale_id = s.id AND si.book_id = ?)")
            params.append(book_id)
        if not include_cancelled:
            where.append("s.is_cancelled = 0")
        sql = (
            "SELECT s.*, c.name AS customer_name, u.full_name AS created_by_name,"
            " (SELECT COUNT(*) FROM sale_items si WHERE si.sale_id = s.id) AS line_count,"
            " (SELECT SUM(si.quantity) FROM sale_items si WHERE si.sale_id = s.id) AS total_qty"
            " FROM sales s"
            " LEFT JOIN wholesale_customers c ON c.id = s.customer_id"
            " JOIN users u ON u.id = s.created_by"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY s.sale_date DESC, s.id DESC"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_sale(sale_id: int) -> dict | None:
    sales = [s for s in list_sales() if s["id"] == sale_id]
    return sales[0] if sales else None


def get_sale_items(sale_id: int) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT si.*, b.code, b.title_devanagari, b.title_roman,"
            " si.quantity * si.unit_price AS line_total"
            " FROM sale_items si JOIN books b ON b.id = si.book_id"
            " WHERE si.sale_id = ? ORDER BY si.id",
            (sale_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def cancel_sale(sale_id: int, owner_id: int, reason: str) -> None:
    """Owner-only soft cancel (FR-5.8): stock restores via the derived views."""
    if not reason.strip():
        raise ValueError("A cancellation reason is required.")
    conn = database.get_connection()
    try:
        with conn:
            cur = conn.execute(
                "UPDATE sales SET is_cancelled = 1, cancelled_by = ?, cancel_reason = ?"
                " WHERE id = ? AND is_cancelled = 0",
                (owner_id, reason.strip(), sale_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Sale not found or already cancelled.")
    finally:
        conn.close()
