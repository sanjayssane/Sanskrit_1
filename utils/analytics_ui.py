"""Shared Streamlit helpers for Analytics pages."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from services import analytics_service
from services.analytics_service import AnalyticsFilters, PERIOD_PRESETS
from utils.money import fmt_inr


def render_period_selector(key_prefix: str = "an") -> tuple[str, str, str]:
    preset = st.selectbox("Period", PERIOD_PRESETS, index=3, key=f"{key_prefix}_preset")
    custom_start = custom_end = None
    if preset == "Custom range":
        c1, c2 = st.columns(2)
        custom_start = c1.date_input("From", dt.date.today().replace(day=1),
                                     key=f"{key_prefix}_from")
        custom_end = c2.date_input("To", dt.date.today(), key=f"{key_prefix}_to")
    start, end = analytics_service.period_range(preset, custom_start, custom_end)
    return preset, start, end


def render_filters_bar(is_owner: bool, key_prefix: str = "an") -> AnalyticsFilters:
    opts = analytics_service.filter_options()
    with st.expander("Filters", expanded=False):
        c1, c2, c3 = st.columns(3)
        sale_type = c1.selectbox("Sale type", ["Both", "Retail", "Wholesale"],
                                 key=f"{key_prefix}_stype")
        payment = c2.selectbox("Payment", ["All", "cash", "upi", "card", "cheque"],
                               key=f"{key_prefix}_pay")
        category = c3.selectbox("Category", ["All"] + opts["categories"],
                                key=f"{key_prefix}_cat")
        c4, c5, c6 = st.columns(3)
        publisher = c4.selectbox("Publisher", ["All"] + opts["publishers"],
                                 key=f"{key_prefix}_pub")
        language = c5.selectbox("Language", ["All"] + opts["languages"],
                                key=f"{key_prefix}_lang")
        user_label = c6.selectbox(
            "Recorded by",
            ["All"] + [u["full_name"] for u in opts["users"]],
            key=f"{key_prefix}_user",
        )
        c7, c8 = st.columns(2)
        supplier_label = c7.selectbox(
            "Supplier", ["All"] + [s["name"] for s in opts["suppliers"]],
            key=f"{key_prefix}_sup",
        )
        customer_label = c8.selectbox(
            "Wholesale customer", ["All"] + [c["name"] for c in opts["customers"]],
            key=f"{key_prefix}_cust",
        )
        include_cancelled = False
        include_inactive = False
        if is_owner:
            c9, c10 = st.columns(2)
            include_cancelled = c9.checkbox("Include cancelled", key=f"{key_prefix}_cancel")
            include_inactive = c10.checkbox("Include inactive books", key=f"{key_prefix}_inact")

    user_id = None
    if user_label != "All":
        user_id = next(u["id"] for u in opts["users"] if u["full_name"] == user_label)
    supplier_id = None
    if supplier_label != "All":
        supplier_id = next(s["id"] for s in opts["suppliers"] if s["name"] == supplier_label)
    customer_id = None
    if customer_label != "All":
        customer_id = next(c["id"] for c in opts["customers"] if c["name"] == customer_label)

    return AnalyticsFilters(
        include_cancelled=include_cancelled,
        include_inactive_books=include_inactive,
        sale_type=None if sale_type == "Both" else sale_type.lower(),
        category=None if category == "All" else category,
        publisher=None if publisher == "All" else publisher,
        language=None if language == "All" else language,
        payment_method=None if payment == "All" else payment,
        created_by=user_id,
        supplier_id=supplier_id,
        customer_id=customer_id,
    )


def metric_delta(label: str, value: str, pct: float | None, help_text: str = "") -> None:
    if pct is None:
        st.metric(label, value, help=help_text or None)
    else:
        st.metric(label, value, f"{pct:+.1f}% vs prev period", help=help_text or None)


def trend_line_chart(rows: list[dict], value_key: str, label: str) -> None:
    if not rows:
        st.info("No data for the selected filters.")
        return
    df = pd.DataFrame(rows).set_index("bucket")[[value_key]]
    df.columns = [label]
    st.line_chart(df, width="stretch")


def bar_chart(rows: list[dict], label_key: str, value_key: str, title: str = "") -> None:
    if not rows:
        st.info("No data for the selected filters.")
        return
    df = pd.DataFrame(rows).set_index(label_key)[[value_key]]
    df.columns = [title or value_key]
    st.bar_chart(df, width="stretch")


def render_alerts() -> None:
    alerts = analytics_service.active_alerts()
    if not alerts:
        st.success("No active alerts.")
        return
    for a in alerts:
        fn = {"error": st.error, "warning": st.warning, "info": st.info}.get(a["level"], st.info)
        fn(a["message"])


def book_title_row(row: dict) -> str:
    return f"{row.get('title_roman', '')} / {row.get('title_devanagari', '')}"


def render_book_drilldown(book_id: int, start: str, end: str, is_owner: bool) -> None:
    detail = analytics_service.book_analytics_detail(book_id, start, end)
    if not detail["book"]:
        st.warning("Book not found.")
        return
    b = detail["book"]
    st.markdown(f"**{b['code']}** — {b['title_roman']} / {b['title_devanagari']}")
    if detail["stock"]:
        st.caption(f"Current stock: {detail['stock']['stock']}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("Sales trend")
        trend_line_chart(detail["sales_trend"], "revenue", "Revenue (paise)")
    with c2:
        st.markdown("Purchase trend")
        trend_line_chart(detail["purchase_trend"], "spend", "Spend (paise)")
    if is_owner and detail["pnl"]["by_book"]:
        p = detail["pnl"]["by_book"][0]
        st.caption(
            f"Period P&L: revenue {fmt_inr(p['revenue'])}, "
            f"profit {fmt_inr(p['profit'])} ({p['margin_pct']:.1f}%)"
        )
