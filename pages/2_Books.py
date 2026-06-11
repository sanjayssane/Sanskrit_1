"""Book catalog: search (both scripts), add with duplicate warning, edit, deactivate."""

import pandas as pd
import streamlit as st

from services import auth_service, book_service
from utils.money import fmt_inr, to_paise, to_rupees

user = auth_service.require_login()
is_owner = user["role"] == "owner"

st.title("Book Catalog")

CATEGORIES = ["", "Veda", "Purana", "Kavya", "Vyakarana", "Darshana", "Textbook", "Other"]
LANGUAGES = ["", "Sanskrit", "Sanskrit-Hindi", "Sanskrit-English", "Other"]


def book_form(key: str, initial: dict | None = None) -> dict | None:
    """Render the add/edit form; return the field dict on submit, else None."""
    b = initial or {}
    with st.form(key):
        col1, col2 = st.columns(2)
        with col1:
            title_dev = st.text_input("Title (Devanagari) *", b.get("title_devanagari", ""))
            author_dev = st.text_input("Author (Devanagari)", b.get("author_devanagari") or "")
            publisher = st.text_input("Publisher", b.get("publisher") or "")
            language = st.selectbox(
                "Language", LANGUAGES,
                index=LANGUAGES.index(b.get("language")) if b.get("language") in LANGUAGES else 0)
            retail = st.number_input(
                "Retail price (₹) *", min_value=0.0, step=1.0, format="%.2f",
                value=to_rupees(b.get("retail_price", 0)))
        with col2:
            title_roman = st.text_input("Title (Roman) *", b.get("title_roman", ""))
            author_roman = st.text_input("Author (Roman)", b.get("author_roman") or "")
            category = st.selectbox(
                "Category", CATEGORIES,
                index=CATEGORIES.index(b.get("category")) if b.get("category") in CATEGORIES else 0)
            isbn = st.text_input("ISBN (optional)", b.get("isbn") or "")
            wholesale = st.number_input(
                "Wholesale price (₹) *", min_value=0.0, step=1.0, format="%.2f",
                value=to_rupees(b.get("wholesale_price", 0)))
        threshold = st.number_input(
            "Low-stock threshold", min_value=0, step=1,
            value=int(b.get("low_stock_threshold", 5)))
        ignore_dup = st.checkbox(
            "Ignore duplicate warning and save anyway", key=f"{key}_ignore_dup")
        submitted = st.form_submit_button("Save book", type="primary")

    if not submitted:
        return None
    if not title_dev.strip() or not title_roman.strip():
        st.error("Both Devanagari and Roman titles are required.")
        return None
    fields = {
        "title_devanagari": title_dev.strip(),
        "title_roman": title_roman.strip(),
        "author_devanagari": author_dev.strip() or None,
        "author_roman": author_roman.strip() or None,
        "publisher": publisher.strip() or None,
        "category": category or None,
        "language": language or None,
        "isbn": isbn.strip() or None,
        "retail_price": to_paise(retail),
        "wholesale_price": to_paise(wholesale),
        "low_stock_threshold": int(threshold),
    }
    fields["_ignore_dup"] = ignore_dup
    return fields


tab_list, tab_add, tab_edit = st.tabs(["Catalog", "Add book", "Edit book"])

with tab_list:
    col_search, col_inactive = st.columns([4, 1])
    term = col_search.text_input(
        "Search (Roman or Devanagari title, author, or code)", key="book_search")
    include_inactive = col_inactive.checkbox("Show deactivated", value=False)
    books = book_service.search_books(term, include_inactive=include_inactive)
    if not books:
        st.info("No books found.")
    else:
        df = pd.DataFrame(books)
        df["retail"] = df["retail_price"].map(fmt_inr)
        df["wholesale"] = df["wholesale_price"].map(fmt_inr)
        df["status"] = df["is_active"].map({1: "Active", 0: "Deactivated"})
        st.dataframe(
            df[["code", "title_devanagari", "title_roman", "author_roman", "publisher",
                "category", "language", "isbn", "retail", "wholesale",
                "low_stock_threshold", "status"]],
            hide_index=True, width="stretch")
        st.caption(f"{len(books)} book(s)")

with tab_add:
    fields = book_form("add_book_form")
    if fields is not None:
        ignore_dup = fields.pop("_ignore_dup")
        dups = book_service.find_duplicates(
            fields["title_roman"], fields["title_devanagari"], fields["publisher"])
        if dups and not ignore_dup:
            st.warning(
                "A book with the same title and publisher already exists: "
                + ", ".join(f"{d['code']} ({d['title_roman']})" for d in dups)
                + ". Tick 'Ignore duplicate warning' to save anyway.")
        else:
            book_id = book_service.add_book(fields)
            book = book_service.get_book(book_id)
            st.success(f"Book saved with code {book['code']}.")

with tab_edit:
    all_books = book_service.search_books("", include_inactive=True)
    if not all_books:
        st.info("No books in the catalog yet.")
    else:
        labels = {f"{b['code']} — {b['title_roman']} / {b['title_devanagari']}": b
                  for b in all_books}
        selected_label = st.selectbox("Select book", list(labels))
        selected = labels[selected_label]

        fields = book_form("edit_book_form", initial=selected)
        if fields is not None:
            ignore_dup = fields.pop("_ignore_dup")
            dups = book_service.find_duplicates(
                fields["title_roman"], fields["title_devanagari"], fields["publisher"],
                exclude_id=selected["id"])
            if dups and not ignore_dup:
                st.warning(
                    "Another book with the same title and publisher exists: "
                    + ", ".join(f"{d['code']} ({d['title_roman']})" for d in dups)
                    + ". Tick 'Ignore duplicate warning' to save anyway.")
            else:
                book_service.update_book(selected["id"], fields)
                st.success("Book updated.")
                st.rerun()

        if is_owner:
            st.divider()
            if selected["is_active"]:
                if st.button("Deactivate this book (hidden from sale screens)"):
                    book_service.set_active(selected["id"], False)
                    st.success("Book deactivated.")
                    st.rerun()
            else:
                if st.button("Reactivate this book"):
                    book_service.set_active(selected["id"], True)
                    st.success("Book reactivated.")
                    st.rerun()
