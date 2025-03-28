import streamlit as st
import pandas as pd
import altair as alt
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
    df["ETA"] = pd.to_datetime(df["expectedArrival__c.dateTimeInLocation"], errors="coerce", utc=True)
    df["ETA Display"] = df["ETA"].dt.strftime("%Y-%m-%d %H:%M").fillna("N/A")
    df = df[[
        "fullId", "status", "customer.name", "pickupCompanyName__c",
        "deliveryCompanyName__c", "deliveryZipPostal__c", "ETA", "ETA Display"
    ]]
    df.columns = ["Order ID", "Status", "Customer", "Pickup", "Delivery", "Postal Code", "ETA", "ETA Display"]
    return df

def customer_filter(df):
    return df[df["Customer"] == st.session_state.customer]

# -------------------------------
# Altair chart with rounded bars
# -------------------------------
def plot_bar(data, x_label, y_label):
    df = data.reset_index()
    df.columns = [x_label, y_label]

    chart = alt.Chart(df).mark_bar(
        cornerRadiusTopLeft=10,
        cornerRadiusTopRight=10
    ).encode(
        x=alt.X(f"{x_label}:N", sort='-y', axis=alt.Axis(labelAngle=-30)),
        y=alt.Y(f"{y_label}:Q", axis=alt.Axis(title=None)),
        color=alt.Color(f"{x_label}:N", legend=None),
        tooltip=[alt.Tooltip(f"{x_label}:N"), alt.Tooltip(f"{y_label}:Q")]
    ).properties(
        width='container',
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

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

    st.sidebar.image("logo.png", use_container_width=True)
    sidebar_footer = st.sidebar.empty()

    st.title(f"📋 Orders for {st.session_state.customer}")

    df = load_data()
    df = customer_filter(df)

    if df.empty:
        st.warning("No orders found for your account.")
        return

    # --- Filter by status (title case dropdown) ---
    df["Status"] = df["Status"].fillna("").astype(str).str.strip()
    status_title_map = {s: s.title() for s in df["Status"].unique()}
    status_options = ["All"] + sorted(status_title_map.values())
    selected_status_title = st.selectbox("Filter by Status", status_options)

    if selected_status_title != "All":
        selected_status_raw = [k for k, v in status_title_map.items() if v == selected_status_title][0]
        df = df[df["Status"] == selected_status_raw]

    # --- Sort and display table ---
    df["Order Num"] = df["Order ID"].str.extract(r"(\d+)").astype(int)
    df = df.sort_values("Order Num", ascending=False).drop(columns=["Order Num"])
    df["ETA"] = df["ETA Display"]
    df = df.drop(columns=["ETA Display"])

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("").astype(str).str.strip().str.lower().str.title()

    df.columns = [col.title() for col in df.columns]

    st.subheader("📄 Order Details")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

    # --- Chart selector ---
    st.subheader("📊 View Chart")
    chart_option = st.selectbox("Choose a chart to display", [
        "None", "Shipments by Status", "Top Delivery Companies", "Top Postal Codes"
    ])

    if chart_option == "Shipments by Status":
        plot_bar(df["Status"].value_counts(), "Status", "Count")
    elif chart_option == "Top Delivery Companies":
        plot_bar(df["Delivery"].value_counts().head(10), "Delivery", "Count")
    elif chart_option == "Top Postal Codes":
        plot_bar(df["Postal Code"].value_counts().head(10), "Postal Code", "Count")


    # --- Sidebar footer ---
    with sidebar_footer.container():
        st.markdown("---")
        st.success(f"Logged in as: {st.session_state.email}")
        if st.button("Logout", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

# Run the app
app()