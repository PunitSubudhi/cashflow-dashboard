"""Reconciliation page UI module."""

import streamlit as st
import pandas as pd
from datetime import date
from src.importers import parse_bank_statement, detect_columns, generate_batch_id
from src.crud import (
    create_bank_import,
    get_pending_bank_imports,
    update_bank_import_status,
    post_bank_import,
    merge_bank_imports,
    get_unique_categories,
)


def render():
    """Render the Reconciliation page."""
    st.header("🔄 Reconciliation")

    tab1, tab2 = st.tabs(["📤 Import Statement", "📋 Staging Area"])

    with tab1:
        render_import_section()

    with tab2:
        render_staging_area()


def render_import_section():
    """Render the bank statement import section."""
    st.subheader("Import Bank Statement")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload your bank statement to import transactions",
    )

    if uploaded_file:
        file_content = uploaded_file.read()
        file_name = uploaded_file.name

        # Detect columns
        detection = detect_columns(file_content, file_name)

        if "error" in detection:
            st.error(f"Error reading file: {detection['error']}")
            return

        st.subheader("Column Mapping")
        st.write("Map your file's columns to the required fields:")

        col1, col2, col3 = st.columns(3)

        with col1:
            date_col = st.selectbox(
                "Date Column",
                detection["all_columns"],
                index=detection["all_columns"].index(detection["date_candidates"][0])
                if detection["date_candidates"]
                and detection["date_candidates"][0] in detection["all_columns"]
                else 0,
            )

        with col2:
            desc_col = st.selectbox(
                "Description Column",
                detection["all_columns"],
                index=detection["all_columns"].index(
                    detection["description_candidates"][0]
                )
                if detection["description_candidates"]
                and detection["description_candidates"][0] in detection["all_columns"]
                else min(1, len(detection["all_columns"]) - 1),
            )

        with col3:
            amount_col = st.selectbox(
                "Amount Column",
                detection["all_columns"],
                index=detection["all_columns"].index(detection["amount_candidates"][0])
                if detection["amount_candidates"]
                and detection["amount_candidates"][0] in detection["all_columns"]
                else len(detection["all_columns"]) - 1,
            )

        # Date format options
        date_format = st.selectbox(
            "Date Format",
            [
                "%Y-%m-%d",  # 2024-01-15
                "%m/%d/%Y",  # 01/15/2024
                "%d/%m/%Y",  # 15/01/2024
                "%m-%d-%Y",  # 01-15-2024
                "%d-%m-%Y",  # 15-01-2024
                "%Y/%m/%d",  # 2024/01/15
            ],
            help="Select the date format used in your file",
        )

        # Preview
        st.subheader("Preview")
        if detection.get("preview"):
            st.dataframe(pd.DataFrame(detection["preview"]), hide_index=True)

        # Parse and import
        if st.button("Parse and Import", type="primary"):
            df, error = parse_bank_statement(
                file_content,
                file_name,
                date_column=date_col,
                description_column=desc_col,
                amount_column=amount_col,
                date_format=date_format,
            )

            if error:
                st.error(error)
            elif df is not None:
                batch_id = generate_batch_id()
                imported_count = 0

                for _, row in df.iterrows():
                    create_bank_import(
                        batch_id=batch_id,
                        import_date=row["date"],
                        description=row["description"],
                        amount=row["amount"],
                    )
                    imported_count += 1

                st.success(
                    f"Successfully imported {imported_count} transactions. Batch ID: {batch_id}"
                )
                st.info("Go to the 'Staging Area' tab to review and post transactions.")


def render_staging_area():
    """Render the staging area for imported transactions."""
    st.subheader("Pending Imports")

    pending = get_pending_bank_imports()

    if not pending:
        st.info("No pending imports. Upload a bank statement to get started.")
        return

    # Display pending imports
    data = []
    for imp in pending:
        data.append(
            {
                "ID": imp.id,
                "Batch": imp.import_batch_id,
                "Date": imp.date,
                "Description": imp.description,
                "Amount": imp.amount,
                "Status": imp.status,
            }
        )

    df = pd.DataFrame(data)

    # Selection for operations
    st.write("Select transactions to post or merge:")

    # Use checkboxes for selection
    selected_ids = []

    for _, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([0.5, 1, 2, 1, 1])
        with col1:
            if st.checkbox(
                "Select", key=f"select_{row['ID']}", label_visibility="collapsed"
            ):
                selected_ids.append(row["ID"])
        with col2:
            st.write(row["Date"])
        with col3:
            st.write(row["Description"])
        with col4:
            amount_color = "green" if row["Amount"] > 0 else "red"
            st.markdown(f":{amount_color}[£{abs(row['Amount']):,.2f}]")
        with col5:
            st.write(row["Batch"])

    st.divider()

    # Category input
    existing_categories = get_unique_categories()
    category = st.text_input(
        "Category for selected transactions",
        placeholder="e.g., Food, Shopping, Bills",
        help=f"Existing categories: {', '.join(existing_categories)}"
        if existing_categories
        else "",
    )

    # Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Post Selected", type="primary", disabled=len(selected_ids) == 0):
            for imp_id in selected_ids:
                post_bank_import(imp_id, category=category)
            st.success(f"Posted {len(selected_ids)} transaction(s)!")
            st.rerun()

    with col2:
        if len(selected_ids) >= 2:
            merge_desc = st.text_input(
                "Merged Description",
                placeholder="Enter description for merged transaction",
                key="merge_desc",
            )
            if st.button("Merge Selected", type="secondary"):
                if merge_desc:
                    result = merge_bank_imports(
                        selected_ids, merge_desc, category=category
                    )
                    if result:
                        st.success(
                            f"Merged {len(selected_ids)} transactions into '{merge_desc}'!"
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Failed to merge. Make sure all selected items are pending."
                        )
                else:
                    st.warning("Please enter a description for the merged transaction.")

    with col3:
        if st.button("Ignore Selected", disabled=len(selected_ids) == 0):
            for imp_id in selected_ids:
                update_bank_import_status(imp_id, "IGNORED")
            st.success(f"Ignored {len(selected_ids)} transaction(s).")
            st.rerun()

    # Summary
    st.divider()
    st.subheader("Summary")

    total_amount = df["Amount"].sum()
    inflow = df[df["Amount"] > 0]["Amount"].sum()
    outflow = df[df["Amount"] < 0]["Amount"].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", len(pending))
    with col2:
        st.metric("Total Inflow", f"£{inflow:,.2f}")
    with col3:
        st.metric("Total Outflow", f"£{abs(outflow):,.2f}")
    with col4:
        st.metric("Net Amount", f"£{total_amount:,.2f}")
