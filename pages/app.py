import streamlit as st
from auth import login, logout

st.set_page_config(page_title="Sundae Dashboard", page_icon="🍦")

user = login()
if user is None:
    st.stop()

st.success(f"Logged in — role: {user['role']}, shop_id: {user['shop_id']}")
if st.button("Logout"):
    logout()