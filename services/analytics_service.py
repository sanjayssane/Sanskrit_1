"""Advanced analytics: read-only aggregations (ADVANCED_ANALYTICS_REQUIREMENTS.md).

All amounts are integer paise. Cancelled transactions excluded by default.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from db import database
from services.report_service import COGS_METHOD

COGS_METHOD_WEIGHTED = "Weighted average purchase price per book"

DEFAULT_SETTINGS: dict[str, str] = {
    "fiscal_year_start_month": "4",
    "dead_stock_days": "180",
    "slow_mover_days": "90",
    "days_of_supply_threshold": "14",
    "dead_stock_capital_alert_paise": "5000000",
    "margin_drop_alert_points": "5",
    "cogs_method": "last_purchase",
}

PERIOD_PRESETS = (
    "Today",
    "Yesterday",
    "Last 7 days",
    "Last 30 days",
    "This month",
    "Last month",
    "This quarter",
    "This year",
    "Custom range",
)

GRANULARITIES = ("daily", "weekly", "monthly")


@dataclass
class AnalyticsFilters:
    include_cancelled: bool = False
    include_inactive_books: bool = False
    sale_type: str | None = None
    book_id: int | None = None
    category: str | None = None
    publisher: str | None = None
    language: str | None = None
    supplier_id: int | None = None
    customer_id: int | None = None
    payment_method: str | None = None
    created_by: int | None = None


# --- Settings -----------------------------------------------------------------

def get_settings() -> dict[str, str]:
    conn = database.get_connection()
    try:
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        out = dict(DEFAULT_SETTINGS)
        out.update({r["key"]: r["value"] for r in rows})
        return out
    except Exception:
        return dict(DEFAULT_SETTINGS)
    finally:
        conn.close()


def set_setting(key: str, value: str) -> None:
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
    finally:
        conn.close()


def get_setting(key: str, default: str | None = None) -> str:
    settings = get_settings()
    return settings.get(key, default if default is not None else DEFAULT_SETTINGS.get(key, ""))


def cogs_method_label(method: str | None = None) -> str:
    m = method or get_setting("cogs_method", "last_purchase")
    return COGS_METHOD_WEIGHTED if m == "weighted_average" else COGS_METHOD


# --- Date helpers -------------------------------------------------------------

def period_range(
    preset: str,
    custom_start: dt.date | None = None,
    custom_end: dt.date | None = None,
) -> tuple[str, str]:
    today = dt.date.today()
    if preset == "Custom range":
        if custom_start is None or custom_end is None:
            start = today.replace(day=1)
            end = today
        else:
            start, end = custom_start, custom_end
    elif preset == "Today":
        start = end = today
    elif preset == "Yesterday":
        start = end = today - dt.timedelta(days=1)
    elif preset == "Last 7 days":
        end = today
        start = today - dt.timedelta(days=6)
    elif preset == "Last 30 days":
        end = today
        start = today - dt.timedelta(days=29)
    elif preset == "This month":
        start = today.replace(day=1)
        end = today
    elif preset == "Last month":
        first_this = today.replace(day=1)
        end = first_this - dt.timedelta(days=1)
        start = end.replace(day=1)
    elif preset == "This quarter":
        q = (today.month - 1) // 3
        start = dt.date(today.year, q * 3 + 1, 1)
        end = today
    elif preset == "This year":
        start = dt.date(today.year, 1, 1)
        end = today
    else:
        end = today
        start = today - dt.timedelta(days=29)
    if start > end:
        start, end = end, start
    return start.isoformat(), end.isoformat()


def previous_period(start: str, end: str) -> tuple[str, str]:
    d0 = dt.date.fromisoformat(start)
    d1 = dt.date.fromisoformat(end)
    length = (d1 - d0).days + 1
    prev_end = d0 - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=length - 1)
    return prev_start.isoformat(), prev_end.isoformat()


def _bucket_expr(date_col: str, granularity: str) -> str:
    if granularity == "weekly":
        return f"strftime('%Y-W%W', {date_col})"
    if granularity == "monthly":
        return f"substr({date_col}, 1, 7)"
    return date_col


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None if current == 0 else 100.0
    return (current - previous) / previous * 100.0


# --- SQL filter builders ------------------------------------------------------

def _cancel_clause(alias: str, include_cancelled: bool) -> str:
    return "" if include_cancelled else f" AND {alias}.is_cancelled = 0"


def _book_active_clause(alias: str, include_inactive: bool) -> str:
    return "" if include_inactive else f" AND {alias}.is_active = 1"


def _sales_filters(filters: AnalyticsFilters, s: str = "s", b: str = "b") -> tuple[str, list]:
    parts: list[str] = []
    params: list[Any] = []
    parts.append(_cancel_clause(s, filters.include_cancelled).lstrip(" AND "))
    if not filters.include_inactive_books:
        parts.append(f"{b}.is_active = 1")
    if filters.sale_type:
        parts.append(f"{s}.sale_type = ?")
        params.append(filters.sale_type)
    if filters.book_id:
        parts.append(f"{b}.id = ?")
        params.append(filters.book_id)
    if filters.category:
        parts.append(f"COALESCE({b}.category, '(Uncategorized)') = ?")
        params.append(filters.category)
    if filters.publisher:
        parts.append(f"COALESCE({b}.publisher, '(Unknown publisher)') = ?")
        params.append(filters.publisher)
    if filters.language:
        parts.append(f"COALESCE({b}.language, '(Unknown)') = ?")
        params.append(filters.language)
    if filters.customer_id:
        parts.append(f"{s}.customer_id = ?")
        params.append(filters.customer_id)
    if filters.payment_method:
        parts.append(f"{s}.payment_method = ?")
        params.append(filters.payment_method)
    if filters.created_by:
        parts.append(f"{s}.created_by = ?")
        params.append(filters.created_by)
    clause = " AND ".join(p for p in parts if p)
    return (f" AND {clause}" if clause else ""), params


def _purchase_filters(filters: AnalyticsFilters, p: str = "p", b: str = "b") -> tuple[str, list]:
    parts: list[str] = []
    params: list[Any] = []
    parts.append(_cancel_clause(p, filters.include_cancelled).lstrip(" AND "))
    if filters.supplier_id:
        parts.append(f"{p}.supplier_id = ?")
        params.append(filters.supplier_id)
    if filters.book_id:
        parts.append(f"{b}.id = ?")
        params.append(filters.book_id)
    if filters.category:
        parts.append(f"COALESCE({b}.category, '(Uncategorized)') = ?")
        params.append(filters.category)
    if filters.publisher:
        parts.append(f"COALESCE({b}.publisher, '(Unknown publisher)') = ?")
        params.append(filters.publisher)
    if filters.created_by:
        parts.append(f"{p}.created_by = ?")
        params.append(filters.created_by)
    if not filters.include_inactive_books:
        parts.append(f"{b}.is_active = 1")
    clause = " AND ".join(p for p in parts if p)
    return (f" AND {clause}" if clause else ""), params


# --- Sales analytics ----------------------------------------------------------

def sales_summary(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS txn_count,
                   COALESCE(SUM(total_amount), 0) AS revenue
            FROM (
                SELECT DISTINCT s.id, s.total_amount
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                JOIN books b ON b.id = si.book_id
                WHERE s.sale_date BETWEEN ? AND ?{sf}
            )
            """,
            (start, end, *sp),
        ).fetchone()
        units_row = conn.execute(
            f"""
            SELECT COALESCE(SUM(si.quantity), 0) AS units,
                   COALESCE(SUM(si.quantity * si.unit_price), 0) AS gross_revenue
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            """,
            (start, end, *sp),
        ).fetchone()
        txn = row["txn_count"] or 0
        revenue = row["revenue"] or 0
        units = units_row["units"] or 0
        return {
            "txn_count": txn,
            "revenue": revenue,
            "units": units,
            "gross_revenue": units_row["gross_revenue"] or 0,
            "avg_ticket": revenue // txn if txn else 0,
            "avg_units_per_txn": units / txn if txn else 0.0,
        }
    finally:
        conn.close()


