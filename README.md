# Cashflow Dashboard

A personal cashflow management dashboard built with Streamlit and SQLite. Track actual and projected cashflows, manage recurring payments, and import bank statements for reconciliation.

## Features

- **Dashboard**: View current balance, monthly metrics, cashflow charts, and spending by category
- **Transaction Management**: Add, edit, and delete transactions with categories
- **Projections**: Define recurring income/expenses (daily, weekly, monthly, yearly)
- **Bank Import**: Import CSV/Excel bank statements and reconcile transactions
- **Aggregation**: Merge multiple imported transactions into single entries

## Quick Start

```bash
# Install dependencies
uv sync

# Run the application
uv run streamlit run main.py
```

Open your browser to `http://localhost:8501`

## Getting Started

1. **Set Opening Balance**: Go to Settings and configure your starting balance and date
2. **Add Transactions**: Use the Dashboard to manually add income/expenses
3. **Create Recurring Rules**: Go to Projections to set up recurring payments (rent, salary, etc.)
4. **Import Statements**: Use Reconciliation to import bank statements and post transactions

## Project Structure

```
cashflow-dashboard/
├── main.py               # App entry point
├── pyproject.toml        # Dependencies
├── data/
│   └── cashflow.db       # SQLite database (created at runtime)
└── src/
    ├── database.py       # DB models (Transaction, RecurrenceRule, BankImport, Setting)
    ├── crud.py           # Database operations
    ├── logic.py          # Business logic (balance calculation, projections)
    ├── importers.py      # Bank statement parsing
    └── ui/
        ├── dashboard.py      # Main dashboard with charts
        ├── projections.py    # Recurrence rules management
        ├── reconciliation.py # Bank import & merge
        └── settings.py       # Configuration
```

## Database Schema

- **transactions**: Core records for actual and projected items
- **recurrence_rules**: Templates for generating projected transactions
- **bank_imports**: Staging area for imported statements
- **settings**: Key-value configuration (opening balance, date)

## Development

```bash
# Add a dependency
uv add <package>

# Run the app
uv run streamlit run main.py
```
