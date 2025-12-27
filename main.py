import streamlit as st
from streamlit_option_menu import option_menu
from src.database import init_db
from src.ui import dashboard, projections, reconciliation, settings, cashflow

# Initialize database
init_db()

st.set_page_config(
    page_title="Cashflow Dashboard",
    page_icon="💷",
    layout="wide"
)

# Modern sidebar navigation with icons
with st.sidebar:
    st.markdown("## 💷 Cashflow")
    st.markdown("---")
    
    page = option_menu(
        menu_title=None,
        options=["Dashboard", "Cashflow", "Projections", "Reconciliation", "Settings"],
        icons=["graph-up", "currency-pound", "calendar-event", "arrow-left-right", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#FF4B4B", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "2px 0",
                "padding": "10px 15px",
                "border-radius": "8px",
            },
            "nav-link-selected": {
                "background-color": "#FF4B4B",
                "color": "white",
            },
        }
    )

if page == "Dashboard":
    dashboard.render()
elif page == "Cashflow":
    cashflow.render()
elif page == "Projections":
    projections.render()
elif page == "Reconciliation":
    reconciliation.render()
elif page == "Settings":
    settings.render()
