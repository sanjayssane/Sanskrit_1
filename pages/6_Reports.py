"""Reports: Sale–Purchase statement, P&L (owner only), stock report (FR-7)."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import auth_service, purchase_service, report_service, sale_service
from utils import exports
from utils.money import fmt_inr

user = auth_service.require_login()
is_owner = user["role"] == "owner"

st.title("Reports")

tabs = ["Sale–Purchase Statement", "Stock Report"]
if is_owner:
    tabs.insert(1, "Profit & Loss (Owner)")
tab_objects = st.tabs(tabs)

c1, c2 = st.columns(2)
start = c1.date_input("From", dt.date.today().replace(day=1), key="rep_from")
end = c2.date_input("To", dt.date.today(), key="rep_to")
start_s, end_s = start.isoformat(), end.isoformat()

# --- Sale–Purchase Statement -------------------------------------------------

with tab_objects[0]:
    stmt = report_service.sale_purchase_statement(start_s, end_s)

    st.subheader("Totals")
    summary = pd.DataFrame([
        {"Section": "Purchases", "Transactions": stmt["purchases"]["cnt"],
         "Quantity": stmt["purchases"]["qty"],
         "Amount": fmt_inr(stmt["purchases"]["amount"])},
        {"Section": "Sales — Retail", "Transactions": stmt["sales"]["retail"]["cnt"],
         "Quantity": stmt["sales"]["retail"]["qty"],
         "Amount": fmt_inr(stmt["sales"]["retail"]["amount"])},
        {"Section": "Sales — Wholesale", "Transactions": stmt["sales"]["wholesale"]["cnt"],
         "Quantity": stmt["sales"]["wholesale"]["qty"],
         "Amount": fmt_inr(stmt["sales"]["wholesale"]["amount"])},
        {"Section": "Sales — Total", "Transactions": stmt["sales_total"]["cnt"],
         "Quantity": stmt["sales_total"]["qty"],
         "Amount": fmt_inr(stmt["sales_total"]["amount"])},
    ])
    st.dataframe(summary, hide_index=True, width="stretch")
    exports.download_buttons(summary, f"sale-purchase-summary-{start_s}-{end_s}", "sps_sum")

    breakdown_mode = st.radio("Breakdown", ["Day-wise", "Month-wise"], horizontal=True)
    rows = stmt["daily"] if breakdown_mode == "Day-wise" else stmt["monthly"]
    if rows:
        bdf = pd.DataFrame([{
            "Period": r["bucket"],
            "Purchases": fmt_inr(r["purchase_amount"]),
            "Retail sales": fmt_inr(r["retail_amount"]),
            "Wholesale sales": fmt_inr(r["wholesale_amount"]),
            "Total sales": fmt_inr(r["retail_amount"] + r["wholesale_amount"]),
        } for r in rows])
        st.dataframe(bdf, hide_index=True, width="stretch")
        exports.download_buttons(bdf, f"sale-purchase-breakdown-{start_s}-{end_s}", "sps_bd")
    else:
        st.info("No transactions in the selected range.")

    with st.expander("Drill-down: individual transactions"):
        st.markdown("**Purchases**")
        purchases = purchase_service.list_purchases(start_s, end_s, include_cancelled=False)
        if purchases:
            pdf_ = pd.DataFrame([{
                "ID": p["id"], "Date": p["purchase_date"], "Supplier": p["supplier_name"],
                "Qty": p["total_qty"], "Amount": fmt_inr(p["total_amount"]),
                "By": p["created_by_name"]} for p in purchases])
            st.dataframe(pdf_, hide_index=True, width="stretch")
            exports.download_buttons(pdf_, f"purchases-{start_s}-{end_s}", "dd_p")
        else:
            st.caption("None")
        st.markdown("**Sales**")
        sales = sale_service.list_sales(start_s, end_s, include_cancelled=False)
        if sales:
            sdf = pd.DataFrame([{
                "ID": s["id"], "Date": s["sale_date"], "Type": s["sale_type"],
                "Customer": s["customer_name"] or "(walk-in)", "Qty": s["total_qty"],
                "Amount": fmt_inr(s["total_amount"]), "By": s["created_by_name"]}
                for s in sales])
            st.dataframe(sdf, hide_index=True, width="stretch")
            exports.download_buttons(sdf, f"sales-{start_s}-{end_s}", "dd_s")
        else:
            st.caption("None")

# --- P&L (owner only) ----------------------------------------------------------

if is_owner:
    with tab_objects[1]:
        pnl = report_service.profit_and_loss(start_s, end_s)
        st.caption(f"COGS method: {pnl['method']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue", fmt_inr(pnl["revenue"]))
        c2.metric("COGS", fmt_inr(pnl["cogs"]))
        c3.metric("Gross profit", fmt_inr(pnl["gross_profit"]))
        c4.metric("Margin", f"{pnl['margin_pct']:.1f}%")

        if pnl["never_purchased_codes"]:
            st.warning(
                "Books sold but never purchased (COGS counted as 0): "
                + ", ".join(pnl["never_purchased_codes"]))

        st.subheader("By sale type")
        type_df = pd.DataFrame([{
            "Type": t.capitalize(),
            "Revenue (after discount)": fmt_inr(v["revenue"]),
            "Discounts": fmt_inr(v["discount"]),
            "COGS": fmt_inr(v["cogs"]),
            "Profit": fmt_inr(v["profit"]),
        } for t, v in pnl["by_type"].items()])
        st.dataframe(type_df, hide_index=True, width="stretch")
        exports.download_buttons(type_df, f"pnl-by-type-{start_s}-{end_s}", "pnl_t")

        st.subheader("Top profitable books")
        if pnl["top_books"]:
            top_df = pd.DataFrame([{
                "Code": b["code"], "Title": f"{b['title_roman']} / {b['title_devanagari']}",
                "Qty sold": b["qty"], "Revenue": fmt_inr(b["revenue"]),
                "COGS": fmt_inr(b["cogs"]), "Profit": fmt_inr(b["profit"]),
            } for b in pnl["top_books"][:20]])
            st.dataframe(top_df, hide_index=True, width="stretch")
            exports.download_buttons(top_df, f"pnl-top-books-{start_s}-{end_s}", "pnl_b")
        else:
            st.info("No sales in the selected range.")

# --- Stock report -----------------------------------------------------------------

with tab_objects[-1]:
    report = report_service.stock_report()
    c1, c2, c3 = st.columns(3)
    c1.metric("Titles", report["total_titles"])
    c2.metric("Units in stock", report["total_units"])
    c3.metric("Stock value", fmt_inr(report["total_value"]))

    if report["rows"]:
        stock_df = pd.DataFrame([{
            "Code": r["code"],
            "Title (Devanagari)": r["title_devanagari"],
            "Title (Roman)": r["title_roman"],
            "Publisher": r["publisher"] or "",
            "Stock": r["stock"],
            "Last purchase price": fmt_inr(r["last_purchase_price"]),
            "Stock value": fmt_inr(r["stock_value"]),
            "Low stock": "YES" if r["is_low"] else "",
        } for r in report["rows"]])
        st.dataframe(stock_df, hide_index=True, width="stretch")
        exports.download_buttons(stock_df, f"stock-report-{end_s}", "stock_rep")

        if report["low_stock"]:
            st.subheader("Low-stock books")
            low_df = pd.DataFrame([{
                "Code": r["code"], "Title": f"{r['title_roman']} / {r['title_devanagari']}",
                "Stock": r["stock"], "Threshold": r["low_stock_threshold"],
            } for r in report["low_stock"]])
            st.dataframe(low_df, hide_index=True, width="stretch")
            exports.download_buttons(low_df, f"low-stock-{end_s}", "low_rep")
    else:
        st.info("No books in the catalog yet.")
