"""Purchases: new purchase entry (multi-line, atomic) + filterable history (FR-4)."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import auth_service, book_service, contact_service, purchase_service
from utils.money import fmt_inr, to_paise, to_rupees

user = auth_service.require_login()
is_owner = user["role"] == "owner"

st.title("Purchases")

tab_new, tab_history = st.tabs(["New purchase", "History"])

# --- New purchase -----------------------------------------------------------

with tab_new:
    suppliers = contact_service.list_contacts("supplier")
    books = book_service.list_active_books()

    if not suppliers:
        st.warning("Add a supplier on the Contacts page first.")
    elif not books:
        st.warning("Add books to the catalog first.")
    else:
        cart = st.session_state.setdefault("purchase_cart", [])

        supplier_labels = {s["name"]: s for s in suppliers}
        book_labels = {f"{b['code']} — {b['title_roman']} / {b['title_devanagari']}": b
                       for b in books}

        col1, col2, col3 = st.columns(3)
        supplier = supplier_labels[col1.selectbox("Supplier *", list(supplier_labels))]
        purchase_date = col2.date_input("Purchase date", dt.date.today())
        invoice_ref = col3.text_input("Invoice / bill reference (optional)")

        st.markdown("**Add line item**")
        with st.form("add_purchase_line", clear_on_submit=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            book = book_labels[c1.selectbox("Book", list(book_labels))]
            qty = c2.number_input("Quantity", min_value=1, step=1, value=1)
            price = c3.number_input("Unit cost (₹)", min_value=0.0, step=1.0, format="%.2f")
            added = st.form_submit_button("Add to purchase")
        if added:
            cart.append({
                "book_id": book["id"],
                "label": f"{book['code']} — {book['title_roman']}",
                "quantity": int(qty),
                "unit_price": to_paise(price),
            })
            st.rerun()

        if cart:
            df = pd.DataFrame([{
                "Book": line["label"],
                "Qty": line["quantity"],
                "Unit cost": fmt_inr(line["unit_price"]),
                "Line total": fmt_inr(line["quantity"] * line["unit_price"]),
            } for line in cart])
            st.dataframe(df, hide_index=True, width="stretch")

            remove_idx = st.selectbox(
                "Remove a line", ["—"] + [f"{i + 1}. {l['label']}" for i, l in enumerate(cart)])
            if remove_idx != "—" and st.button("Remove selected line"):
                cart.pop(int(remove_idx.split(".")[0]) - 1)
                st.rerun()

            total = sum(l["quantity"] * l["unit_price"] for l in cart)
            st.subheader(f"Total: {fmt_inr(total)}")

            notes = st.text_area("Notes (optional)", key="purchase_notes")
            if st.button("Save purchase", type="primary"):
                try:
                    purchase_id = purchase_service.create_purchase(
                        purchase_date.isoformat(), supplier["id"],
                        [{k: l[k] for k in ("book_id", "quantity", "unit_price")}
                         for l in cart],
                        user["id"], invoice_ref.strip() or None, notes.strip() or None)
                    st.session_state["purchase_cart"] = []
                    st.success(f"Purchase #{purchase_id} saved — stock updated.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.info("Add at least one line item.")

# --- History ----------------------------------------------------------------

with tab_history:
    suppliers_all = contact_service.list_contacts("supplier", include_inactive=True)
    books_all = book_service.search_books("", include_inactive=True)

    c1, c2, c3, c4 = st.columns(4)
    start = c1.date_input("From", dt.date.today() - dt.timedelta(days=30), key="ph_from")
    end = c2.date_input("To", dt.date.today(), key="ph_to")
    sup_filter = c3.selectbox("Supplier", ["All"] + [s["name"] for s in suppliers_all])
    book_filter = c4.selectbox(
        "Book", ["All"] + [f"{b['code']} — {b['title_roman']}" for b in books_all])

    sup_id = next((s["id"] for s in suppliers_all if s["name"] == sup_filter), None)
    book_id = next((b["id"] for b in books_all
                    if f"{b['code']} — {b['title_roman']}" == book_filter), None)

    purchases = purchase_service.list_purchases(
        start.isoformat(), end.isoformat(), sup_id, book_id)

    if not purchases:
        st.info("No purchases in the selected range.")
    else:
        df = pd.DataFrame([{
            "ID": p["id"],
            "Date": p["purchase_date"],
            "Supplier": p["supplier_name"],
            "Invoice": p["invoice_ref"] or "",
            "Lines": p["line_count"],
            "Qty": p["total_qty"],
            "Total": fmt_inr(p["total_amount"]),
            "By": p["created_by_name"],
            "Status": "CANCELLED" if p["is_cancelled"] else "OK",
        } for p in purchases])
        st.dataframe(df, hide_index=True, width="stretch")

        ids = [p["id"] for p in purchases]
        detail_id = st.selectbox("View details of purchase #", ids)
        detail = next(p for p in purchases if p["id"] == detail_id)
        items = purchase_service.get_purchase_items(detail_id)
        st.dataframe(pd.DataFrame([{
            "Book": f"{i['code']} — {i['title_roman']} / {i['title_devanagari']}",
            "Qty": i["quantity"],
            "Unit cost": fmt_inr(i["unit_price"]),
            "Line total": fmt_inr(i["line_total"]),
        } for i in items]), hide_index=True, width="stretch")
        if detail["is_cancelled"]:
            st.error(f"Cancelled — reason: {detail['cancel_reason']}")
        elif is_owner:
            with st.form("cancel_purchase"):
                reason = st.text_input("Cancellation reason (required)")
                ok = st.form_submit_button("Cancel this purchase")
            if ok:
                try:
                    purchase_service.cancel_purchase(detail_id, user["id"], reason)
                    st.success("Purchase cancelled — stock reversed.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
