import streamlit as st
from src.database import init_db
from src.ui import dashboard, projections, reconciliation

# Initialize database
init_db()

st.set_page_config(page_title="Cashflow Dashboard", layout="wide")

st.title("Cashflow Management Dashboard")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Projections", "Reconciliation", "Settings"])

if page == "Dashboard":
    dashboard.render()
elif page == "Projections":
    projections.render()
elif page == "Reconciliation":
    reconciliation.render()
elif page == "Settings":
    st.header("Settings")
    st.write("Configuration options will go here.")
