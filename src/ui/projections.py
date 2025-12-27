"""Projections page UI module."""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from src.logic import generate_projections
from src.crud import (
    get_all_recurrence_rules,
    create_recurrence_rule,
    update_recurrence_rule,
    delete_recurrence_rule,
    create_transaction,
    update_transaction,
)


def render():
    """Render the Projections page."""
    st.header("📅 Projections")

    tab1, tab2, tab3 = st.tabs(
        ["📋 Upcoming Projections", "🔄 Recurrence Rules", "➕ Add Rule"]
    )

    with tab1:
        render_projections_view()

    with tab2:
        render_recurrence_rules()

    with tab3:
        render_add_rule_form()


def render_projections_view():
    """Render the upcoming projected transactions."""
    st.subheader("Projected Transactions")

    # Get rules to determine earliest start date
    rules = get_all_recurrence_rules()
    earliest_rule_date = (
        min((r.start_date for r in rules), default=date.today())
        if rules
        else date.today()
    )

    # Date range for projections - default to earliest rule start
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From Date", value=earliest_rule_date, key="proj_start"
        )
    with col2:
        end_date = st.date_input(
            "To Date", value=date.today() + timedelta(days=365), key="proj_end"
        )

    # Generate projections
    projections = generate_projections(start_date, end_date)

    if not projections:
        st.info(
            "No projected transactions for this period. Add recurrence rules to generate projections."
        )
        return

    # Count past due items
    past_due = [p for p in projections if p["date"] < date.today()]
    if past_due:
        st.warning(
            f"⚠️ {len(past_due)} projection(s) are past due and need to be marked as paid/received."
        )

    # Display projections
    data = []
    for i, proj in enumerate(projections):
        status = (
            "⏰ Past Due"
            if proj["date"] < date.today()
            else ("📅 Today" if proj["date"] == date.today() else "🔮 Upcoming")
        )
        source_label = (
            "🔄 Recurring"
            if proj["source"] == "RECURRING" and proj.get("transaction_id") is None
            else "📝 One-time"
        )
        data.append(
            {
                "Index": i,
                "Status": status,
                "Date": proj["date"],
                "Description": proj["description"],
                "Amount": f"£{proj['amount']:,.2f}",
                "Type": proj["type"],
                "Source": source_label,
            }
        )

    df = pd.DataFrame(data)
    st.dataframe(df.drop(columns=["Index"]), hide_index=True, use_container_width=True)

    # Summary
    total_inflow = sum(p["amount"] for p in projections if p["type"] == "INFLOW")
    total_outflow = sum(p["amount"] for p in projections if p["type"] == "OUTFLOW")

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Projected Inflow", f"£{total_inflow:,.2f}")
    with col2:
        st.metric("Total Projected Outflow", f"£{total_outflow:,.2f}")
    with col3:
        st.metric("Net Projected Change", f"£{total_inflow - total_outflow:,.2f}")

    st.divider()

    # Mark as Actual section
    st.subheader("Mark Projection as Paid/Received")

    if projections:
        proj_options = [
            f"{p['date']} - {p['description']} (£{p['amount']:,.2f})"
            for p in projections
        ]
        selected_proj_idx = st.selectbox(
            "Select Projection",
            range(len(proj_options)),
            format_func=lambda x: proj_options[x],
            key="select_proj",
        )

        if st.button("Mark as Paid/Received", type="primary"):
            proj = projections[selected_proj_idx]

            # Check if this is a manually added projected transaction (has transaction_id)
            if proj.get("transaction_id"):
                # Update the existing projected transaction to ACTUAL
                update_transaction(txn_id=proj["transaction_id"], status="ACTUAL")
                st.success(f"'{proj['description']}' marked as actual!")
            else:
                # This is a recurring projection - create a new actual transaction
                create_transaction(
                    transaction_date=proj["date"],
                    description=proj["description"],
                    amount=proj["amount"],
                    transaction_type=proj["type"],
                    status="ACTUAL",
                    category=proj.get("category", ""),
                    source="RECURRING",
                    recurrence_id=proj["recurrence_id"],
                )
                st.success(f"'{proj['description']}' marked as actual!")
            st.rerun()