def sales_trend(
    start: str,
    end: str,
    granularity: str = "daily",
    filters: AnalyticsFilters | None = None,
) -> list[dict]:
    if granularity not in GRANULARITIES:
        granularity = "daily"
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        bucket = _bucket_expr("s.sale_date", granularity)
        rev_rows = conn.execute(
            f"""
            SELECT bucket,
                   COALESCE(SUM(total_amount), 0) AS revenue,
                   COUNT(*) AS txn_count
            FROM (
                SELECT DISTINCT s.id, {bucket} AS bucket, s.total_amount
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                JOIN books b ON b.id = si.book_id
                WHERE s.sale_date BETWEEN ? AND ?{sf}
            )
            GROUP BY bucket
            ORDER BY bucket
            """,
            (start, end, *sp),
        ).fetchall()
        unit_rows = conn.execute(
            f"""
            SELECT {_bucket_expr('s.sale_date', granularity)} AS bucket,
                   COALESCE(SUM(si.quantity), 0) AS units
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            GROUP BY bucket
            ORDER BY bucket
            """,
            (start, end, *sp),
        ).fetchall()
        units_map = {r["bucket"]: r["units"] for r in unit_rows}
        return [{
            "bucket": r["bucket"],
            "revenue": r["revenue"],
            "units": units_map.get(r["bucket"], 0),
            "txn_count": r["txn_count"],
        } for r in rev_rows]
    finally:
        conn.close()


