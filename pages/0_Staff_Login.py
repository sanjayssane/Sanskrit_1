"""Staff login page (owner and employee accounts)."""

import streamlit as st

from services import auth_service

SHOP_TITLE = "संस्कृत साहित्य रत्नाकर — Sanskrit Sahitya Ratnakar"

st.title(SHOP_TITLE)
st.subheader("Staff Login")
with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in", type="primary")
if submitted:
    user = auth_service.authenticate(username, password)
    if user is None:
        st.error("Invalid username or password, or account is deactivated.")
    else:
        st.session_state.user = user
        st.rerun()