def render_recurrence_rules():
    """Render the list of recurrence rules."""
    st.subheader("Recurrence Rules")

    rules = get_all_recurrence_rules()

    if not rules:
        st.info(
            "No recurrence rules defined. Add a rule to start generating projections."
        )
        return

    # Display rules
    data = []
    for rule in rules:
        data.append(
            {
                "ID": rule.id,
                "Description": rule.description,
                "Amount": f"£{rule.amount:,.2f}",
                "Type": rule.type,
                "Frequency": rule.frequency,
                "Start Date": rule.start_date,
                "End Date": rule.end_date or "Ongoing",
            }
        )

    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Edit/Delete section
    st.subheader("Edit or Delete Rule")

    rule_ids = [r.id for r in rules]
    selected_id = st.selectbox("Select Rule ID", rule_ids, key="rule_select")

    if selected_id:
        selected_rule = next((r for r in rules if r.id == selected_id), None)
        if selected_rule:
            with st.form("edit_rule_form"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_desc = st.text_input(
                        "Description", value=selected_rule.description
                    )
                    edit_amount = st.number_input(
                        "Amount", value=selected_rule.amount, min_value=0.0
                    )
                    edit_type = st.selectbox(
                        "Type",
                        ["INFLOW", "OUTFLOW"],
                        index=0 if selected_rule.type == "INFLOW" else 1,
                    )

                with col2:
                    edit_freq = st.selectbox(
                        "Frequency",
                        ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"],
                        index=["DAILY", "WEEKLY", "MONTHLY", "YEARLY"].index(
                            selected_rule.frequency
                        ),
                    )
                    edit_start = st.date_input(
                        "Start Date", value=selected_rule.start_date
                    )
                    edit_end = st.date_input(
                        "End Date (optional)",
                        value=selected_rule.end_date
                        if selected_rule.end_date
                        else None,
                    )

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    update_btn = st.form_submit_button("Update Rule", type="primary")
                with btn_col2:
                    delete_btn = st.form_submit_button("Delete Rule", type="secondary")

                if update_btn:
                    update_recurrence_rule(
                        selected_id,
                        description=edit_desc,
                        amount=edit_amount,
                        rule_type=edit_type,
                        frequency=edit_freq,
                        start_date=edit_start,
                        end_date=edit_end if edit_end else None,
                    )
                    st.success("Rule updated!")
                    st.rerun()

                if delete_btn:
                    delete_recurrence_rule(selected_id)
                    st.success("Rule deleted!")
                    st.rerun()


def render_add_rule_form():
    """Render the add recurrence rule form."""
    st.subheader("Add New Recurrence Rule")

    with st.form("add_rule_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            description = st.text_input(
                "Description", placeholder="e.g., Rent, Salary, Netflix"
            )
            amount = st.number_input(
                "Amount (£)", min_value=0.01, value=0.01, step=0.01
            )
            rule_type = st.selectbox("Type", ["OUTFLOW", "INFLOW"])

        with col2:
            frequency = st.selectbox(
                "Frequency", ["MONTHLY", "WEEKLY", "DAILY", "YEARLY"]
            )
            start_date = st.date_input("Start Date", value=date.today())
            end_date = st.date_input(
                "End Date (optional)",
                value=None,
                help="Leave empty for ongoing recurring transactions",
            )

        # Examples
        st.caption("**Examples:**")
        st.caption("• Rent: £2,000, OUTFLOW, MONTHLY, starts on 1st of month")
        st.caption("• Salary: £5,000, INFLOW, MONTHLY, starts on 15th of month")
        st.caption("• Netflix: £15.99, OUTFLOW, MONTHLY")

        submitted = st.form_submit_button(
            "Add Recurrence Rule", type="primary", use_container_width=True
        )

        if submitted:
            if not description:
                st.error("Please enter a description.")
            else:
                create_recurrence_rule(
                    description=description,
                    amount=amount,
                    rule_type=rule_type,
                    frequency=frequency,
                    start_date=start_date,
                    end_date=end_date if end_date else None,
                )
                st.success(f"Recurrence rule '{description}' added successfully!")
                st.rerun()
