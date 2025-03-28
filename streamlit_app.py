import streamlit as st
import pandas as pd
from pathlib import Path

# -------------------------------
# Customer login setup
# -------------------------------
USERS = {
    "covalon@client.com": {"password": "demo123", "customer": "Covalon Technologies Inc"},
    "biyork@client.com": {"password": "demo123", "customer": "Biyork"},
    "pdrtools@client.com": {"password": "demo123", "customer": "PDR Tools Canada"},
    "aspen@client.com": {"password": "demo123", "customer": "Aspen Clean"},
    "santova@client.com": {"password": "demo123", "customer": "Santova Logistics"},
}

def login():
    st.title("📦 Freight Dashboard Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in USERS and USERS[email]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.session_state.customer = USERS[email]["customer"]
            st.rerun()
        else:
            st.error("Invalid email or password.")

# -------------------------------
# Load and filter data
# -------------------------------
@st.cache_data
def load_data():
    path = Path(__file__).parent / "ShipWise - Rose Rocket Orders Table 2025-03-19.xlsx"
    df = pd.read_excel(path)
    df = df.drop_duplicates(subset="fullId")
    df["ETA_raw"] = df["expectedArrival__c.dateTimeInLocation"]
    df["ETA"] = pd.to_datetime(df["ETA_raw"], errors="coerce", utc=True)
    df = df[[
        "fullId", "status", "customer.name", "pickupCompanyName__c",
        "deliveryCompanyName__c", "deliveryZipPostal__c", "ETA"
    ]]
    df.columns = ["Order ID", "Status", "Customer", "Pickup", "Delivery", "Postal Code", "ETA"]
    return df

def customer_filter(df):
    return df[df["Customer"] == st.session_state.customer]

# -------------------------------
# App layout
# -------------------------------
def app():
    st.set_page_config(page_title="Freight Orders", layout="wide")

    for key in ["logged_in", "email", "customer"]:
        if key not in st.session_state:
            st.session_state[key] = None if key != "logged_in" else False

    if not st.session_state.logged_in:
        login()
        return

    # Logo
    st.sidebar.image("logo.png",  use_container_width=True)

    # Bottom login info block
    sidebar_footer = st.sidebar.empty()

    # Title
    st.title(f"📋 Orders for {st.session_state.customer}")

    # Load + filter
    df = load_data()
    df = customer_filter(df)

    if df.empty:
        st.warning("No orders found for your account.")
        return

    # Format Status values and build dropdown
    df["Status"] = (
        df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Create mapping from raw → title case
    status_title_map = {s: s.title() for s in df["Status"].unique()}
    status_options = ["All"] + sorted(status_title_map.values())
    selected_status_title = st.selectbox("Filter by Status", status_options)

    if selected_status_title != "All":
        selected_status_raw = [k for k, v in status_title_map.items() if v == selected_status_title][0]
        df = df[df["Status"] == selected_status_raw]

    # Sort by order ID numerically
    df["Order Num"] = df["Order ID"].str.extract(r"(\d+)").astype(int)
    df = df.sort_values("Order Num", ascending=False).drop(columns=["Order Num"])

    # Format ETA
    df["ETA"] = df["ETA"].dt.strftime("%Y-%m-%d %H:%M").fillna("N/A")

    for col in ["Status", "Customer", "Pickup", "Delivery", "Postal Code"]:
        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.title()
        )

    # Data table
    st.subheader("📄 Order Details")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

    # Sidebar footer: login state
    with sidebar_footer.container():
        st.markdown("---")
        st.success(f"Logged in as: {st.session_state.email}")
        if st.button("Logout", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

# Run the app
app()