"""Suppliers and wholesale customers: list, add, edit, deactivate (FR-3)."""

import pandas as pd
import streamlit as st

from services import auth_service, contact_service

auth_service.require_login()

st.title("Contacts")

KIND_LABELS = {"supplier": "Suppliers (publishers/wholesalers)",
               "customer": "Wholesale customers"}


def contact_section(kind: str) -> None:
    include_inactive = st.checkbox("Show deactivated", key=f"{kind}_inactive")
    contacts = contact_service.list_contacts(kind, include_inactive=include_inactive)

    if contacts:
        df = pd.DataFrame(contacts)
        df["status"] = df["is_active"].map({1: "Active", 0: "Deactivated"})
        st.dataframe(
            df[["name", "contact_person", "phone", "address", "notes", "status"]],
            hide_index=True, width="stretch")
    else:
        st.info("No entries yet.")

    with st.expander("Add new"):
        with st.form(f"add_{kind}", clear_on_submit=True):
            name = st.text_input("Name *")
            contact_person = st.text_input("Contact person")
            phone = st.text_input("Phone")
            address = st.text_area("Address")
            notes = st.text_area("Notes")
            ok = st.form_submit_button("Add", type="primary")
        if ok:
            if not name.strip():
                st.error("Name is required.")
            else:
                contact_service.add_contact(kind, {
                    "name": name.strip(),
                    "contact_person": contact_person.strip() or None,
                    "phone": phone.strip() or None,
                    "address": address.strip() or None,
                    "notes": notes.strip() or None,
                })
                st.success(f"{name} added.")
                st.rerun()

    if contacts:
        with st.expander("Edit / deactivate"):
            labels = {f"{c['name']} (#{c['id']})": c for c in contacts}
            selected = labels[st.selectbox("Select", list(labels), key=f"sel_{kind}")]
            with st.form(f"edit_{kind}"):
                name = st.text_input("Name *", selected["name"])
                contact_person = st.text_input("Contact person", selected["contact_person"] or "")
                phone = st.text_input("Phone", selected["phone"] or "")
                address = st.text_area("Address", selected["address"] or "")
                notes = st.text_area("Notes", selected["notes"] or "")
                ok = st.form_submit_button("Save changes", type="primary")
            if ok:
                if not name.strip():
                    st.error("Name is required.")
                else:
                    contact_service.update_contact(kind, selected["id"], {
                        "name": name.strip(),
                        "contact_person": contact_person.strip() or None,
                        "phone": phone.strip() or None,
                        "address": address.strip() or None,
                        "notes": notes.strip() or None,
                    })
                    st.success("Saved.")
                    st.rerun()
            if selected["is_active"]:
                if st.button("Deactivate", key=f"deact_{kind}"):
                    contact_service.set_active(kind, selected["id"], False)
                    st.rerun()
            else:
                if st.button("Reactivate", key=f"react_{kind}"):
                    contact_service.set_active(kind, selected["id"], True)
                    st.rerun()


tab_sup, tab_cust = st.tabs(list(KIND_LABELS.values()))
with tab_sup:
    contact_section("supplier")
with tab_cust:
    contact_section("customer")
