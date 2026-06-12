"""Public guest ordering: browse in-stock books and place orders (no login)."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import book_service, order_service
from services.sale_service import InsufficientStockError
from utils.money import fmt_inr

SHOP_TITLE = "संस्कृत साहित्य रत्नाकर — Sanskrit Sahitya Ratnakar"

st.title(SHOP_TITLE)
st.subheader("Order Books Online")
st.caption("Browse our catalog and place an order. We will contact you to confirm pickup.")

if st.session_state.get("order_confirmed_id"):
    oid = st.session_state.pop("order_confirmed_id")
    st.success(
        f"Thank you! Your order **#{oid}** has been received. "
        "Our shop will contact you shortly to arrange pickup."
    )

search = st.text_input("Search books", placeholder="Title, author, or code in Devanagari or Roman")

books = book_service.list_active_books()
if search.strip():
    ids = {b["id"] for b in book_service.search_books(search)}
    books = [b for b in books if b["id"] in ids]

in_stock = [b for b in books if b["stock"] > 0]

cart_key = "order_cart"
cart = st.session_state.setdefault(cart_key, [])

tab_browse, tab_cart = st.tabs(["Browse catalog", f"Your cart ({len(cart)})"])

with tab_browse:
    if not in_stock:
        st.info("No books currently in stock matching your search.")
    else:
        df = pd.DataFrame([{
            "Code": b["code"],
            "Title (Roman)": b["title_roman"],
            "Title (Devanagari)": b["title_devanagari"],
            "Author": b["author_roman"] or "",
            "Price": fmt_inr(b["retail_price"]),
            "In stock": b["stock"],
        } for b in in_stock])
        st.dataframe(df, hide_index=True, width="stretch")

        book_labels = {
            f"{b['code']} — {b['title_roman']} / {b['title_devanagari']} "
            f"(₹{b['retail_price'] / 100:.2f}, stock: {b['stock']})": b
            for b in in_stock
        }
        st.markdown("**Add to cart**")
        c1, c2 = st.columns([3, 1])
        picked = book_labels[c1.selectbox("Book", list(book_labels), key="pick_book")]
        max_qty = picked["stock"]
        in_cart = sum(l["quantity"] for l in cart if l["book_id"] == picked["id"])
        available = max(0, max_qty - in_cart)
        if available == 0:
            st.warning("This book is already at maximum quantity in your cart.")
        else:
            qty = c2.number_input("Quantity", min_value=1, max_value=available,
                                  step=1, value=1, key="pick_qty")
            if st.button("Add to cart"):
                existing = next((l for l in cart if l["book_id"] == picked["id"]), None)
                if existing:
                    existing["quantity"] += int(qty)
                else:
                    cart.append({
                        "book_id": picked["id"],
                        "label": f"{picked['code']} — {picked['title_roman']}",
                        "quantity": int(qty),
                        "unit_price": picked["retail_price"],
                        "max_stock": picked["stock"],
                    })
                st.rerun()

with tab_cart:
    if not cart:
        st.info("Your cart is empty. Browse the catalog to add books.")
    else:
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
        st.subheader(f"Order total: {fmt_inr(subtotal)}")

        st.markdown("**Your contact details**")
        with st.form("checkout_form"):
            name = st.text_input("Full name *")
            phone = st.text_input("Phone *")
            email = st.text_input("Email (optional)")
            notes = st.text_area("Notes (optional)", placeholder="Pickup preferences, etc.")
            submitted = st.form_submit_button("Place order", type="primary")

        if submitted:
            try:
                order_id = order_service.create_order(
                    dt.date.today().isoformat(),
                    name, phone,
                    [{k: l[k] for k in ("book_id", "quantity", "unit_price")} for l in cart],
                    customer_email=email.strip() or None,
                    notes=notes.strip() or None,
                )
                st.session_state[cart_key] = []
                st.session_state["order_confirmed_id"] = order_id
                st.rerun()
            except InsufficientStockError as exc:
                st.error(str(exc))
            except ValueError as exc:
                st.error(str(exc))

st.divider()
st.caption("Staff: use **Staff Login** in the sidebar to manage orders.")
