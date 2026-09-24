import streamlit as st
import pandas as pd
import pytz
IST = pytz.timezone("Asia/Kolkata")
from datetime import date
from db import get_client

st.set_page_config(page_title="Dashboard", page_icon="📊")

user = st.session_state.get("user")
if not user:
    st.warning("Please log in from the main page first.")
    st.stop()
if user["role"] != "admin":
    st.error("Admin access only.")
    st.stop()

st.title("📊 Shop Performance Dashboard")

col1, col2 = st.columns(2)
start = col1.date_input("From", value=date.today())
end = col2.date_input("To", value=date.today())

client = get_client()

shops = client.table("shops").select("id,name").execute().data
shop_map = {s["id"]: s["name"] for s in shops}

start_utc = IST.localize(pd.Timestamp(start)).astimezone(pytz.UTC)
end_utc = IST.localize(pd.Timestamp(end) + pd.Timedelta(days=1)).astimezone(pytz.UTC)

bills = client.table("bills").select("id,shop_id,total,bill_no,created_at") \
    .gte("created_at", start_utc.isoformat()) \
    .lt("created_at", end_utc.isoformat()) \
    .execute().data
df = pd.DataFrame(bills)
if df.empty:
    st.info("No bills in this range.")
else:
    df["shop"] = df["shop_id"].map(shop_map)

    st.subheader("Sales by shop")
    sales_by_shop = df.groupby("shop")["total"].sum()
    c1, c2 = st.columns([2, 1])
    c1.bar_chart(sales_by_shop)
    c2.dataframe(sales_by_shop.rename("Total ₹"))

    st.subheader("Item-wise sales")
    lines = client.table("bill_lines").select("bill_id,item_name,qty,price") \
        .in_("bill_id", df["id"].tolist()).execute().data
    ldf = pd.DataFrame(lines)
    if not ldf.empty:
        ldf["revenue"] = ldf["qty"] * ldf["price"]
        item_totals = ldf.groupby("item_name").agg(qty=("qty", "sum"), revenue=("revenue", "sum"))
        st.bar_chart(item_totals["revenue"])
        st.dataframe(item_totals)

    df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_convert(IST).dt.strftime("%d %b %Y, %I:%M %p")
    st.subheader("Bills")
    st.dataframe(df[["bill_no", "shop", "total", "created_at"]].sort_values("created_at", ascending=False))


st.divider()
st.subheader("🍨 Manage items")

items = client.table("items").select("*").order("name").execute().data
idf = pd.DataFrame(items)
if not idf.empty:
    st.dataframe(idf[["id", "name", "variant", "price", "theme", "active"]])

with st.form("add_item_form"):
    st.write("Add new item")
    shop_options = {"(Shared — all shops)": None}
    shop_options.update({s["name"]: s["id"] for s in shops})
    target_shop_label = st.selectbox("Shop", list(shop_options.keys()))
    new_name = st.text_input("Name")
    new_variant = st.text_input("Variant", value="")
    new_price = st.number_input("Price", min_value=0.0, step=1.0)
    new_theme = st.text_input("Theme (CSS class, optional)", value="")
    if st.form_submit_button("Add item"):
        if not new_name:
            st.error("Name is required.")
        else:
            try:
                client.table("items").insert({
                    "name": new_name, "variant": new_variant,
                    "price": new_price, "theme": new_theme, "active": True,
                    "shop_id": shop_options[target_shop_label]
                }).execute()
                st.success(f"Added {new_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

if not idf.empty:
    st.write("Edit / activate / deactivate")
    target_item = st.selectbox("Item", idf["id"].tolist())
    current = idf[idf["id"] == target_item].iloc[0]

    with st.form("edit_item_form"):
        edit_name = st.text_input("Name", value=current["name"])
        edit_variant = st.text_input("Variant", value=current["variant"] or "")
        edit_price = st.number_input("Price", min_value=0.0, step=1.0, value=float(current["price"]))
        edit_theme = st.text_input("Theme", value=current["theme"] or "")
        if st.form_submit_button("Save changes"):
            client.table("items").update({
                "name": edit_name, "variant": edit_variant,
                "price": edit_price, "theme": edit_theme
            }).eq("id", target_item).execute()
            st.success("Updated")
            st.rerun()

    col_a, col_b = st.columns(2)
    if col_a.button("Deactivate" if current["active"] else "Reactivate"):
        client.table("items").update({"active": not bool(current["active"])}).eq("id", target_item).execute()
        st.rerun()

st.divider()
st.subheader("🔑 Reset shop PIN")

from auth import reset_pin

profiles = client.table("profiles").select("id,role,shop_id").execute().data
options = {}
for p in profiles:
    label = shop_map.get(p["shop_id"], "Admin") if p["role"] == "shop" else "Admin"
    options[label] = p["id"]

target_label = st.selectbox("Account", list(options.keys()))
new_pin = st.text_input("New 8-character PIN", max_chars=8, type="password")

if st.button("Reset PIN"):
    if len(new_pin) != 8:
        st.error("PIN must be exactly 8 characters.")
    else:
        try:
            reset_pin(options[target_label], new_pin)
            st.success(f"PIN reset for {target_label}.")
        except Exception as e:
            st.error(f"Failed: {e}")