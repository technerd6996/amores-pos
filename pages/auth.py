import streamlit as st
from db import get_client, get_admin_client

_EMAIL_MAP = {
    "Shop 1": "shop1@amores.local",
    "Shop 2": "shop02@amores.loca",
    "Shop 3": "shop03@amores.loca",
    "Admin": "shopowner@amores.local",
}

def login():
    if "user" in st.session_state:
        return st.session_state["user"]

    st.title("Sundae Dashboard Login")
    label = st.selectbox("Login as", list(_EMAIL_MAP.keys()))
    pin = st.text_input("8-character PIN", type="password", max_chars=8)

    if st.button("Login"):
        try:
            res = get_client().auth.sign_in_with_password(
                {"email": _EMAIL_MAP[label], "password": pin}
            )
        except Exception:
            st.error("Invalid PIN")
            return None

        profile = get_client().table("profiles").select("*").eq("id", res.user.id).single().execute()
        st.session_state["user"] = {
            "id": res.user.id,
            "role": profile.data["role"],
            "shop_id": profile.data["shop_id"],
        }
        st.rerun()
    return None

def logout():
    st.session_state.pop("user", None)
    st.rerun()

def reset_pin(target_user_id: str, new_pin: str):
    """Call only after confirming the caller's role == 'admin'."""
    if len(new_pin) != 8:
        raise ValueError("PIN must be exactly 8 characters")
    get_admin_client().auth.admin.update_user_by_id(target_user_id, {"password": new_pin})