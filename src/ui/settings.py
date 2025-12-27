"""Settings page UI module."""

import streamlit as st
from datetime import date, datetime
from src.crud import (
    get_opening_balance,
    set_opening_balance,
    get_opening_date,
    set_opening_date,
    get_unique_categories,
)
from src.portability import export_to_json, import_from_json, get_data_summary


def render():
    """Render the Settings page."""
    st.header("⚙️ Settings")

    st.subheader("Opening Balance Configuration")

    col1, col2 = st.columns(2)

    with col1:
        # Opening Balance
        current_balance = get_opening_balance()
        new_balance = st.number_input(
            "Opening Balance (£)",
            value=current_balance,
            min_value=0.0,
            step=100.0,
            help="Set your initial account balance",
        )

        if st.button("Update Opening Balance"):
            set_opening_balance(new_balance)
            st.success(f"Opening balance updated to £{new_balance:,.2f}")
            st.rerun()

    with col2:
        # Opening Date
        current_date = get_opening_date() or date.today()
        new_date = st.date_input(
            "Opening Date",
            value=current_date,
            help="The date from which to start tracking",
        )

        if st.button("Update Opening Date"):
            set_opening_date(new_date)
            st.success(f"Opening date updated to {new_date.strftime('%Y-%m-%d')}")
            st.rerun()

    st.divider()

    # Display current settings
    st.subheader("Current Settings")
    settings_col1, settings_col2 = st.columns(2)

    with settings_col1:
        st.metric("Opening Balance", f"£{get_opening_balance():,.2f}")

    with settings_col2:
        opening_date = get_opening_date()
        st.metric(
            "Opening Date",
            opening_date.strftime("%Y-%m-%d") if opening_date else "Not set",
        )

    st.divider()

    # Categories overview
    st.subheader("Categories")
    categories = get_unique_categories()
    if categories:
        st.write("Existing categories used in transactions:")
        for cat in categories:
            st.write(f"• {cat}")
    else:
        st.info(
            "No categories defined yet. Categories are created automatically when you add transactions."
        )

    st.divider()

    # Data Portability Section
    st.subheader("📦 Data Export & Import")
    st.write(
        "Export all your data to a file for backup or to transfer to another instance of the app."
    )

    # Show current data summary
    summary = get_data_summary()
    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
    with col_summary1:
        st.metric("Settings", summary["settings"])
    with col_summary2:
        st.metric("Transactions", summary["transactions"])
    with col_summary3:
        st.metric("Recurrence Rules", summary["recurrence_rules"])
    with col_summary4:
        st.metric("Bank Imports", summary["bank_imports"])

    export_col, import_col = st.columns(2)

    with export_col:
        st.markdown("#### Export Data")
        st.write("Download all your data as a JSON file.")

        if st.button("Generate Export File", type="primary"):
            try:
                json_data = export_to_json()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cashflow_backup_{timestamp}.json"

                st.download_button(
                    label="📥 Download Backup File",
                    data=json_data,
                    file_name=filename,
                    mime="application/json",
                    type="secondary",
                )
                st.success("Export file ready for download!")
            except Exception as e:
                st.error(f"Export failed: {e}")

    with import_col:
        st.markdown("#### Import Data")
        st.write("Restore data from a previously exported file.")

        uploaded_file = st.file_uploader(
            "Choose a backup file",
            type=["json"],
            help="Upload a JSON file previously exported from this app",
        )

        if uploaded_file is not None:
            st.warning(
                "⚠️ Importing will **replace all existing data**. Make sure to export your current data first if needed."
            )

            if st.button("🔄 Import Data", type="primary"):
                try:
                    json_str = uploaded_file.read().decode("utf-8")
                    result = import_from_json(json_str, clear_existing=True)

                    st.success("✅ Data imported successfully!")
                    st.write("**Imported records:**")
                    st.write(f"- Settings: {result['counts']['settings']}")
                    st.write(f"- Transactions: {result['counts']['transactions']}")
                    st.write(
                        f"- Recurrence Rules: {result['counts']['recurrence_rules']}"
                    )
                    st.write(f"- Bank Imports: {result['counts']['bank_imports']}")

                    if result.get("export_timestamp"):
                        st.write(f"*Backup was created: {result['export_timestamp']}*")

                    st.rerun()
                except ValueError as e:
                    st.error(f"Import failed: {e}")
                except Exception as e:
                    st.error(f"Unexpected error during import: {e}")
