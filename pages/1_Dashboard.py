"""Dashboard: today's totals, analytics charts, alerts, recent transactions (FR-8, AR-DASH)."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import (analytics_service, auth_service, inventory_service,
                      purchase_service, report_service, sale_service)
from utils import analytics_ui
from utils.money import fmt_inr

user = auth_service.require_login()
is_owner = user["role"] == "owner"

st.title("Dashboard")
st.caption(f"Welcome, {user['full_name']}")

today = dt.date.today().isoformat()
month_start = dt.date.today().replace(day=1).isoformat()
last30_start = (dt.date.today() - dt.timedelta(days=29)).isoformat()

# Alerts (AR-ALERT)
alerts = analytics_service.active_alerts()
for a in alerts[:3]:
    fn = {"error": st.error, "warning": st.warning, "info": st.info}.get(a["level"], st.info)
    fn(a["message"])

today_sales = sale_service.list_sales(today, today, include_cancelled=False)
today_purchases = purchase_service.list_purchases(today, today, include_cancelled=False)

c1, c2, c3 = st.columns(3)
c1.metric("Today's sales", fmt_inr(sum(s["total_amount"] for s in today_sales)),
          f"{len(today_sales)} transaction(s)")
c2.metric("Today's purchases", fmt_inr(sum(p["total_amount"] for p in today_purchases)),
          f"{len(today_purchases)} transaction(s)")
low_stock = inventory_service.low_stock_books()
c3.metric("Low-stock titles", len(low_stock))

if not is_owner:
    self_stats = analytics_service.employee_self_stats(user["id"])
    c1, c2 = st.columns(2)
    c1.metric("Your sales today", self_stats["today_sales"])
    c2.metric("Your sales this week", self_stats["week_sales"])

if is_owner:
    pnl = report_service.profit_and_loss(month_start, today)
    st.subheader("Month to date (Owner)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MTD revenue", fmt_inr(pnl["revenue"]))
    c2.metric("MTD COGS", fmt_inr(pnl["cogs"]))
    c3.metric("MTD gross profit", fmt_inr(pnl["gross_profit"]))
    c4.metric("Margin", f"{pnl['margin_pct']:.1f}%")

# Analytics KPIs — last 30 days (AR-DASH-3)
st.subheader("Last 30 days")
kpis = analytics_service.dashboard_kpis(last30_start, today)
c1, c2, c3, c4 = st.columns(4)
analytics_ui.metric_delta("Sales revenue", fmt_inr(kpis["revenue"]), kpis["revenue_change_pct"])
analytics_ui.metric_delta("Transactions", str(kpis["txn_count"]), kpis["txn_change_pct"])
analytics_ui.metric_delta("Units sold", str(kpis["units"]), kpis["units_change_pct"])
analytics_ui.metric_delta("Avg ticket", fmt_inr(kpis["avg_ticket"]), kpis["avg_ticket_change_pct"])

col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    st.markdown("**Sales revenue trend (30 days)**")
    trend = analytics_service.sales_trend(last30_start, today, "daily")
    analytics_ui.trend_line_chart(trend, "revenue", "Revenue (paise)")

with col_chart2:
    st.markdown("**Retail vs wholesale (this month)**")
    by_type = analytics_service.sales_by_type(month_start, today)
    if by_type["retail"]["revenue"] or by_type["wholesale"]["revenue"]:
        split = pd.DataFrame([
            {"Type": "Retail", "Revenue": by_type["retail"]["revenue"]},
            {"Type": "Wholesale", "Revenue": by_type["wholesale"]["revenue"]},
        ]).set_index("Type")
        st.bar_chart(split, width="stretch")
    else:
        st.info("No sales this month yet.")

if is_owner:
    st.markdown("**MTD gross profit trend**")
    ptrend = analytics_service.profit_trend(month_start, today, "daily")
    analytics_ui.trend_line_chart(ptrend, "gross_profit", "Gross profit (paise)")

    st.markdown("**Purchase vs sales cash flow (90 days)**")
    cf_start = (dt.date.today() - dt.timedelta(days=89)).isoformat()
    cf = analytics_service.cash_flow_trend(cf_start, today)
    if cf:
        cf_df = pd.DataFrame(cf).set_index("bucket")[["sales", "purchases"]]
        st.line_chart(cf_df, width="stretch")

st.markdown("**Top 5 bestsellers (this month)**")
best = analytics_service.bestsellers(month_start, today, 5)
if best:
    st.dataframe(pd.DataFrame([{
        "Code": b["code"],
        "Title": f"{b['title_roman']} / {b['title_devanagari']}",
        "Qty": b["qty"],
        "Revenue": fmt_inr(b["line_revenue"]),
    } for b in best]), hide_index=True, width="stretch")
else:
    st.caption("No sales this month.")

if not is_owner:
    st.markdown("**Your activity**")
    self_stats = analytics_service.employee_self_stats(user["id"])
    c1, c2 = st.columns(2)
    c1.metric("Purchases recorded this week", self_stats["week_purchases"])
    c2.metric("Sales recorded this week", self_stats["week_sales"])

col_low, col_recent = st.columns(2)

with col_low:
    st.subheader("Low-stock alerts")
    if low_stock:
        st.dataframe(pd.DataFrame([{
            "Code": b["code"],
            "Title": f"{b['title_roman']} / {b['title_devanagari']}",
            "Stock": b["stock"],
            "Threshold": b["low_stock_threshold"],
        } for b in low_stock]), hide_index=True, width="stretch")
    else:
        st.success("No books below their low-stock threshold.")

with col_recent:
    st.subheader("Recent transactions")
    recent_sales = sale_service.list_sales()[:5]
    recent_purchases = purchase_service.list_purchases()[:5]
    recent = (
        [{"When": s["sale_date"], "Type": f"Sale ({s['sale_type']})",
          "Ref": f"#{s['id']}", "Amount": fmt_inr(s["total_amount"]),
          "By": s["created_by_name"],
          "Status": "CANCELLED" if s["is_cancelled"] else "OK"} for s in recent_sales]
        + [{"When": p["purchase_date"], "Type": "Purchase",
            "Ref": f"#{p['id']}", "Amount": fmt_inr(p["total_amount"]),
            "By": p["created_by_name"],
            "Status": "CANCELLED" if p["is_cancelled"] else "OK"}
           for p in recent_purchases])
    if recent:
        recent.sort(key=lambda r: r["When"], reverse=True)
        st.dataframe(pd.DataFrame(recent[:10]), hide_index=True, width="stretch")
    else:
        st.info("No transactions yet.")
