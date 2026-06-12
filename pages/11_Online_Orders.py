"""Staff view: pending online orders, fulfillment, and cancellation."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import auth_service, order_service, sale_service
from services.sale_service import InsufficientStockError
from utils import receipt_pdf
from utils.money import fmt_inr

user = auth_service.require_login()

st.title("Online Orders")

tab_pending, tab_completed, tab_cancelled = st.tabs(["Pending", "Completed", "Cancelled"])


def _order_table(orders: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{
        "Order #": o["id"],
        "Date": o["order_date"],
        "Customer": o["customer_name"],
        "Phone": o["customer_phone"],
        "Email": o["customer_email"] or "",
        "Lines": o["line_count"],
        "Qty": o["total_qty"],
        "Total": fmt_inr(o["total_amount"]),
    } for o in orders])


def _show_detail(order: dict) -> None:
    items = order_service.get_order_items(order["id"])
    st.dataframe(pd.DataFrame([{
        "Book": f"{i['code']} — {i['title_roman']} / {i['title_devanagari']}",
        "Qty": i["quantity"],
        "Unit price": fmt_inr(i["unit_price"]),
        "Line total": fmt_inr(i["line_total"]),
    } for i in items]), hide_index=True, width="stretch")
    if order["notes"]:
        st.caption(f"Customer notes: {order['notes']}")


with tab_pending:
    pending = order_service.list_orders(status="pending")
    if not pending:
        st.info("No pending online orders.")
    else:
        st.dataframe(_order_table(pending), hide_index=True, width="stretch")
        sel = st.selectbox("Manage order #", [o["id"] for o in pending], key="pending_sel")
        order = next(o for o in pending if o["id"] == sel)
        _show_detail(order)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Mark complete", type="primary", key="complete_btn"):
                try:
                    sale_id = order_service.complete_order(sel, user["id"])
                    st.session_state["last_completed_sale"] = sale_id
                    st.session_state["last_completed_order"] = sel
                    st.rerun()
                except InsufficientStockError as exc:
                    st.error(str(exc))
                except ValueError as exc:
                    st.error(str(exc))
        with c2:
            with st.form("cancel_order_form"):
                reason = st.text_input("Cancellation reason (required)")
                cancel_ok = st.form_submit_button("Cancel order")
            if cancel_ok:
                try:
                    order_service.cancel_order(sel, user["id"], reason)
                    st.success(f"Order #{sel} cancelled.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        if st.session_state.get("last_completed_order") == sel:
            sale_id = st.session_state.get("last_completed_sale")
            st.success(f"Order #{sel} completed — sale #{sale_id} recorded, stock updated.")
            if sale_id:
                st.download_button(
                    f"Download receipt #{sale_id} (PDF)",
                    data=receipt_pdf.build_receipt_pdf(
                        sale_service.get_sale(sale_id),
                        sale_service.get_sale_items(sale_id)),
                    file_name=f"receipt-{sale_id}.pdf",
                    mime="application/pdf",
                    key="receipt_complete",
                )

with tab_completed:
    c1, c2 = st.columns(2)
    start = c1.date_input("From", dt.date.today() - dt.timedelta(days=30), key="co_from")
    end = c2.date_input("To", dt.date.today(), key="co_to")
    completed = order_service.list_orders(
        start.isoformat(), end.isoformat(), status="completed")
    if not completed:
        st.info("No completed online orders in this range.")
    else:
        df = pd.DataFrame([{
            "Order #": o["id"],
            "Date": o["order_date"],
            "Customer": o["customer_name"],
            "Phone": o["customer_phone"],
            "Total": fmt_inr(o["total_amount"]),
            "Completed at": o["completed_at"] or "",
            "Completed by": o["completed_by_name"] or "",
            "Sale #": o["sale_id"] or "",
        } for o in completed])
        st.dataframe(df, hide_index=True, width="stretch")

        sel = st.selectbox("View order #", [o["id"] for o in completed], key="completed_sel")
        order = next(o for o in completed if o["id"] == sel)
        _show_detail(order)
        if order.get("sale_id"):
            st.download_button(
                f"Download receipt #{order['sale_id']} (PDF)",
                data=receipt_pdf.build_receipt_pdf(
                    sale_service.get_sale(order["sale_id"]),
                    sale_service.get_sale_items(order["sale_id"])),
                file_name=f"receipt-{order['sale_id']}.pdf",
                mime="application/pdf",
                key="receipt_completed",
            )

with tab_cancelled:
    c1, c2 = st.columns(2)
    start = c1.date_input("From", dt.date.today() - dt.timedelta(days=30), key="ca_from")
    end = c2.date_input("To", dt.date.today(), key="ca_to")
    cancelled = order_service.list_orders(
        start.isoformat(), end.isoformat(), status="cancelled")
    if not cancelled:
        st.info("No cancelled online orders in this range.")
    else:
        df = pd.DataFrame([{
            "Order #": o["id"],
            "Date": o["order_date"],
            "Customer": o["customer_name"],
            "Phone": o["customer_phone"],
            "Total": fmt_inr(o["total_amount"]),
            "Cancelled at": o["cancelled_at"] or "",
            "Cancelled by": o["cancelled_by_name"] or "",
            "Reason": o["cancel_reason"] or "",
        } for o in cancelled])
        st.dataframe(df, hide_index=True, width="stretch")

        sel = st.selectbox("View order #", [o["id"] for o in cancelled], key="cancelled_sel")
        order = next(o for o in cancelled if o["id"] == sel)
        _show_detail(order)
