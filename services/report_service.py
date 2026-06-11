"""Reports: Sale–Purchase statement, P&L (last-purchase-price COGS), stock report
(FR-7). All amounts in integer paise; cancelled transactions always excluded."""

from __future__ import annotations

from db import database

COGS_METHOD = "Last purchase price per book (PRD §9.4)"


def sale_purchase_statement(start: str, end: str) -> dict:
    """Totals + day-wise and month-wise breakdown for a date range (FR-7.1)."""
    conn = database.get_connection()
    try:
        purchases = conn.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(q.qty), 0) AS qty,"
            " COALESCE(SUM(p.total_amount), 0) AS amount"
            " FROM purchases p"
            " JOIN (SELECT purchase_id, SUM(quantity) AS qty FROM purchase_items"
            "       GROUP BY purchase_id) q ON q.purchase_id = p.id"
            " WHERE p.is_cancelled = 0 AND p.purchase_date BETWEEN ? AND ?",
            (start, end)).fetchone()

        sales_by_type = {}
        for sale_type in ("retail", "wholesale"):
            row = conn.execute(
                "SELECT COUNT(*) AS cnt, COALESCE(SUM(q.qty), 0) AS qty,"
                " COALESCE(SUM(s.total_amount), 0) AS amount"
                " FROM sales s"
                " JOIN (SELECT sale_id, SUM(quantity) AS qty FROM sale_items"
                "       GROUP BY sale_id) q ON q.sale_id = s.id"
                " WHERE s.is_cancelled = 0 AND s.sale_type = ?"
                " AND s.sale_date BETWEEN ? AND ?",
                (sale_type, start, end)).fetchone()
            sales_by_type[sale_type] = dict(row)

        def _breakdown(bucket_expr_p: str, bucket_expr_s: str) -> list[dict]:
            rows = conn.execute(
                f"""
                SELECT bucket,
                       SUM(purchase_amount) AS purchase_amount,
                       SUM(retail_amount)   AS retail_amount,
                       SUM(wholesale_amount) AS wholesale_amount
                FROM (
                    SELECT {bucket_expr_p} AS bucket, total_amount AS purchase_amount,
                           0 AS retail_amount, 0 AS wholesale_amount
                    FROM purchases
                    WHERE is_cancelled = 0 AND purchase_date BETWEEN ? AND ?
                    UNION ALL
                    SELECT {bucket_expr_s}, 0,
                           CASE WHEN sale_type = 'retail' THEN total_amount ELSE 0 END,
                           CASE WHEN sale_type = 'wholesale' THEN total_amount ELSE 0 END
                    FROM sales
                    WHERE is_cancelled = 0 AND sale_date BETWEEN ? AND ?
                )
                GROUP BY bucket ORDER BY bucket
                """,
                (start, end, start, end)).fetchall()
            return [dict(r) for r in rows]

        daily = _breakdown("purchase_date", "sale_date")
        monthly = _breakdown("substr(purchase_date, 1, 7)", "substr(sale_date, 1, 7)")

        return {
            "purchases": dict(purchases),
            "sales": sales_by_type,
            "sales_total": {
                k: sales_by_type["retail"][k] + sales_by_type["wholesale"][k]
                for k in ("cnt", "qty", "amount")},
            "daily": daily,
            "monthly": monthly,
        }
    finally:
        conn.close()


def profit_and_loss(start: str, end: str) -> dict:
    """P&L with COGS at last purchase price per book (FR-7.2, TDD §5.4)."""
    conn = database.get_connection()
    try:
        lines = conn.execute(
            "SELECT si.book_id, b.code, b.title_roman, b.title_devanagari, s.sale_type,"
            " si.quantity, si.quantity * si.unit_price AS line_revenue,"
            " si.quantity * v.last_purchase_price AS line_cogs,"
            " v.last_purchase_price"
            " FROM sale_items si"
            " JOIN sales s ON s.id = si.sale_id"
            " JOIN books b ON b.id = si.book_id"
            " JOIN v_current_stock v ON v.book_id = si.book_id"
            " WHERE s.is_cancelled = 0 AND s.sale_date BETWEEN ? AND ?",
            (start, end)).fetchall()

        discounts = {}
        for sale_type in ("retail", "wholesale"):
            discounts[sale_type] = conn.execute(
                "SELECT COALESCE(SUM(discount), 0) FROM sales"
                " WHERE is_cancelled = 0 AND sale_type = ?"
                " AND sale_date BETWEEN ? AND ?",
                (sale_type, start, end)).fetchone()[0]

        by_type = {t: {"line_revenue": 0, "cogs": 0, "discount": discounts[t]}
                   for t in ("retail", "wholesale")}
        by_book: dict[int, dict] = {}
        never_purchased = set()
        for ln in lines:
            t = by_type[ln["sale_type"]]
            t["line_revenue"] += ln["line_revenue"]
            t["cogs"] += ln["line_cogs"]
            book = by_book.setdefault(ln["book_id"], {
                "code": ln["code"], "title_roman": ln["title_roman"],
                "title_devanagari": ln["title_devanagari"],
                "qty": 0, "revenue": 0, "cogs": 0})
            book["qty"] += ln["quantity"]
            book["revenue"] += ln["line_revenue"]
            book["cogs"] += ln["line_cogs"]
            if ln["last_purchase_price"] == 0:
                never_purchased.add(ln["code"])

        for t in by_type.values():
            t["revenue"] = t["line_revenue"] - t["discount"]
            t["profit"] = t["revenue"] - t["cogs"]

        revenue = sum(t["revenue"] for t in by_type.values())
        cogs = sum(t["cogs"] for t in by_type.values())
        profit = revenue - cogs

        top_books = sorted(
            ({**b, "profit": b["revenue"] - b["cogs"]} for b in by_book.values()),
            key=lambda b: b["profit"], reverse=True)

        return {
            "method": COGS_METHOD,
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": profit,
            "margin_pct": (profit / revenue * 100) if revenue else 0.0,
            "by_type": by_type,
            "top_books": top_books,
            "never_purchased_codes": sorted(never_purchased),
        }
    finally:
        conn.close()


def stock_report(include_inactive: bool = False) -> dict:
    """Current stock with valuation totals and low-stock list (FR-7.3)."""
    from services import inventory_service

    rows = inventory_service.current_stock(include_inactive=include_inactive)
    return {
        "rows": rows,
        "total_titles": len(rows),
        "total_units": sum(r["stock"] for r in rows),
        "total_value": sum(r["stock_value"] for r in rows),
        "low_stock": [r for r in rows if r["is_low"]],
    }
