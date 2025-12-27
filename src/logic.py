"""Business logic for cashflow calculations and projections."""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional
import pandas as pd

from src.crud import (
    get_opening_balance,
    get_opening_date,
    get_all_transactions,
    get_all_recurrence_rules,
)
from src.database import RecurrenceRule


def calculate_balance(as_of_date: Optional[date] = None) -> float:
    """
    Calculate the current balance.
    Balance = Opening Balance + Sum(Actual Inflows) - Sum(Actual Outflows)
    """
    if as_of_date is None:
        as_of_date = date.today()

    opening_balance = get_opening_balance()
    transactions = get_all_transactions(status="ACTUAL", end_date=as_of_date)

    balance = opening_balance
    for txn in transactions:
        if txn.type == "INFLOW":
            balance += txn.amount
        else:
            balance -= txn.amount

    return balance


def calculate_running_balance(
    start_date: date, end_date: date, include_projections: bool = True
) -> pd.DataFrame:
    """
    Calculate running balance over a date range.
    Returns a DataFrame with date, balance, and status columns.
    """
    opening_balance = get_opening_balance()
    opening_date = get_opening_date() or start_date

    # Get all actual transactions
    actuals = get_all_transactions(
        status="ACTUAL", start_date=opening_date, end_date=end_date
    )

    # Get projections if requested
    projections = []
    if include_projections:
        projections = generate_projections(date.today(), end_date)

    # Combine and sort by date
    all_transactions = []
    for txn in actuals:
        all_transactions.append(
            {
                "date": txn.date,
                "description": txn.description,
                "amount": txn.amount if txn.type == "INFLOW" else -txn.amount,
                "type": txn.type,
                "status": "ACTUAL",
            }
        )

    for proj in projections:
        all_transactions.append(
            {
                "date": proj["date"],
                "description": proj["description"],
                "amount": proj["amount"]
                if proj["type"] == "INFLOW"
                else -proj["amount"],
                "type": proj["type"],
                "status": "PROJECTED",
            }
        )

    if not all_transactions:
        # Return empty dataframe with opening balance
        return pd.DataFrame(
            {
                "date": [opening_date],
                "balance": [opening_balance],
                "status": ["OPENING"],
            }
        )

    df = pd.DataFrame(all_transactions)
    df = df.sort_values("date")

    # Calculate running balance
    df["balance"] = opening_balance + df["amount"].cumsum()

    return df


def generate_projections(
    start_date: date, end_date: date, exclude_recorded: bool = True
) -> List[Dict]:
    """
    Generate projected transactions from recurrence rules AND manually added projected transactions.
    Returns list of dicts with transaction data (not persisted).

    Args:
        start_date: Start of date range
        end_date: End of date range
        exclude_recorded: If True, excludes projections that already have a matching actual transaction
    """
    rules = get_all_recurrence_rules()
    projections = []

    # Get existing actual transactions from recurring rules to avoid duplicates
    recorded_actuals = set()
    if exclude_recorded:
        actuals = get_all_transactions(
            status="ACTUAL", start_date=start_date, end_date=end_date
        )
        for txn in actuals:
            if txn.recurrence_id:
                # Key: (recurrence_id, date)
                recorded_actuals.add((txn.recurrence_id, txn.date))

    # Add projections from recurrence rules
    for rule in rules:
        dates = expand_recurrence(rule, start_date, end_date)
        for d in dates:
            # Skip if already recorded as actual
            if exclude_recorded and (rule.id, d) in recorded_actuals:
                continue
            projections.append(
                {
                    "date": d,
                    "description": rule.description,
                    "amount": rule.amount,
                    "type": rule.type,
                    "category": "",
                    "source": "RECURRING",
                    "recurrence_id": rule.id,
                    "transaction_id": None,  # Not a stored transaction
                }
            )

    # Add manually added singular projected transactions from the database
    projected_transactions = get_all_transactions(
        status="PROJECTED", start_date=start_date, end_date=end_date
    )
    for txn in projected_transactions:
        projections.append(
            {
                "date": txn.date,
                "description": txn.description,
                "amount": txn.amount,
                "type": txn.type,
                "category": txn.category or "",
                "source": txn.source or "MANUAL",
                "recurrence_id": txn.recurrence_id,
                "transaction_id": txn.id,  # Stored transaction ID for marking as actual
            }
        )

    return sorted(projections, key=lambda x: x["date"])


def expand_recurrence(
    rule: RecurrenceRule, start_date: date, end_date: date
) -> List[date]:
    """
    Expand a recurrence rule into specific dates within the given range.
    """
    dates = []
    current = rule.start_date

    # Generate dates until end_date
    rule_end = rule.end_date or end_date
    final_end = min(end_date, rule_end)

    while current <= final_end:
        # Include if within the requested range
        if current >= start_date:
            dates.append(current)
        current = get_next_occurrence(current, rule.frequency)
        if current is None:
            break

    return dates


def get_next_occurrence(current_date: date, frequency: str) -> Optional[date]:
    """Get the next occurrence date based on frequency."""
    if frequency == "DAILY":
        return current_date + timedelta(days=1)
    elif frequency == "WEEKLY":
        return current_date + timedelta(weeks=1)
    elif frequency == "MONTHLY":
        return current_date + relativedelta(months=1)
    elif frequency == "YEARLY":
        return current_date + relativedelta(years=1)
    return None


def get_summary_metrics(as_of_date: Optional[date] = None) -> Dict:
    """
    Calculate summary metrics for the dashboard.
    """
    if as_of_date is None:
        as_of_date = date.today()

    current_balance = calculate_balance(as_of_date)

    # Get this month's transactions
    month_start = as_of_date.replace(day=1)
    if as_of_date.month == 12:
        month_end = as_of_date.replace(
            year=as_of_date.year + 1, month=1, day=1
        ) - timedelta(days=1)
    else:
        month_end = as_of_date.replace(month=as_of_date.month + 1, day=1) - timedelta(
            days=1
        )

    monthly_txns = get_all_transactions(
        status="ACTUAL", start_date=month_start, end_date=month_end
    )

    monthly_inflow = sum(t.amount for t in monthly_txns if t.type == "INFLOW")
    monthly_outflow = sum(t.amount for t in monthly_txns if t.type == "OUTFLOW")

    # Calculate projected end of month balance
    projections = generate_projections(as_of_date, month_end)
    projected_change = sum(
        p["amount"] if p["type"] == "INFLOW" else -p["amount"] for p in projections
    )
    projected_eom_balance = current_balance + projected_change

    # Calculate savings rate (if there's income)
    savings_rate = 0.0
    if monthly_inflow > 0:
        savings_rate = ((monthly_inflow - monthly_outflow) / monthly_inflow) * 100

    return {
        "current_balance": current_balance,
        "monthly_inflow": monthly_inflow,
        "monthly_outflow": monthly_outflow,
        "projected_eom_balance": projected_eom_balance,
        "savings_rate": savings_rate,
        "net_cashflow": monthly_inflow - monthly_outflow,
    }


def get_category_breakdown(
    start_date: Optional[date] = None, end_date: Optional[date] = None
) -> pd.DataFrame:
    """
    Get spending breakdown by category.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date.replace(day=1)

    transactions = get_all_transactions(
        status="ACTUAL", start_date=start_date, end_date=end_date
    )

    # Filter to outflows only
    outflows = [t for t in transactions if t.type == "OUTFLOW"]

    if not outflows:
        return pd.DataFrame(columns=["category", "amount"])

    data = [
        {"category": t.category or "Uncategorized", "amount": t.amount}
        for t in outflows
    ]
    df = pd.DataFrame(data)

    return (
        df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
