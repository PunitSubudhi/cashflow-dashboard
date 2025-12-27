import os
import streamlit as st
from streamlit_option_menu import option_menu
from src.database import init_db
from src.ui import dashboard, projections, reconciliation, settings, cashflow

# Initialize database
init_db()

# Authentication configuration
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "password")


def check_password():
    """Returns True if the user has entered the correct password."""

    def login_form():
        """Display the login form."""
        st.markdown("## 🔐 Login")
        st.markdown("---")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if username == APP_USERNAME and password == APP_PASSWORD:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("😕 Invalid username or password")

    if st.session_state.get("authenticated"):
        return True

    login_form()
    return False


st.set_page_config(page_title="Cashflow Dashboard", page_icon="💷", layout="wide")

# Check authentication before showing the app
if not check_password():
    st.stop()

# Modern sidebar navigation with icons
with st.sidebar:
    st.markdown("## 💷 Cashflow")
    st.markdown("---")

    page = option_menu(
        menu_title=None,
        options=["Dashboard", "Cashflow", "Projections", "Reconciliation", "Settings"],
        icons=[
            "graph-up",
            "currency-pound",
            "calendar-event",
            "arrow-left-right",
            "gear",
        ],
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
        },
    )

    # Logout button at the bottom of the sidebar
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.rerun()

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
