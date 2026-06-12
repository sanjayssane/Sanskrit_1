"""Online orders: guest checkout, staff fulfillment via retail sale creation."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from db import database
from services.sale_service import InsufficientStockError


def _check_stock(conn, items: list[dict]) -> None:
    """Re-check stock inside a transaction (same rules as sale_service)."""
    needed: dict[int, int] = defaultdict(int)
    for item in items:
        needed[item["book_id"]] += item["quantity"]
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
        raise InsufficientStockError("Not enough stock — " + "; ".join(shortages))


def create_order(order_date: str, customer_name: str, customer_phone: str,
                 items: list[dict], customer_email: str | None = None,
                 notes: str | None = None) -> int:
    """Place a pending online order. Stock is checked but not reserved.

    items: [{"book_id": int, "quantity": int, "unit_price": int paise}, ...]
    """
    name = customer_name.strip()
    phone = customer_phone.strip()
    if not name:
        raise ValueError("Customer name is required.")
    if not phone:
        raise ValueError("Phone number is required.")
    if not items:
        raise ValueError("An order needs at least one line item.")
    for item in items:
        if item["quantity"] <= 0:
            raise ValueError("Quantities must be positive.")
        if item["unit_price"] < 0:
            raise ValueError("Unit prices cannot be negative.")

    total = sum(i["quantity"] * i["unit_price"] for i in items)
    email = customer_email.strip() if customer_email else None
    order_notes = notes.strip() if notes else None

    conn = database.get_connection()
    try:
        with conn:
            _check_stock(conn, items)
            cur = conn.execute(
                "INSERT INTO online_orders"
                " (order_date, customer_name, customer_phone, customer_email,"
                " notes, total_amount, status)"
                " VALUES (?, ?, ?, ?, ?, ?, 'pending')",
                (order_date, name, phone, email, order_notes, total),
            )
            order_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO online_order_items (order_id, book_id, quantity, unit_price)"
                " VALUES (?, ?, ?, ?)",
                [(order_id, i["book_id"], i["quantity"], i["unit_price"]) for i in items],
            )
        return order_id
    finally:
        conn.close()


def list_orders(start: str | None = None, end: str | None = None,
                status: str | None = None) -> list[dict]:
    conn = database.get_connection()
    try:
        where, params = [], []
        if start:
            where.append("o.order_date >= ?")
            params.append(start)
        if end:
            where.append("o.order_date <= ?")
            params.append(end)
        if status:
            where.append("o.status = ?")
            params.append(status)
        sql = (
            "SELECT o.*,"
            " cu.full_name AS completed_by_name,"
            " ca.full_name AS cancelled_by_name,"
            " (SELECT COUNT(*) FROM online_order_items oi WHERE oi.order_id = o.id)"
            "   AS line_count,"
            " (SELECT SUM(oi.quantity) FROM online_order_items oi WHERE oi.order_id = o.id)"
            "   AS total_qty"
            " FROM online_orders o"
            " LEFT JOIN users cu ON cu.id = o.completed_by"
            " LEFT JOIN users ca ON ca.id = o.cancelled_by"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY o.order_date DESC, o.id DESC"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_order(order_id: int) -> dict | None:
    orders = [o for o in list_orders() if o["id"] == order_id]
    return orders[0] if orders else None


def get_order_items(order_id: int) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT oi.*, b.code, b.title_devanagari, b.title_roman,"
            " oi.quantity * oi.unit_price AS line_total"
            " FROM online_order_items oi JOIN books b ON b.id = oi.book_id"
            " WHERE oi.order_id = ? ORDER BY oi.id",
            (order_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def pending_count() -> int:
    conn = database.get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM online_orders WHERE status = 'pending'"
        ).fetchone()[0]
    finally:
        conn.close()


def complete_order(order_id: int, user_id: int) -> int:
    """Fulfill a pending order: create retail sale and mark completed."""
    conn = database.get_connection()
    try:
        with conn:
            order = conn.execute(
                "SELECT * FROM online_orders WHERE id = ?", (order_id,)
            ).fetchone()
            if order is None:
                raise ValueError("Order not found.")
            if order["status"] != "pending":
                raise ValueError("Only pending orders can be completed.")

            items = [dict(r) for r in conn.execute(
                "SELECT book_id, quantity, unit_price FROM online_order_items"
                " WHERE order_id = ? ORDER BY id",
                (order_id,),
            ).fetchall()]
            if not items:
                raise ValueError("Order has no line items.")

            _check_stock(conn, items)

            sale_notes = f"Online order #{order_id} — pay on pickup"
            if order["notes"]:
                sale_notes += f"\n{order['notes']}"

            cur = conn.execute(
                "INSERT INTO sales (sale_date, sale_type, customer_id, discount, notes,"
                " total_amount, payment_method, created_by)"
                " VALUES (?, 'retail', NULL, 0, ?, ?, 'cash', ?)",
                (order["order_date"], sale_notes, order["total_amount"], user_id),
            )
            sale_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO sale_items (sale_id, book_id, quantity, unit_price)"
                " VALUES (?, ?, ?, ?)",
                [(sale_id, i["book_id"], i["quantity"], i["unit_price"]) for i in items],
            )

            now = dt.datetime.now().isoformat(timespec="seconds")
            cur = conn.execute(
                "UPDATE online_orders SET status = 'completed', sale_id = ?,"
                " completed_by = ?, completed_at = ?"
                " WHERE id = ? AND status = 'pending'",
                (sale_id, user_id, now, order_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Order was already processed.")
        return sale_id
    finally:
        conn.close()


def cancel_order(order_id: int, user_id: int, reason: str) -> None:
    """Cancel a pending order without affecting stock."""
    if not reason.strip():
        raise ValueError("A cancellation reason is required.")
    conn = database.get_connection()
    try:
        with conn:
            now = dt.datetime.now().isoformat(timespec="seconds")
            cur = conn.execute(
                "UPDATE online_orders SET status = 'cancelled',"
                " cancelled_by = ?, cancelled_at = ?, cancel_reason = ?"
                " WHERE id = ? AND status = 'pending'",
                (user_id, now, reason.strip(), order_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Order not found or not pending.")
    finally:
        conn.close()