def sales_by_type(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    f = filters or AnalyticsFilters()
    out: dict[str, dict] = {}
    for stype in ("retail", "wholesale"):
        if f.sale_type and f.sale_type != stype:
            out[stype] = {"revenue": 0, "units": 0, "txn_count": 0, "avg_ticket": 0}
            continue
        typed = AnalyticsFilters(
            include_cancelled=f.include_cancelled,
            include_inactive_books=f.include_inactive_books,
            sale_type=stype,
            book_id=f.book_id,
            category=f.category,
            publisher=f.publisher,
            language=f.language,
            customer_id=f.customer_id,
            payment_method=f.payment_method,
            created_by=f.created_by,
        )
        summary = sales_summary(start, end, typed)
        out[stype] = {
            "revenue": summary["revenue"],
            "units": summary["units"],
            "txn_count": summary["txn_count"],
            "avg_ticket": summary["avg_ticket"],
        }
    return out


def bestsellers(
    start: str,
    end: str,
    limit: int = 50,
    filters: AnalyticsFilters | None = None,
    sort_by: str = "qty",
) -> list[dict]:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        order = "qty DESC" if sort_by == "qty" else "line_revenue DESC"
        rows = conn.execute(
            f"""
            SELECT b.id AS book_id, b.code, b.title_roman, b.title_devanagari,
                   COALESCE(b.category, '(Uncategorized)') AS category,
                   SUM(si.quantity) AS qty,
                   SUM(si.quantity * si.unit_price) AS line_revenue
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            GROUP BY b.id
            ORDER BY {order}
            LIMIT ?
            """,
            (start, end, *sp, limit),
        ).fetchall()
        total_rev = sum(r["line_revenue"] for r in rows)
        return [{
            "book_id": r["book_id"],
            "code": r["code"],
            "title_roman": r["title_roman"],
            "title_devanagari": r["title_devanagari"],
            "category": r["category"],
            "qty": r["qty"],
            "line_revenue": r["line_revenue"],
            "pct_of_revenue": (r["line_revenue"] / total_rev * 100) if total_rev else 0.0,
        } for r in rows]
    finally:
        conn.close()


def slow_movers(days: int | None = None, filters: AnalyticsFilters | None = None) -> list[dict]:
    settings = get_settings()
    n = days if days is not None else int(settings.get("slow_mover_days", "90"))
    cutoff = (dt.date.today() - dt.timedelta(days=n)).isoformat()
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        rows = conn.execute(
            f"""
            SELECT v.book_id, v.code, v.title_roman, v.title_devanagari,
                   v.stock, v.category, v.last_purchase_price
            FROM v_current_stock v
            WHERE v.stock > 0 AND v.is_active = 1
              AND v.book_id NOT IN (
                  SELECT DISTINCT si.book_id
                  FROM sale_items si
                  JOIN sales s ON s.id = si.sale_id
                  JOIN books b ON b.id = si.book_id
                  WHERE s.sale_date >= ?{sf}
              )
            ORDER BY v.stock DESC
            """,
            (cutoff, *sp),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def discount_analysis(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        row = conn.execute(
            f"""
            SELECT COALESCE(SUM(s.discount), 0) AS total_discount,
                   COALESCE(SUM(si.quantity * si.unit_price), 0) AS gross_revenue
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            """,
            (start, end, *sp),
        ).fetchone()
        total_discount = row["total_discount"] or 0
        gross = row["gross_revenue"] or 0
        top = conn.execute(
            f"""
            SELECT s.id, s.sale_date, s.sale_type, s.discount, s.total_amount,
                   COALESCE(wc.name, '(walk-in)') AS customer_name
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN books b ON b.id = si.book_id
            LEFT JOIN wholesale_customers wc ON wc.id = s.customer_id
            WHERE s.sale_date BETWEEN ? AND ? AND s.discount > 0{sf}
            GROUP BY s.id
            ORDER BY s.discount DESC
            LIMIT 10
            """,
            (start, end, *sp),
        ).fetchall()
        return {
            "total_discount": total_discount,
            "gross_revenue": gross,
            "discount_pct": (total_discount / gross * 100) if gross else 0.0,
            "top_sales": [dict(r) for r in top],
        }
    finally:
        conn.close()


def payment_method_breakdown(start: str, end: str, filters: AnalyticsFilters | None = None) -> list[dict]:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        rows = conn.execute(
            f"""
            SELECT s.payment_method,
                   COUNT(DISTINCT s.id) AS txn_count,
                   COALESCE(SUM(s.total_amount), 0) AS revenue
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            GROUP BY s.payment_method
            ORDER BY revenue DESC
            """,
            (start, end, *sp),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def sales_by_weekday(start: str, end: str, filters: AnalyticsFilters | None = None) -> list[dict]:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        rows = conn.execute(
            f"""
            SELECT CAST(strftime('%w', s.sale_date) AS INTEGER) AS dow,
                   COUNT(DISTINCT s.sale_date) AS day_count,
                   COALESCE(SUM(s.total_amount), 0) AS revenue,
                   COUNT(DISTINCT s.id) AS txn_count
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            GROUP BY dow
            ORDER BY dow
            """,
            (start, end, *sp),
        ).fetchall()
        names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        return [{
            "weekday": names[r["dow"]],
            "dow": r["dow"],
            "revenue": r["revenue"],
            "txn_count": r["txn_count"],
            "avg_daily_revenue": r["revenue"] // r["day_count"] if r["day_count"] else 0,
        } for r in rows]
    finally:
        conn.close()


def sales_by_hour(start: str, end: str, filters: AnalyticsFilters | None = None) -> list[dict]:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        rows = conn.execute(
            f"""
            SELECT CAST(strftime('%H', s.created_at) AS INTEGER) AS hour,
                   COUNT(DISTINCT s.id) AS txn_count,
                   COALESCE(SUM(s.total_amount), 0) AS revenue
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            GROUP BY hour
            ORDER BY hour
            """,
            (start, end, *sp),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def price_override_analysis(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        rows = conn.execute(
            f"""
            SELECT si.quantity, si.unit_price,
                   CASE WHEN s.sale_type = 'retail' THEN b.retail_price
                        ELSE b.wholesale_price END AS catalog_price
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            """,
            (start, end, *sp),
        ).fetchall()
        overrides = [r for r in rows if r["unit_price"] != r["catalog_price"]]
        total_delta = sum((r["unit_price"] - r["catalog_price"]) * r["quantity"] for r in overrides)
        total_qty = sum(r["quantity"] for r in overrides)
        return {
            "override_line_count": len(overrides),
            "override_units": total_qty,
            "avg_delta_per_unit": total_delta // total_qty if total_qty else 0,
            "total_delta": total_delta,
        }
    finally:
        conn.close()


def dimension_performance(
    start: str,
    end: str,
    dimension: str,
    filters: AnalyticsFilters | None = None,
) -> list[dict]:
    col = {"category": "b.category", "publisher": "b.publisher"}.get(dimension)
    if not col:
        return []
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        label = f"COALESCE({col}, '(Unknown)')"
        rows = conn.execute(
            f"""
            SELECT {label} AS label,
                   SUM(si.quantity) AS qty,
                   SUM(si.quantity * si.unit_price) AS revenue
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            GROUP BY label
            ORDER BY revenue DESC
            """,
            (start, end, *sp),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --- Purchase analytics -------------------------------------------------------

def purchase_summary(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        pf, pp = _purchase_filters(f)
        row = conn.execute(
            f"""
            SELECT COUNT(DISTINCT p.id) AS txn_count,
                   COALESCE(SUM(p.total_amount), 0) AS spend,
                   COALESCE(SUM(pi.quantity), 0) AS units
            FROM purchases p
            JOIN purchase_items pi ON pi.purchase_id = p.id
            JOIN books b ON b.id = pi.book_id
            WHERE p.purchase_date BETWEEN ? AND ?{pf}
            """,
            (start, end, *pp),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def purchase_trend(
    start: str,
    end: str,
    granularity: str = "daily",
    filters: AnalyticsFilters | None = None,
) -> list[dict]:
    if granularity not in GRANULARITIES:
        granularity = "daily"
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        pf, pp = _purchase_filters(f)
        bucket = _bucket_expr("p.purchase_date", granularity)
        rows = conn.execute(
            f"""
            SELECT {bucket} AS bucket,
                   COALESCE(SUM(p.total_amount), 0) AS spend,
                   COALESCE(SUM(pi.quantity), 0) AS units,
                   COUNT(DISTINCT p.id) AS txn_count
            FROM purchases p
            JOIN purchase_items pi ON pi.purchase_id = p.id
            JOIN books b ON b.id = pi.book_id
            WHERE p.purchase_date BETWEEN ? AND ?{pf}
            GROUP BY {bucket}
            ORDER BY bucket
            """,
            (start, end, *pp),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def supplier_ranking(start: str, end: str, filters: AnalyticsFilters | None = None) -> list[dict]:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        pf, pp = _purchase_filters(f)
        rows = conn.execute(
            f"""
            SELECT sup.id AS supplier_id, sup.name AS supplier_name,
                   COUNT(DISTINCT p.id) AS purchase_count,
                   COALESCE(SUM(pi.quantity), 0) AS total_qty,
                   COALESCE(SUM(pi.quantity * pi.unit_price), 0) AS total_spend,
                   MAX(p.purchase_date) AS last_purchase_date
            FROM purchases p
            JOIN purchase_items pi ON pi.purchase_id = p.id
            JOIN books b ON b.id = pi.book_id
            JOIN suppliers sup ON sup.id = p.supplier_id
            WHERE p.purchase_date BETWEEN ? AND ?{pf}
            GROUP BY sup.id
            ORDER BY total_spend DESC
            """,
            (start, end, *pp),
        ).fetchall()
        out = []
        for r in rows:
            avg_cost = r["total_spend"] // r["total_qty"] if r["total_qty"] else 0
            out.append({**dict(r), "avg_unit_cost": avg_cost})
        return out
    finally:
        conn.close()


def supplier_concentration(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    ranking = supplier_ranking(start, end, filters)
    total = sum(r["total_spend"] for r in ranking)
    top3 = sum(r["total_spend"] for r in ranking[:3])
    return {
        "total_spend": total,
        "top3_spend": top3,
        "top3_pct": (top3 / total * 100) if total else 0.0,
    }


def top_purchased_titles(
    start: str,
    end: str,
    limit: int = 20,
    filters: AnalyticsFilters | None = None,
) -> list[dict]:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        pf, pp = _purchase_filters(f)
        rows = conn.execute(
            f"""
            SELECT b.id AS book_id, b.code, b.title_roman, b.title_devanagari,
                   SUM(pi.quantity) AS qty,
                   SUM(pi.quantity * pi.unit_price) AS spend
            FROM purchase_items pi
            JOIN purchases p ON p.id = pi.purchase_id
            JOIN books b ON b.id = pi.book_id
            WHERE p.purchase_date BETWEEN ? AND ?{pf}
            GROUP BY b.id
            ORDER BY qty DESC
            LIMIT ?
            """,
            (start, end, *pp, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def purchase_price_trend(book_id: int) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.purchase_date AS bucket, pi.unit_price, pi.quantity
            FROM purchase_items pi
            JOIN purchases p ON p.id = pi.purchase_id
            WHERE pi.book_id = ? AND p.is_cancelled = 0
            ORDER BY p.purchase_date, pi.id
            """,
            (book_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --- Inventory analytics ------------------------------------------------------

def _stock_at_date(conn, as_of: str) -> dict[int, int]:
    """Per-book stock on as_of (inclusive) from ledger movements."""
    rows = conn.execute(
        """
        SELECT book_id, SUM(quantity_delta) AS stock
        FROM v_stock_ledger
        WHERE movement_date <= ?
        GROUP BY book_id
        """,
        (as_of,),
    ).fetchall()
    return {r["book_id"]: r["stock"] for r in rows}


def inventory_valuation(include_inactive: bool = False) -> dict:
    from services import inventory_service

    rows = inventory_service.current_stock(include_inactive=include_inactive)
    return {
        "total_titles": len(rows),
        "total_units": sum(r["stock"] for r in rows),
        "total_value": sum(r["stock_value"] for r in rows),
        "rows": rows,
    }


def stock_movement_summary(start: str, end: str) -> dict:
    conn = database.get_connection()
    try:
        purchased = conn.execute(
            """
            SELECT COALESCE(SUM(pi.quantity), 0) AS units
            FROM purchase_items pi
            JOIN purchases p ON p.id = pi.purchase_id
            WHERE p.is_cancelled = 0 AND p.purchase_date BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()[0]
        sold = conn.execute(
            """
            SELECT COALESCE(SUM(si.quantity), 0) AS units
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE s.is_cancelled = 0 AND s.sale_date BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()[0]
        adj = conn.execute(
            """
            SELECT COALESCE(SUM(quantity_delta), 0) AS units
            FROM stock_adjustments
            WHERE adjustment_date BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()[0]
        return {
            "units_in": purchased,
            "units_out": sold,
            "net_adjustments": adj,
            "net_change": purchased - sold + adj,
        }
    finally:
        conn.close()


def inventory_turnover(start: str, end: str, cogs_method: str | None = None) -> dict:
    pnl = profit_and_loss(start, end, cogs_method=cogs_method)
    conn = database.get_connection()
    try:
        stock_end = conn.execute(
            "SELECT COALESCE(SUM(stock * last_purchase_price), 0) FROM v_current_stock WHERE is_active = 1"
        ).fetchone()[0]
        stock_start_map = _stock_at_date(conn, start)
        prices = {r["book_id"]: r["last_purchase_price"]
                  for r in conn.execute(
                      "SELECT book_id, last_purchase_price FROM v_current_stock").fetchall()}
        stock_start = sum(
            max(0, stock_start_map.get(bid, 0)) * prices.get(bid, 0) for bid in prices)
        avg_inv = (stock_start + stock_end) / 2
        cogs = pnl["cogs"]
        ratio = cogs / avg_inv if avg_inv else None
        return {
            "cogs": cogs,
            "opening_value": stock_start,
            "closing_value": stock_end,
            "average_inventory_value": int(avg_inv),
            "turnover_ratio": ratio,
            "method": cogs_method_label(cogs_method),
        }
    finally:
        conn.close()


def days_of_supply(threshold_days: int | None = None) -> list[dict]:
    settings = get_settings()
    thresh = threshold_days if threshold_days is not None else int(
        settings.get("days_of_supply_threshold", "14"))
    since = (dt.date.today() - dt.timedelta(days=29)).isoformat()
    today = dt.date.today().isoformat()
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT v.book_id, v.code, v.title_roman, v.title_devanagari,
                   v.stock, v.category,
                   COALESCE(s.qty_30d, 0) AS sold_30d
            FROM v_current_stock v
            LEFT JOIN (
                SELECT si.book_id, SUM(si.quantity) AS qty_30d
                FROM sale_items si
                JOIN sales sa ON sa.id = si.sale_id
                WHERE sa.is_cancelled = 0 AND sa.sale_date BETWEEN ? AND ?
                GROUP BY si.book_id
            ) s ON s.book_id = v.book_id
            WHERE v.is_active = 1 AND v.stock > 0
            ORDER BY v.stock
            """,
            (since, today),
        ).fetchall()
        out = []
        for r in rows:
            daily = r["sold_30d"] / 30.0 if r["sold_30d"] else 0.0
            dos = r["stock"] / daily if daily > 0 else None
            out.append({
                **dict(r),
                "avg_daily_sales": daily,
                "days_of_supply": dos,
                "below_threshold": dos is not None and dos < thresh,
            })
        return out
    finally:
        conn.close()


def dead_stock(days: int | None = None, filters: AnalyticsFilters | None = None) -> list[dict]:
    settings = get_settings()
    n = days if days is not None else int(settings.get("dead_stock_days", "180"))
    movers = slow_movers(n, filters)
    for m in movers:
        m["tied_up_capital"] = m["stock"] * m["last_purchase_price"]
    return movers


def out_of_stock_with_recent_sales(start: str, end: str) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT b.id AS book_id, b.code, b.title_roman, b.title_devanagari,
                   SUM(si.quantity) AS sold_in_period
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            JOIN v_current_stock v ON v.book_id = b.id
            WHERE s.is_cancelled = 0 AND s.sale_date BETWEEN ? AND ?
              AND v.stock = 0
            GROUP BY b.id
            ORDER BY sold_in_period DESC
            """,
            (start, end),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def abc_classification(months: int = 12) -> list[dict]:
    end = dt.date.today().isoformat()
    start = (dt.date.today() - dt.timedelta(days=months * 30)).isoformat()
    books = bestsellers(start, end, limit=10_000)
    total = sum(b["line_revenue"] for b in books)
    if not total:
        return []
    cumulative = 0.0
    out = []
    for b in books:
        cumulative += b["line_revenue"]
        pct = cumulative / total * 100
        cls = "A" if pct <= 80 else ("B" if pct <= 95 else "C")
        out.append({**b, "abc_class": cls, "cumulative_pct": pct})
    return out


def reorder_suggestions() -> list[dict]:
    dos_rows = days_of_supply()
    conn = database.get_connection()
    try:
        suggestions = []
        for r in conn.execute(
            "SELECT book_id, code, title_roman, title_devanagari, stock,"
            " low_stock_threshold FROM v_current_stock WHERE is_active = 1"
        ).fetchall():
            dos = next((d for d in dos_rows if d["book_id"] == r["book_id"]), None)
            sold_30 = int(dos["sold_30d"]) if dos else 0
            target = max(r["low_stock_threshold"], sold_30)
            need = target - r["stock"]
            low = r["stock"] <= r["low_stock_threshold"]
            dos_low = dos and dos.get("below_threshold")
            if (low or dos_low) and need > 0:
                suggestions.append({
                    "book_id": r["book_id"],
                    "code": r["code"],
                    "title_roman": r["title_roman"],
                    "title_devanagari": r["title_devanagari"],
                    "stock": r["stock"],
                    "threshold": r["low_stock_threshold"],
                    "suggested_qty": need,
                })
        return suggestions
    finally:
        conn.close()


def adjustment_analytics(start: str, end: str) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT reason, COUNT(*) AS cnt, SUM(quantity_delta) AS net_qty
            FROM stock_adjustments
            WHERE adjustment_date BETWEEN ? AND ?
            GROUP BY reason
            ORDER BY cnt DESC
            """,
            (start, end),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --- Profitability ------------------------------------------------------------

def _weighted_avg_cost(conn, book_id: int) -> int:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(pi.quantity * pi.unit_price), 0) AS cost,
               COALESCE(SUM(pi.quantity), 0) AS qty
        FROM purchase_items pi
        JOIN purchases p ON p.id = pi.purchase_id
        WHERE pi.book_id = ? AND p.is_cancelled = 0
        """,
        (book_id,),
    ).fetchone()
    if not row["qty"]:
        return 0
    return row["cost"] // row["qty"]


def profit_and_loss(
    start: str,
    end: str,
    cogs_method: str | None = None,
    filters: AnalyticsFilters | None = None,
) -> dict:
    method = cogs_method or get_setting("cogs_method", "last_purchase")
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        lines = conn.execute(
            f"""
            SELECT si.book_id, b.code, b.title_roman, b.title_devanagari,
                   b.category, b.publisher, s.sale_type,
                   si.quantity, si.quantity * si.unit_price AS line_revenue,
                   v.last_purchase_price
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            JOIN v_current_stock v ON v.book_id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            """,
            (start, end, *sp),
        ).fetchall()

        discounts: dict[str, int] = {}
        for stype in ("retail", "wholesale"):
            if f.sale_type and f.sale_type != stype:
                discounts[stype] = 0
                continue
            typed = AnalyticsFilters(
                include_cancelled=f.include_cancelled,
                include_inactive_books=f.include_inactive_books,
                sale_type=stype,
                book_id=f.book_id,
                category=f.category,
                publisher=f.publisher,
                language=f.language,
                customer_id=f.customer_id,
                payment_method=f.payment_method,
                created_by=f.created_by,
            )
            dsf, dsp = _sales_filters(typed)
            drows = conn.execute(
                f"""
                SELECT s.id, s.discount
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                JOIN books b ON b.id = si.book_id
                WHERE s.sale_date BETWEEN ? AND ?{dsf}
                GROUP BY s.id
                """,
                (start, end, *dsp),
            ).fetchall()
            discounts[stype] = sum(r["discount"] for r in drows)

        by_type = {t: {"line_revenue": 0, "cogs": 0, "discount": discounts[t]}
                   for t in ("retail", "wholesale")}
        by_book: dict[int, dict] = {}
        never_purchased = set()

        for ln in lines:
            if method == "weighted_average":
                unit_cogs = _weighted_avg_cost(conn, ln["book_id"])
            else:
                unit_cogs = ln["last_purchase_price"]
            line_cogs = ln["quantity"] * unit_cogs
            if unit_cogs == 0:
                never_purchased.add(ln["code"])

            t = by_type[ln["sale_type"]]
            t["line_revenue"] += ln["line_revenue"]
            t["cogs"] += line_cogs

            book = by_book.setdefault(ln["book_id"], {
                "book_id": ln["book_id"],
                "code": ln["code"],
                "title_roman": ln["title_roman"],
                "title_devanagari": ln["title_devanagari"],
                "category": ln["category"] or "(Uncategorized)",
                "publisher": ln["publisher"] or "(Unknown publisher)",
                "qty": 0, "revenue": 0, "cogs": 0,
            })
            book["qty"] += ln["quantity"]
            book["revenue"] += ln["line_revenue"]
            book["cogs"] += line_cogs

        for t in by_type.values():
            t["revenue"] = t["line_revenue"] - t["discount"]
            t["profit"] = t["revenue"] - t["cogs"]
            t["margin_pct"] = (t["profit"] / t["revenue"] * 100) if t["revenue"] else 0.0

        revenue = sum(t["revenue"] for t in by_type.values())
        cogs = sum(t["cogs"] for t in by_type.values())
        profit = revenue - cogs

        book_list = []
        for b in by_book.values():
            p = b["revenue"] - b["cogs"]
            book_list.append({
                **b,
                "profit": p,
                "margin_pct": (p / b["revenue"] * 100) if b["revenue"] else 0.0,
            })
        book_list.sort(key=lambda x: x["profit"], reverse=True)

        return {
            "method": cogs_method_label(method),
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": profit,
            "margin_pct": (profit / revenue * 100) if revenue else 0.0,
            "by_type": by_type,
            "by_book": book_list,
            "never_purchased_codes": sorted(never_purchased),
        }
    finally:
        conn.close()


def profit_trend(
    start: str,
    end: str,
    granularity: str = "daily",
    cogs_method: str | None = None,
    filters: AnalyticsFilters | None = None,
) -> list[dict]:
    if granularity not in GRANULARITIES:
        granularity = "daily"
    method = cogs_method or get_setting("cogs_method", "last_purchase")
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        bucket = _bucket_expr("s.sale_date", granularity)
        lines = conn.execute(
            f"""
            SELECT {bucket} AS bucket, si.book_id, si.quantity,
                   si.quantity * si.unit_price AS line_revenue,
                   s.discount, s.id AS sale_id, s.sale_type,
                   v.last_purchase_price
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            JOIN v_current_stock v ON v.book_id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?{sf}
            """,
            (start, end, *sp),
        ).fetchall()

        sale_discounts: dict[int, int] = {}
        for ln in lines:
            sale_discounts[ln["sale_id"]] = ln["discount"]

        buckets: dict[str, dict] = {}
        for ln in lines:
            b = buckets.setdefault(ln["bucket"], {
                "bucket": ln["bucket"],
                "line_revenue": 0,
                "cogs": 0,
                "sale_ids": set(),
            })
            if method == "weighted_average":
                unit_cogs = _weighted_avg_cost(conn, ln["book_id"])
            else:
                unit_cogs = ln["last_purchase_price"]
            b["line_revenue"] += ln["line_revenue"]
            b["cogs"] += ln["quantity"] * unit_cogs
            b["sale_ids"].add(ln["sale_id"])

        out = []
        for b in sorted(buckets.values(), key=lambda x: x["bucket"]):
            disc = sum(sale_discounts.get(sid, 0) for sid in b["sale_ids"])
            revenue = b["line_revenue"] - disc
            profit = revenue - b["cogs"]
            out.append({
                "bucket": b["bucket"],
                "revenue": revenue,
                "cogs": b["cogs"],
                "gross_profit": profit,
                "margin_pct": (profit / revenue * 100) if revenue else 0.0,
            })
        return out
    finally:
        conn.close()


def profit_by_dimension(
    start: str,
    end: str,
    dimension: str,
    cogs_method: str | None = None,
    filters: AnalyticsFilters | None = None,
) -> list[dict]:
    pnl = profit_and_loss(start, end, cogs_method, filters)
    key = {"category": "category", "publisher": "publisher", "book": "book_id"}.get(dimension)
    if not key:
        return []
    if dimension == "book":
        return pnl["by_book"]
    groups: dict[str, dict] = {}
    for b in pnl["by_book"]:
        label = b.get(key, "(Unknown)")
        g = groups.setdefault(label, {"label": label, "revenue": 0, "cogs": 0, "qty": 0})
        g["revenue"] += b["revenue"]
        g["cogs"] += b["cogs"]
        g["qty"] += b["qty"]
    out = []
    for g in groups.values():
        p = g["revenue"] - g["cogs"]
        out.append({
            **g,
            "profit": p,
            "margin_pct": (p / g["revenue"] * 100) if g["revenue"] else 0.0,
        })
    out.sort(key=lambda x: x["profit"], reverse=True)
    return out


def loss_making_sales(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    f = filters or AnalyticsFilters()
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f)
        rows = conn.execute(
            f"""
            SELECT si.quantity, si.unit_price, v.last_purchase_price,
                   b.code, b.title_roman, s.sale_date, s.id AS sale_id
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            JOIN v_current_stock v ON v.book_id = si.book_id
            WHERE s.sale_date BETWEEN ? AND ?
              AND v.last_purchase_price > 0
              AND si.unit_price < v.last_purchase_price{sf}
            """,
            (start, end, *sp),
        ).fetchall()
        total_loss = sum((r["last_purchase_price"] - r["unit_price"]) * r["quantity"] for r in rows)
        total_units = sum(r["quantity"] for r in rows)
        return {
            "line_count": len(rows),
            "units": total_units,
            "total_loss": total_loss,
            "lines": [dict(r) for r in rows[:50]],
        }
    finally:
        conn.close()


def purchase_to_sales_ratio_trend(
    start: str,
    end: str,
    granularity: str = "monthly",
) -> list[dict]:
    purchases = {r["bucket"]: r["spend"] for r in purchase_trend(start, end, granularity)}
    sales = {r["bucket"]: r["revenue"] for r in sales_trend(start, end, granularity)}
    buckets = sorted(set(purchases) | set(sales))
    return [{
        "bucket": b,
        "purchases": purchases.get(b, 0),
        "sales": sales.get(b, 0),
        "ratio": purchases.get(b, 0) / sales.get(b, 1) if sales.get(b, 0) else None,
    } for b in buckets]


# --- Customer analytics -------------------------------------------------------

def wholesale_customer_ranking(
    start: str,
    end: str,
    filters: AnalyticsFilters | None = None,
) -> list[dict]:
    f = filters or AnalyticsFilters()
    f2 = AnalyticsFilters(
        include_cancelled=f.include_cancelled,
        sale_type="wholesale",
        customer_id=f.customer_id,
        created_by=f.created_by,
        payment_method=f.payment_method,
    )
    conn = database.get_connection()
    try:
        sf, sp = _sales_filters(f2)
        rows = conn.execute(
            f"""
            SELECT wc.id AS customer_id, wc.name AS customer_name,
                   COUNT(*) AS txn_count,
                   COALESCE(SUM(s.total_amount), 0) AS revenue,
                   MAX(s.sale_date) AS last_order_date
            FROM (
                SELECT DISTINCT s.id, s.customer_id, s.total_amount, s.sale_date
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                JOIN books b ON b.id = si.book_id
                WHERE s.sale_date BETWEEN ? AND ?{sf}
            ) s
            JOIN wholesale_customers wc ON wc.id = s.customer_id
            GROUP BY wc.id
            ORDER BY revenue DESC
            """,
            (start, end, *sp),
        ).fetchall()
        unit_map = {
            r["customer_id"]: r["units"]
            for r in conn.execute(
                f"""
                SELECT s.customer_id, COALESCE(SUM(si.quantity), 0) AS units
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                JOIN books b ON b.id = si.book_id
                WHERE s.sale_date BETWEEN ? AND ?{sf}
                GROUP BY s.customer_id
                """,
                (start, end, *sp),
            ).fetchall()
        }
        out = []
        for r in rows:
            txn = r["txn_count"] or 0
            out.append({
                **dict(r),
                "units": unit_map.get(r["customer_id"], 0),
                "avg_order_value": r["revenue"] // txn if txn else 0,
            })
        return out
    finally:
        conn.close()


def customer_concentration(start: str, end: str) -> dict:
    ranking = wholesale_customer_ranking(start, end)
    total = sum(r["revenue"] for r in ranking)
    top5 = sum(r["revenue"] for r in ranking[:5])
    return {
        "total_revenue": total,
        "top5_revenue": top5,
        "top5_pct": (top5 / total * 100) if total else 0.0,
    }


def customer_frequency(start: str, end: str) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT wc.id, wc.name,
                   COUNT(*) AS order_count,
                   MIN(s.sale_date) AS first_order,
                   MAX(s.sale_date) AS last_order
            FROM sales s
            JOIN wholesale_customers wc ON wc.id = s.customer_id
            WHERE s.is_cancelled = 0 AND s.sale_type = 'wholesale'
              AND s.sale_date BETWEEN ? AND ?
            GROUP BY wc.id
            HAVING order_count > 1
            """,
            (start, end),
        ).fetchall()
        out = []
        for r in rows:
            d0 = dt.date.fromisoformat(r["first_order"])
            d1 = dt.date.fromisoformat(r["last_order"])
            span = (d1 - d0).days or 1
            out.append({
                **dict(r),
                "avg_days_between_orders": span / (r["order_count"] - 1),
            })
        return out
    finally:
        conn.close()


def inactive_customers(days: int = 90) -> list[dict]:
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT wc.id, wc.name,
                   MAX(s.sale_date) AS last_order,
                   COUNT(*) AS historical_orders
            FROM wholesale_customers wc
            JOIN sales s ON s.customer_id = wc.id
            WHERE s.is_cancelled = 0 AND s.sale_type = 'wholesale'
            GROUP BY wc.id
            HAVING last_order < ?
            ORDER BY last_order DESC
            """,
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def customer_top_books(customer_id: int, start: str, end: str) -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT b.code, b.title_roman, b.title_devanagari,
                   SUM(si.quantity) AS qty,
                   SUM(si.quantity * si.unit_price) AS revenue
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN books b ON b.id = si.book_id
            WHERE s.is_cancelled = 0 AND s.customer_id = ?
              AND s.sale_date BETWEEN ? AND ?
            GROUP BY b.id
            ORDER BY qty DESC
            LIMIT 20
            """,
            (customer_id, start, end),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def retail_aggregate(start: str, end: str) -> dict:
    conn = database.get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS txn_count, COALESCE(SUM(total_amount), 0) AS revenue
            FROM sales
            WHERE is_cancelled = 0 AND sale_type = 'retail'
              AND sale_date BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


# --- Employee analytics -------------------------------------------------------

def employee_activity(
    start: str,
    end: str,
    user_id: int | None = None,
    include_cancelled: bool = False,
) -> list[dict]:
    conn = database.get_connection()
    try:
        cancel = "" if include_cancelled else " AND is_cancelled = 0"
        user_rows = conn.execute(
            "SELECT id, full_name, username FROM users WHERE role IN ('owner', 'employee')"
            + (" AND id = ?" if user_id else ""),
            ([user_id] if user_id else []),
        ).fetchall()

        out = []
        for u in user_rows:
            sc = conn.execute(
                f"SELECT COUNT(*) AS c, COALESCE(SUM(total_amount),0) AS rev,"
                f" COALESCE(SUM(discount),0) AS disc"
                f" FROM sales WHERE created_by = ? AND sale_date BETWEEN ? AND ?{cancel}",
                (u["id"], start, end),
            ).fetchone()
            pc = conn.execute(
                f"SELECT COUNT(*) FROM purchases WHERE created_by = ?"
                f" AND purchase_date BETWEEN ? AND ?{cancel.replace('is_cancelled', 'is_cancelled')}",
                (u["id"], start, end),
            ).fetchone()[0]

            retail = conn.execute(
                f"SELECT COUNT(*) AS c, COALESCE(SUM(total_amount),0) AS rev"
                f" FROM sales WHERE created_by = ? AND sale_type = 'retail'"
                f" AND sale_date BETWEEN ? AND ?{cancel}",
                (u["id"], start, end),
            ).fetchone()
            wholesale = conn.execute(
                f"SELECT COUNT(*) AS c, COALESCE(SUM(total_amount),0) AS rev"
                f" FROM sales WHERE created_by = ? AND sale_type = 'wholesale'"
                f" AND sale_date BETWEEN ? AND ?{cancel}",
                (u["id"], start, end),
            ).fetchone()

            cancelled_sales = conn.execute(
                "SELECT COUNT(*) FROM sales WHERE created_by = ?"
                " AND sale_date BETWEEN ? AND ? AND is_cancelled = 1",
                (u["id"], start, end),
            ).fetchone()[0]
            total_sales = conn.execute(
                "SELECT COUNT(*) FROM sales WHERE created_by = ?"
                " AND sale_date BETWEEN ? AND ?",
                (u["id"], start, end),
            ).fetchone()[0]

            out.append({
                "user_id": u["id"],
                "full_name": u["full_name"],
                "username": u["username"],
                "sales_count": sc["c"],
                "sales_revenue": sc["rev"],
                "purchase_count": pc,
                "discount_total": sc["disc"],
                "retail_count": retail["c"],
                "retail_revenue": retail["rev"],
                "retail_avg_sale": retail["rev"] // retail["c"] if retail["c"] else 0,
                "wholesale_count": wholesale["c"],
                "wholesale_revenue": wholesale["rev"],
                "wholesale_avg_sale": wholesale["rev"] // wholesale["c"] if wholesale["c"] else 0,
                "cancellation_rate": (cancelled_sales / total_sales * 100) if total_sales else 0.0,
            })
        return out
    finally:
        conn.close()


def employee_daily_timeline(start: str, end: str, user_id: int | None = None) -> dict:
    conn = database.get_connection()
    try:
        uid = " AND created_by = ?" if user_id else ""
        params: list[Any] = [start, end]
        if user_id:
            params.append(user_id)
        sales = conn.execute(
            f"""
            SELECT sale_date AS day, created_by, COUNT(*) AS cnt
            FROM sales WHERE is_cancelled = 0 AND sale_date BETWEEN ? AND ?{uid}
            GROUP BY sale_date, created_by
            """,
            params,
        ).fetchall()
        purchases = conn.execute(
            f"""
            SELECT purchase_date AS day, created_by, COUNT(*) AS cnt
            FROM purchases WHERE is_cancelled = 0 AND purchase_date BETWEEN ? AND ?{uid}
            GROUP BY purchase_date, created_by
            """,
            params,
        ).fetchall()
        return {
            "sales": [dict(r) for r in sales],
            "purchases": [dict(r) for r in purchases],
        }
    finally:
        conn.close()


def employee_self_stats(user_id: int) -> dict:
    today = dt.date.today().isoformat()
    week_start = (dt.date.today() - dt.timedelta(days=6)).isoformat()
    act_today = employee_activity(today, today, user_id=user_id)
    act_week = employee_activity(week_start, today, user_id=user_id)
    t = act_today[0] if act_today else {}
    w = act_week[0] if act_week else {}
    return {
        "today_sales": t.get("sales_count", 0),
        "today_purchases": t.get("purchase_count", 0),
        "week_sales": w.get("sales_count", 0),
        "week_purchases": w.get("purchase_count", 0),
    }


# --- Dashboard KPIs -----------------------------------------------------------

def dashboard_kpis(start: str, end: str, filters: AnalyticsFilters | None = None) -> dict:
    f = filters or AnalyticsFilters()
    current = sales_summary(start, end, f)
    prev_start, prev_end = previous_period(start, end)
    previous = sales_summary(prev_start, prev_end, f)
    return {
        "period": {"start": start, "end": end},
        "compare_period": {"start": prev_start, "end": prev_end},
        "revenue": current["revenue"],
        "txn_count": current["txn_count"],
        "units": current["units"],
        "avg_ticket": current["avg_ticket"],
        "revenue_change_pct": _pct_change(current["revenue"], previous["revenue"]),
        "txn_change_pct": _pct_change(current["txn_count"], previous["txn_count"]),
        "units_change_pct": _pct_change(current["units"], previous["units"]),
        "avg_ticket_change_pct": _pct_change(current["avg_ticket"], previous["avg_ticket"]),
    }


def cash_flow_trend(start: str, end: str, granularity: str = "daily") -> list[dict]:
    sales = {r["bucket"]: r["revenue"] for r in sales_trend(start, end, granularity)}
    purchases = {r["bucket"]: r["spend"] for r in purchase_trend(start, end, granularity)}
    buckets = sorted(set(sales) | set(purchases))
    return [{
        "bucket": b,
        "sales": sales.get(b, 0),
        "purchases": purchases.get(b, 0),
    } for b in buckets]


# --- Book detail drill-down ---------------------------------------------------

def book_analytics_detail(book_id: int, start: str, end: str) -> dict:
    conn = database.get_connection()
    try:
        book = conn.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        stock = conn.execute(
            "SELECT stock, last_purchase_price FROM v_current_stock WHERE book_id = ?",
            (book_id,),
        ).fetchone()
        sales = sales_trend(start, end, "daily", AnalyticsFilters(book_id=book_id))
        purchases = purchase_trend(start, end, "daily", AnalyticsFilters(book_id=book_id))
        pnl = profit_and_loss(start, end, filters=AnalyticsFilters(book_id=book_id))
        return {
            "book": dict(book) if book else None,
            "stock": dict(stock) if stock else None,
            "sales_trend": sales,
            "purchase_trend": purchases,
            "pnl": pnl,
        }
    finally:
        conn.close()


# --- Alerts -------------------------------------------------------------------

def _newly_low_stock_count(days: int = 7) -> int:
    today = dt.date.today()
    past = (today - dt.timedelta(days=days)).isoformat()
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT book_id, stock, low_stock_threshold FROM v_current_stock WHERE is_active = 1"
        ).fetchall()
        count = 0
        for r in rows:
            if r["stock"] > r["low_stock_threshold"]:
                continue
            stock_then = _stock_at_date(conn, past).get(r["book_id"], 0)
            if stock_then > r["low_stock_threshold"]:
                count += 1
        return count
    finally:
        conn.close()


def active_alerts() -> list[dict]:
    settings = get_settings()
    alerts: list[dict] = []
    today = dt.date.today()
    month_start = today.replace(day=1).isoformat()
    today_s = today.isoformat()

    from services import inventory_service

    low = inventory_service.low_stock_books()
    newly = _newly_low_stock_count(7)
    msg = f"{len(low)} title(s) below low-stock threshold."
    if newly:
        msg += f" {newly} newly low this week."
    if low:
        alerts.append({"level": "warning", "code": "low_stock", "message": msg})

    dead = dead_stock()
    capital = sum(d.get("tied_up_capital", 0) for d in dead)
    threshold = int(settings.get("dead_stock_capital_alert_paise", "5000000"))
    if capital >= threshold:
        alerts.append({
            "level": "warning",
            "code": "dead_stock_capital",
            "message": f"Dead stock ties up {capital} paise ({len(dead)} titles).",
        })

    # MTD margin vs last month
    last_month_end = month_start
    lm_start = (today.replace(day=1) - dt.timedelta(days=1)).replace(day=1).isoformat()
    lm_end = (today.replace(day=1) - dt.timedelta(days=1)).isoformat()
    mtd = profit_and_loss(month_start, today_s)
    lm = profit_and_loss(lm_start, lm_end)
    drop_pts = float(settings.get("margin_drop_alert_points", "5"))
    if lm["margin_pct"] and mtd["margin_pct"] < lm["margin_pct"] - drop_pts:
        alerts.append({
            "level": "warning",
            "code": "margin_drop",
            "message": (
                f"MTD margin {mtd['margin_pct']:.1f}% is down "
                f"{lm['margin_pct'] - mtd['margin_pct']:.1f} pts vs last month."
            ),
        })

    # Sales spike/drop (P2)
    trend = sales_trend((today - dt.timedelta(days=29)).isoformat(), today_s)
    if trend:
        avg = sum(t["revenue"] for t in trend) / len(trend)
        today_rev = next((t["revenue"] for t in trend if t["bucket"] == today_s), 0)
        if avg > 0 and today_rev > 2 * avg:
            alerts.append({"level": "info", "code": "sales_spike",
                           "message": "Today's sales are unusually high vs the 30-day average."})
        elif avg > 0 and today_rev < 0.5 * avg and today_rev > 0:
            alerts.append({"level": "info", "code": "sales_drop",
                           "message": "Today's sales are below half the 30-day daily average."})

    loss_today = loss_making_sales(today_s, today_s)
    if loss_today["line_count"]:
        alerts.append({
            "level": "error",
            "code": "loss_making_today",
            "message": f"{loss_today['line_count']} line(s) sold below cost today.",
        })

    reorder = reorder_suggestions()
    if reorder:
        alerts.append({
            "level": "info",
            "code": "reorder",
            "message": f"{len(reorder)} title(s) suggested for reorder.",
        })

    return alerts


# --- Filter option lists ------------------------------------------------------

def filter_options() -> dict:
    conn = database.get_connection()
    try:
        categories = [r[0] for r in conn.execute(
            "SELECT DISTINCT COALESCE(category, '(Uncategorized)') FROM books ORDER BY 1").fetchall()]
        publishers = [r[0] for r in conn.execute(
            "SELECT DISTINCT COALESCE(publisher, '(Unknown publisher)') FROM books ORDER BY 1").fetchall()]
        languages = [r[0] for r in conn.execute(
            "SELECT DISTINCT COALESCE(language, '(Unknown)') FROM books ORDER BY 1").fetchall()]
        users = [dict(r) for r in conn.execute(
            "SELECT id, full_name FROM users ORDER BY full_name").fetchall()]
        suppliers = [dict(r) for r in conn.execute(
            "SELECT id, name FROM suppliers WHERE is_active = 1 ORDER BY name").fetchall()]
        customers = [dict(r) for r in conn.execute(
            "SELECT id, name FROM wholesale_customers WHERE is_active = 1 ORDER BY name").fetchall()]
        return {
            "categories": categories,
            "publishers": publishers,
            "languages": languages,
            "users": users,
            "suppliers": suppliers,
            "customers": customers,
        }
    finally:
        conn.close()
