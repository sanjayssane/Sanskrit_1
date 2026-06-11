"""Sales: retail/wholesale entry with stock check + receipt PDF, history (FR-5)."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import auth_service, book_service, contact_service, sale_service
from services.sale_service import InsufficientStockError
from utils import receipt_pdf
from utils.money import fmt_inr, to_paise, to_rupees

user = auth_service.require_login()
is_owner = user["role"] == "owner"

st.title("Sales")

tab_new, tab_history = st.tabs(["New sale", "History"])


def receipt_download(sale_id: int, key: str) -> None:
    sale = sale_service.get_sale(sale_id)
    items = sale_service.get_sale_items(sale_id)
    st.download_button(
        f"Download receipt #{sale_id} (PDF)",
        data=receipt_pdf.build_receipt_pdf(sale, items),
        file_name=f"receipt-{sale_id}.pdf",
        mime="application/pdf",
        key=key)


# --- New sale ----------------------------------------------------------------

with tab_new:
    books = book_service.list_active_books()
    customers = contact_service.list_contacts("customer")

    if not books:
        st.warning("Add books to the catalog first.")
    else:
        sale_type = st.radio("Sale type", ["retail", "wholesale"], horizontal=True,
                             format_func=str.capitalize)

        customer = None
        if sale_type == "wholesale":
            if not customers:
                st.warning("Add a wholesale customer on the Contacts page first.")
                st.stop()
            customer_labels = {c["name"]: c for c in customers}
            customer = customer_labels[st.selectbox("Customer *", list(customer_labels))]

        cart_key = "sale_cart"
        cart = st.session_state.setdefault(cart_key, [])

        book_labels = {
            f"{b['code']} — {b['title_roman']} / {b['title_devanagari']} (stock: {b['stock']})": b
            for b in books}

        st.markdown("**Add line item** (price auto-fills from the catalog, editable)")
        c1, c2 = st.columns([3, 1])
        picked = book_labels[c1.selectbox("Book", list(book_labels))]
        default_price = picked["retail_price"] if sale_type == "retail" else picked["wholesale_price"]
        qty = c2.number_input("Quantity", min_value=1, step=1, value=1)
        price = st.number_input(
            "Unit price (₹)", min_value=0.0, step=1.0, format="%.2f",
            value=to_rupees(default_price),
            key=f"price_{picked['id']}_{sale_type}")
        if st.button("Add to sale"):
            cart.append({
                "book_id": picked["id"],
                "label": f"{picked['code']} — {picked['title_roman']}",
                "quantity": int(qty),
                "unit_price": to_paise(price),
            })
            st.rerun()

        if cart:
            df = pd.DataFrame([{
                "Book": line["label"],
                "Qty": line["quantity"],
                "Unit price": fmt_inr(line["unit_price"]),
                "Line total": fmt_inr(line["quantity"] * line["unit_price"]),
            } for line in cart])
            st.dataframe(df, hide_index=True, width="stretch")

            remove_idx = st.selectbox(
                "Remove a line", ["—"] + [f"{i + 1}. {l['label']}" for i, l in enumerate(cart)])
            if remove_idx != "—" and st.button("Remove selected line"):
                cart.pop(int(remove_idx.split(".")[0]) - 1)
                st.rerun()

            subtotal = sum(l["quantity"] * l["unit_price"] for l in cart)
            c1, c2, c3 = st.columns(3)
            sale_date = c1.date_input("Sale date", dt.date.today())
            discount = c2.number_input(
                "Discount on bill (₹)", min_value=0.0,
                max_value=to_rupees(subtotal), step=1.0, format="%.2f")
            payment = c3.selectbox("Payment method", list(sale_service.PAYMENT_METHODS),
                                   format_func=str.upper)
            notes = st.text_area("Notes (optional)", key="sale_notes")

            st.subheader(f"Subtotal: {fmt_inr(subtotal)} — "
                         f"Total: {fmt_inr(subtotal - to_paise(discount))}")

            if st.button("Save sale", type="primary"):
                try:
                    sale_id = sale_service.create_sale(
                        sale_date.isoformat(), sale_type,
                        [{k: l[k] for k in ("book_id", "quantity", "unit_price")}
                         for l in cart],
                        user["id"],
                        customer_id=customer["id"] if customer else None,
                        discount=to_paise(discount),
                        payment_method=payment,
                        notes=notes.strip() or None)
                    st.session_state[cart_key] = []
                    st.session_state["last_sale_id"] = sale_id
                    st.rerun()
                except InsufficientStockError as exc:
                    st.error(str(exc))
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.info("Add at least one line item.")

        if st.session_state.get("last_sale_id"):
            st.success(f"Sale #{st.session_state['last_sale_id']} saved — stock updated.")
            receipt_download(st.session_state["last_sale_id"], key="receipt_new")

# --- History -------------------------------------------------------------------

with tab_history:
    customers_all = contact_service.list_contacts("customer", include_inactive=True)
    books_all = book_service.search_books("", include_inactive=True)
    users_all = auth_service.list_users()

    c1, c2, c3 = st.columns(3)
    start = c1.date_input("From", dt.date.today() - dt.timedelta(days=30), key="sh_from")
    end = c2.date_input("To", dt.date.today(), key="sh_to")
    type_filter = c3.selectbox("Type", ["All", "retail", "wholesale"], format_func=str.capitalize)

    c4, c5, c6 = st.columns(3)
    cust_filter = c4.selectbox("Customer", ["All"] + [c["name"] for c in customers_all])
    book_filter = c5.selectbox(
        "Book", ["All"] + [f"{b['code']} — {b['title_roman']}" for b in books_all],
        key="sh_book")
    user_filter = c6.selectbox("Recorded by", ["All"] + [u["username"] for u in users_all])

    sales = sale_service.list_sales(
        start.isoformat(), end.isoformat(),
        sale_type=None if type_filter == "All" else type_filter,
        customer_id=next((c["id"] for c in customers_all if c["name"] == cust_filter), None),
        book_id=next((b["id"] for b in books_all
                      if f"{b['code']} — {b['title_roman']}" == book_filter), None),
        user_id=next((u["id"] for u in users_all if u["username"] == user_filter), None))

    if not sales:
        st.info("No sales in the selected range.")
    else:
        df = pd.DataFrame([{
            "ID": s["id"],
            "Date": s["sale_date"],
            "Type": s["sale_type"],
            "Customer": s["customer_name"] or "(walk-in)",
            "Lines": s["line_count"],
            "Qty": s["total_qty"],
            "Discount": fmt_inr(s["discount"]),
            "Total": fmt_inr(s["total_amount"]),
            "Payment": s["payment_method"].upper(),
            "By": s["created_by_name"],
            "Status": "CANCELLED" if s["is_cancelled"] else "OK",
        } for s in sales])
        st.dataframe(df, hide_index=True, width="stretch")

        detail_id = st.selectbox("View details of sale #", [s["id"] for s in sales])
        detail = next(s for s in sales if s["id"] == detail_id)
        items = sale_service.get_sale_items(detail_id)
        st.dataframe(pd.DataFrame([{
            "Book": f"{i['code']} — {i['title_roman']} / {i['title_devanagari']}",
            "Qty": i["quantity"],
            "Unit price": fmt_inr(i["unit_price"]),
            "Line total": fmt_inr(i["line_total"]),
        } for i in items]), hide_index=True, width="stretch")

        receipt_download(detail_id, key="receipt_history")

        if detail["is_cancelled"]:
            st.error(f"Cancelled — reason: {detail['cancel_reason']}")
        elif is_owner:
            with st.form("cancel_sale"):
                reason = st.text_input("Cancellation reason (required)")
                ok = st.form_submit_button("Cancel this sale")
            if ok:
                try:
                    sale_service.cancel_sale(detail_id, user["id"], reason)
                    st.success("Sale cancelled — stock restored.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
