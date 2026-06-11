"""Inventory: stock table with low-stock flags, per-book ledger, adjustments (FR-6)."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import auth_service, inventory_service
from utils.money import fmt_inr

user = auth_service.require_login()
is_owner = user["role"] == "owner"

st.title("Inventory")

tab_stock, tab_ledger, tab_adjust = st.tabs(
    ["Current stock", "Stock ledger", "Manual adjustment"])

# --- Current stock -----------------------------------------------------------

with tab_stock:
    include_inactive = st.checkbox("Include deactivated books")
    rows = inventory_service.current_stock(include_inactive=include_inactive)
    if not rows:
        st.info("No books in the catalog yet.")
    else:
        low_count = sum(1 for r in rows if r["is_low"])
        total_value = sum(r["stock_value"] for r in rows)
        c1, c2, c3 = st.columns(3)
        c1.metric("Titles", len(rows))
        c2.metric("Stock value", fmt_inr(total_value))
        c3.metric("Low-stock titles", low_count)

        df = pd.DataFrame([{
            "Code": r["code"],
            "Title (Devanagari)": r["title_devanagari"],
            "Title (Roman)": r["title_roman"],
            "Publisher": r["publisher"] or "",
            "Stock": r["stock"],
            "Threshold": r["low_stock_threshold"],
            "Low?": "LOW" if r["is_low"] else "",
            "Last purchase price": fmt_inr(r["last_purchase_price"]),
            "Stock value": fmt_inr(r["stock_value"]),
        } for r in rows])
        only_low = st.checkbox("Show only low-stock books")
        if only_low:
            df = df[df["Low?"] == "LOW"]
        st.dataframe(df, hide_index=True, width="stretch")

# --- Ledger --------------------------------------------------------------------

with tab_ledger:
    rows = inventory_service.current_stock(include_inactive=True)
    if not rows:
        st.info("No books in the catalog yet.")
    else:
        labels = {f"{r['code']} — {r['title_roman']} / {r['title_devanagari']}": r
                  for r in rows}
        selected = labels[st.selectbox("Book", list(labels))]
        ledger = inventory_service.stock_ledger(selected["book_id"])
        if not ledger:
            st.info("No stock movements for this book yet.")
        else:
            st.dataframe(pd.DataFrame([{
                "Date": e["movement_date"],
                "Type": e["movement_type"],
                "Qty +/-": e["quantity_delta"],
                "Balance": e["balance"],
                "Ref #": e["reference_id"],
                "By": e["created_by_name"],
            } for e in ledger]), hide_index=True, width="stretch")
            st.caption(f"Current stock: {selected['stock']}")

# --- Manual adjustment ----------------------------------------------------------

with tab_adjust:
    if not is_owner:
        st.info("Manual stock adjustments are available to the Owner only.")
    else:
        rows = inventory_service.current_stock(include_inactive=True)
        if not rows:
            st.info("No books in the catalog yet.")
        else:
            labels = {f"{r['code']} — {r['title_roman']} (stock: {r['stock']})": r
                      for r in rows}
            with st.form("adjustment_form", clear_on_submit=True):
                selected = labels[st.selectbox("Book", list(labels))]
                adj_date = st.date_input("Date", dt.date.today())
                delta = st.number_input(
                    "Quantity change (negative = damaged/lost, positive = found)",
                    min_value=-10000, max_value=10000, step=1, value=0)
                reason = st.text_input("Reason (required)")
                ok = st.form_submit_button("Record adjustment", type="primary")
            if ok:
                try:
                    inventory_service.add_adjustment(
                        selected["book_id"], adj_date.isoformat(), int(delta),
                        reason, user["id"])
                    st.success("Adjustment recorded.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
