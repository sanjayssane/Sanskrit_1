"""Owner-only user management: list, add, deactivate, reset passwords, delete (FR-1.3/1.4)."""

import pandas as pd
import streamlit as st

from services import auth_service

owner = auth_service.require_owner()

st.title("User Management")

users = auth_service.list_users()
df = pd.DataFrame(users)
df["status"] = df["is_active"].map({1: "Active", 0: "Deactivated"})
df["pending password change"] = df["must_change_pw"].map({1: "Yes", 0: "No"})
st.dataframe(
    df[["id", "username", "full_name", "role", "status", "pending password change", "created_at"]],
    hide_index=True,
    width="stretch",
)

tab_add, tab_manage = st.tabs(["Add user", "Manage existing user"])

with tab_add:
    with st.form("add_user_form", clear_on_submit=True):
        username = st.text_input("Username")
        full_name = st.text_input("Full name")
        role = st.selectbox("Role", ["employee", "owner"], index=0)
        initial_pw = st.text_input("Initial password", type="password")
        submitted = st.form_submit_button("Create user", type="primary")
    if submitted:
        if not username.strip() or not full_name.strip():
            st.error("Username and full name are required.")
        elif len(initial_pw) < 6:
            st.error("Initial password must be at least 6 characters.")
        else:
            try:
                auth_service.create_user(username, full_name, initial_pw, role)
                st.success(
                    f"User '{username}' created. They must change the password on first login."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

with tab_manage:
    others = [u for u in users if u["id"] != owner["id"]]
    if not others:
        st.info("No other users to manage.")
    else:
        labels = {f"{u['username']} — {u['full_name']}": u for u in others}
        selected_label = st.selectbox("Select user", list(labels))
        selected = labels[selected_label]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Account status**")
            if selected["is_active"]:
                if st.button("Deactivate account"):
                    auth_service.set_active(selected["id"], False)
                    st.success(f"'{selected['username']}' deactivated. Past records stay intact.")
                    st.rerun()
            else:
                if st.button("Reactivate account"):
                    auth_service.set_active(selected["id"], True)
                    st.success(f"'{selected['username']}' reactivated.")
                    st.rerun()
        with col2:
            st.markdown("**Reset password**")
            with st.form("reset_pw_form"):
                new_pw = st.text_input("New temporary password", type="password")
                ok = st.form_submit_button("Reset password")
            if ok:
                if len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    auth_service.reset_password(selected["id"], new_pw)
                    st.success(
                        f"Password reset. '{selected['username']}' must change it at next login."
                    )

        st.divider()
        st.markdown("**Delete user permanently**")
        block = auth_service.delete_block_reason(selected["id"], owner["id"])
        if block:
            st.info(block)
        else:
            st.caption(
                "Only users with no purchase, sale, or adjustment records can be deleted. "
                "For staff who have worked in the system, use Deactivate instead."
            )
            confirm = st.checkbox(
                f"I understand — permanently delete '{selected['username']}'",
                key=f"delete_confirm_{selected['id']}")
            if st.button("Delete user", type="primary", disabled=not confirm):
                try:
                    auth_service.delete_user(selected["id"], owner["id"])
                    st.success(f"User '{selected['username']}' deleted.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
