"""Cashflow view UI module - shows all transactions with running balance."""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from src.crud import (
    get_opening_balance,
    get_opening_date,
    get_all_transactions,
    get_all_recurrence_rules,
)
from src.logic import generate_projections


def render():
    """Render the Cashflow view page."""
    st.header("💷 Cashflow")

    # Get date range
    opening_date = get_opening_date() or date.today()
    opening_balance = get_opening_balance()

    # Get all recurrence rules to find the furthest end date
    rules = get_all_recurrence_rules()

    # Default end date: 1 year from now or furthest rule end date
    default_end = date.today() + timedelta(days=365)
    if rules:
        rule_ends = [r.end_date for r in rules if r.end_date]
        if rule_ends:
            default_end = max(default_end, max(rule_ends))

    # Generate projections to find the last projected date
    projections = generate_projections(date.today(), default_end)
    if projections:
        last_projection_date = max(p["date"] for p in projections)
        default_end = max(default_end, last_projection_date)

    # Build the complete cashflow table
    cashflow_data = []

    # Add opening balance row
    cashflow_data.append(
        {
            "date": opening_date,
            "description": "📍 Opening Balance",
            "inflow": None,
            "outflow": None,
            "type": "OPENING",
            "status": "ACTUAL",
            "category": "-",
            "running_balance": opening_balance,
        }
    )

    # Get all actual transactions
    actuals = get_all_transactions(status="ACTUAL")
    for txn in actuals:
        cashflow_data.append(
            {
                "date": txn.date,
                "description": txn.description,
                "inflow": txn.amount if txn.type == "INFLOW" else None,
                "outflow": txn.amount if txn.type == "OUTFLOW" else None,
                "type": txn.type,
                "status": "✅ Actual",
                "category": txn.category or "-",
                "running_balance": 0,  # Will be calculated
            }
        )

    # Add projections
    for proj in projections:
        cashflow_data.append(
            {
                "date": proj["date"],
                "description": proj["description"],
                "inflow": proj["amount"] if proj["type"] == "INFLOW" else None,
                "outflow": proj["amount"] if proj["type"] == "OUTFLOW" else None,
                "type": proj["type"],
                "status": "🔮 Projected",
                "category": proj.get("category", "-") or "-",
                "running_balance": 0,  # Will be calculated
            }
        )

    if not cashflow_data:
        st.info(
            "No transactions found. Add transactions or set up recurrence rules to see your cashflow."
        )
        return

    # Sort by date
    cashflow_data.sort(key=lambda x: (x["date"], 0 if x["type"] == "OPENING" else 1))

    # Calculate running balance
    running_balance = 0
    for row in cashflow_data:
        if row["type"] == "OPENING":
            running_balance = row["running_balance"]
        else:
            if row["inflow"]:
                running_balance += row["inflow"]
            if row["outflow"]:
                running_balance -= row["outflow"]
            row["running_balance"] = running_balance

    # Convert to DataFrame for display
    df = pd.DataFrame(cashflow_data)

    # Format for display
    display_df = pd.DataFrame(
        {
            "Date": df["date"],
            "Description": df["description"],
            "Inflow": df["inflow"].apply(
                lambda x: f"£{x:,.2f}" if pd.notna(x) else "-"
            ),
            "Outflow": df["outflow"].apply(
                lambda x: f"£{x:,.2f}" if pd.notna(x) else "-"
            ),
            "Status": df["status"],
            "Category": df["category"],
            "Running Balance": df["running_balance"].apply(lambda x: f"£{x:,.2f}"),
        }
    )

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    total_inflows = df["inflow"].sum() or 0
    total_outflows = df["outflow"].sum() or 0
    final_balance = (
        cashflow_data[-1]["running_balance"] if cashflow_data else opening_balance
    )

    with col1:
        st.metric("Opening Balance", f"£{opening_balance:,.2f}")
    with col2:
        st.metric("Total Inflows", f"£{total_inflows:,.2f}")
    with col3:
        st.metric("Total Outflows", f"£{total_outflows:,.2f}")
    with col4:
        st.metric("Final Projected Balance", f"£{final_balance:,.2f}")

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["✅ Actual", "🔮 Projected"],
            default=["✅ Actual", "🔮 Projected"],
        )
    with col2:
        # Get unique categories
        categories = df["category"].unique().tolist()
        category_filter = st.multiselect(
            "Filter by Category", categories, default=categories
        )
    with col3:
        show_opening = st.checkbox("Show Opening Balance Row", value=True)

    # Apply filters
    filtered_df = display_df.copy()
    mask = display_df["Status"].isin(status_filter) | (
        display_df["Description"] == "📍 Opening Balance"
    )
    if not show_opening:
        mask = mask & (display_df["Description"] != "📍 Opening Balance")

    # Category filter
    category_mask = df["category"].isin(category_filter) | (df["type"] == "OPENING")
    mask = mask & category_mask

    filtered_df = display_df[mask]

    # Display the table
    st.subheader(
        f"Cashflow Statement ({opening_date.strftime('%d %b %Y')} - {default_end.strftime('%d %b %Y')})"
    )
    st.dataframe(filtered_df, hide_index=True, use_container_width=True, height=600)

    # Export option
    st.divider()
    if st.button("📥 Export to CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"cashflow_{date.today().isoformat()}.csv",
            mime="text/csv",
        )
