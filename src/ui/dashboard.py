"""Dashboard page UI module."""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, timedelta
from src.logic import (
    get_summary_metrics,
    calculate_running_balance,
    get_category_breakdown,
)
from src.crud import (
    get_all_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_unique_categories,
    get_opening_date,
)


def render():
    """Render the Dashboard page."""
    st.header("📊 Dashboard")

    # Summary metrics
    metrics = get_summary_metrics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Current Balance",
            f"£{metrics['current_balance']:,.2f}",
            delta=f"£{metrics['net_cashflow']:,.2f} this month",
        )

    with col2:
        st.metric("Monthly Inflow", f"£{metrics['monthly_inflow']:,.2f}")

    with col3:
        st.metric("Monthly Outflow", f"£{metrics['monthly_outflow']:,.2f}")

    with col4:
        st.metric(
            "Projected EOM Balance",
            f"£{metrics['projected_eom_balance']:,.2f}",
            delta=f"{metrics['savings_rate']:.1f}% savings rate",
        )

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(
        ["📈 Cashflow Chart", "📋 Transactions", "➕ Add Transaction"]
    )

    with tab1:
        render_cashflow_chart()

    with tab2:
        render_transactions_table()

    with tab3:
        render_add_transaction_form()


def render_cashflow_chart():
    """Render the cashflow over time chart."""
    st.subheader("Cashflow Over Time")

    # Date range selector
    col1, col2 = st.columns(2)
    opening_date = get_opening_date() or date.today() - timedelta(days=30)

    with col1:
        start_date = st.date_input("Start Date", value=opening_date, key="chart_start")
    with col2:
        end_date = st.date_input(
            "End Date", value=date.today() + timedelta(days=90), key="chart_end"
        )

    include_projections = st.checkbox("Include Projections", value=True)

    # Get running balance data
    df = calculate_running_balance(start_date, end_date, include_projections)

    if not df.empty and "balance" in df.columns:
        # Create main balance line chart
        balance_chart = (
            alt.Chart(df)
            .mark_line(color="#1f77b4", strokeWidth=2)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("balance:Q", title="Balance (£)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                    alt.Tooltip("balance:Q", title="Balance", format=",.2f"),
                ],
            )
        )

        # Add vertical line for current date
        today_df = pd.DataFrame({"date": [date.today()]})
        today_line = (
            alt.Chart(today_df)
            .mark_rule(color="red", strokeWidth=2, strokeDash=[5, 5])
            .encode(x="date:T")
        )

        # Add "Today" label
        today_label = (
            alt.Chart(today_df)
            .mark_text(
                align="left", dx=5, dy=-10, color="red", fontSize=12, fontWeight="bold"
            )
            .encode(x="date:T", y=alt.value(0), text=alt.value("Today"))
        )

        # Combine charts
        combined_chart = (
            (balance_chart + today_line + today_label)
            .properties(height=400)
            .interactive()
        )

        st.altair_chart(combined_chart, use_container_width=True)

        # Show category breakdown
        st.subheader("Spending by Category")
        category_df = get_category_breakdown(start_date, end_date)
        if not category_df.empty:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.bar_chart(category_df.set_index("category")["amount"])
            with col2:
                st.dataframe(category_df, hide_index=True, use_container_width=True)
        else:
            st.info("No expense data available for this period.")
    else:
        st.info(
            "No transaction data available. Add some transactions to see the chart."
        )


def render_transactions_table():
    """Render the transactions list with edit/delete options."""
    st.subheader("All Transactions")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Status", ["All", "ACTUAL", "PROJECTED"], key="status_filter"
        )

    with col2:
        start_filter = st.date_input(
            "From Date", value=date.today() - timedelta(days=30), key="txn_start"
        )

    with col3:
        end_filter = st.date_input(
            "To Date", value=date.today() + timedelta(days=30), key="txn_end"
        )

    # Get transactions
    status = None if status_filter == "All" else status_filter
    transactions = get_all_transactions(
        status=status, start_date=start_filter, end_date=end_filter
    )

    if not transactions:
        st.info("No transactions found for the selected filters.")
        return

    # Display as dataframe
    data = []
    for txn in transactions:
        data.append(
            {
                "ID": txn.id,
                "Date": txn.date,
                "Description": txn.description,
                "Amount": f"£{txn.amount:,.2f}",
                "Type": txn.type,
                "Status": txn.status,
                "Category": txn.category or "-",
                "Source": txn.source,
            }
        )

    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Edit/Delete section
    st.subheader("Edit or Delete Transaction")

    txn_ids = [t.id for t in transactions]
    selected_id = st.selectbox("Select Transaction ID", txn_ids, key="edit_select")

    if selected_id:
        selected_txn = next((t for t in transactions if t.id == selected_id), None)
        if selected_txn:
            with st.form("edit_transaction_form"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_date = st.date_input("Date", value=selected_txn.date)
                    edit_desc = st.text_input(
                        "Description", value=selected_txn.description
                    )
                    edit_amount = st.number_input(
                        "Amount", value=selected_txn.amount, min_value=0.0
                    )

                with col2:
                    edit_type = st.selectbox(
                        "Type",
                        ["INFLOW", "OUTFLOW"],
                        index=0 if selected_txn.type == "INFLOW" else 1,
                    )
                    edit_status = st.selectbox(
                        "Status",
                        ["ACTUAL", "PROJECTED"],
                        index=0 if selected_txn.status == "ACTUAL" else 1,
                    )
                    edit_category = st.text_input(
                        "Category", value=selected_txn.category or ""
                    )

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    update_btn = st.form_submit_button(
                        "Update Transaction", type="primary"
                    )
                with btn_col2:
                    delete_btn = st.form_submit_button(
                        "Delete Transaction", type="secondary"
                    )

                if update_btn:
                    update_transaction(
                        selected_id,
                        transaction_date=edit_date,
                        description=edit_desc,
                        amount=edit_amount,
                        transaction_type=edit_type,
                        status=edit_status,
                        category=edit_category,
                    )
                    st.success("Transaction updated!")
                    st.rerun()

                if delete_btn:
                    delete_transaction(selected_id)
                    st.success("Transaction deleted!")
                    st.rerun()


def render_add_transaction_form():
    """Render the add transaction form."""
    st.subheader("Add New Transaction")

    with st.form("add_transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            txn_date = st.date_input("Date", value=date.today())
            description = st.text_input(
                "Description", placeholder="e.g., Groceries, Salary"
            )
            amount = st.number_input(
                "Amount (£)", min_value=0.01, value=0.01, step=0.01
            )

        with col2:
            txn_type = st.selectbox("Type", ["OUTFLOW", "INFLOW"])
            status = st.selectbox("Status", ["ACTUAL", "PROJECTED"])

            # Category suggestions
            existing_categories = get_unique_categories()
            category = st.text_input(
                "Category",
                placeholder="e.g., Food, Utilities, Salary",
                help=f"Existing categories: {', '.join(existing_categories)}"
                if existing_categories
                else "",
            )

        submitted = st.form_submit_button(
            "Add Transaction", type="primary", use_container_width=True
        )

        if submitted:
            if not description:
                st.error("Please enter a description.")
            else:
                create_transaction(
                    transaction_date=txn_date,
                    description=description,
                    amount=amount,
                    transaction_type=txn_type,
                    status=status,
                    category=category,
                )
                st.success(f"Transaction '{description}' added successfully!")
                st.rerun()
