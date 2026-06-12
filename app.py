"""Entry point: startup (migrate + seed), login gate, role-based navigation."""

import streamlit as st

from db import database
from services import auth_service

USER_GUIDE = st.Page("pages/12_User_Guide.py", title="User Guide", icon="📖")

st.set_page_config(
    page_title="Sanskrit Sahitya Ratnakar",
    layout="wide",
)


@st.cache_resource
def _startup() -> bool:
    conn = database.init_db()
    conn.close()
    try:
        from utils import backup

        backup.backup_if_needed()
    except ImportError:
        pass  # backup module arrives in a later milestone
    return True


_startup()


def change_password_page() -> None:
    user = st.session_state.user
    st.title("Change your password")
    st.info("You must set a new password before continuing (first login or after a reset).")
    with st.form("change_pw_form"):
        new_pw = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Set password", type="primary")
    if submitted:
        if len(new_pw) < 6:
            st.error("Password must be at least 6 characters.")
        elif new_pw != confirm:
            st.error("Passwords do not match.")
        elif new_pw == database.DEFAULT_PASSWORD:
            st.error("Please choose a password different from the default one.")
        else:
            auth_service.change_password(user["id"], new_pw)
            st.session_state.user = {**user, "must_change_pw": False}
            st.success("Password updated.")
            st.rerun()


user = st.session_state.get("user")

if user is None:
    nav = st.navigation([
        st.Page("pages/10_Order_Books.py", title="Order Books", default=True),
        st.Page("pages/0_Staff_Login.py", title="Staff Login"),
        USER_GUIDE,
    ])
elif user["must_change_pw"]:
    nav = st.navigation([
        st.Page(change_password_page, title="Change Password"),
        USER_GUIDE,
    ])
else:
    pages = [
        st.Page("pages/1_Dashboard.py", title="Dashboard", default=True),
        st.Page("pages/2_Books.py", title="Books"),
        st.Page("pages/3_Purchases.py", title="Purchases"),
        st.Page("pages/4_Sales.py", title="Sales"),
        st.Page("pages/5_Inventory.py", title="Inventory"),
        st.Page("pages/6_Reports.py", title="Reports"),
        st.Page("pages/9_Analytics.py", title="Analytics"),
        st.Page("pages/7_Contacts.py", title="Contacts"),
        st.Page("pages/11_Online_Orders.py", title="Online Orders"),
    ]
    if user["role"] == "owner":
        pages.append(st.Page("pages/8_Users.py", title="Users"))
    pages.append(USER_GUIDE)
    with st.sidebar:
        st.markdown(f"**{user['full_name']}**  \n_{user['role'].capitalize()}_")
        if st.button("Log out"):
            auth_service.logout()
            st.rerun()
    nav = st.navigation(pages)

nav.run()
