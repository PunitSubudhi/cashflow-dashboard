# Cashflow Management Dashboard Implementation Plan

## 1. Project Overview
A personal cashflow management dashboard built with Streamlit and SQLite. The application tracks actual and projected cashflows, allowing for manual entry, recurring schedules, and bank statement reconciliation with transaction aggregation.

## 2. Architecture & Tech Stack
- **Frontend:** Streamlit
- **Database:** SQLite (stored in `./data/cashflow.db`)
- **Data Processing:** Pandas
- **File Handling:** `openpyxl` (Excel), `csv` module
- **ORM/Database Access:** `sqlite3` or `SQLAlchemy` (recommended for better management)

## 3. Database Schema Design

### Tables
1.  **`settings`**
    *   `key` (PK, TEXT): e.g., 'opening_balance', 'opening_date'
    *   `value` (TEXT)

2.  **`transactions`**
    *   `id` (PK, INTEGER, Auto-increment)
    *   `date` (DATE): Transaction date
    *   `description` (TEXT)
    *   `amount` (REAL): Positive for inflow, negative for outflow
    *   `type` (TEXT): 'INFLOW' or 'OUTFLOW'
    *   `status` (TEXT): 'PROJECTED' or 'ACTUAL'
    *   `category` (TEXT)
    *   `source` (TEXT): 'MANUAL', 'RECURRING', 'BANK_IMPORT'
    *   `recurrence_id` (FK, INTEGER, Nullable): Link to recurrence rule if applicable

3.  **`recurrence_rules`**
    *   `id` (PK, INTEGER, Auto-increment)
    *   `description` (TEXT)
    *   `amount` (REAL)
    *   `type` (TEXT): 'INFLOW' or 'OUTFLOW'
    *   `frequency` (TEXT): 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'
    *   `start_date` (DATE)
    *   `end_date` (DATE, Nullable)
    *   `last_generated_date` (DATE, Nullable)

4.  **`bank_imports`** (Staging area for imported statements)
    *   `id` (PK, INTEGER, Auto-increment)
    *   `import_batch_id` (TEXT): UUID for the upload batch
    *   `date` (DATE)
    *   `description` (TEXT)
    *   `amount` (REAL)
    *   `status` (TEXT): 'PENDING', 'MERGED', 'POSTED', 'IGNORED'

## 4. Functional Modules

### A. Setup & Configuration
- Input for **Opening Balance** and **Start Date**.
- Stored in the `settings` table.

### B. Projections Engine
- **Manual Entry:** Form to add single future income/expense.
- **Recurring Schedules:**
    - Define rules (e.g., Rent, Salary).
    - Logic to generate `transactions` with status 'PROJECTED' based on these rules up to a future horizon (e.g., next 12 months).
- **Conversion:** UI to mark a 'PROJECTED' item as 'ACTUAL' (Paid/Received).

### C. Bank Import & Reconciliation
- **Upload Interface:** Drag & drop for CSV/XLSX.
- **Mapping:** Map columns (Date, Description, Amount) from file to system format.
- **Staging View:** Display imported rows.
- **Aggregation Feature:**
    - Select multiple rows from the staging table.
    - Click "Merge & Post".
    - Modal to enter new Description and Category for the aggregated total.
    - Creates one 'ACTUAL' record in `transactions`.
    - Marks staging rows as 'MERGED'.
- **Direct Post:** Select single row -> Post as 'ACTUAL'.

### D. Dashboard & Visualization
- **Cashflow Chart:** Line chart showing running balance over time (combining Actuals up to today + Projections future).
- **Data Table:** Filterable view of all transactions (Actual vs Projected).
- **Summary Metrics:** Current Balance, Projected End-of-Month Balance.

## 5. Implementation Steps

### Phase 1: Foundation
1.  **Environment Setup:** Configure `pyproject.toml` with dependencies (streamlit, pandas, sqlalchemy, openpyxl) for `uv`.
2.  **Configuration:** Create `.streamlit/config.toml` for theme/server settings and `.streamlit/secrets.toml` for sensitive data (if any).
3.  **Database Init:** Create `database.py` to handle SQLite connection and table creation in `./data`.
4.  **Basic UI:** Create `main.py` with Streamlit layout and navigation.

### Phase 2: Core Cashflow (Manual)
4.  **Settings Module:** Implement Opening Balance setup.
5.  **Transaction CRUD:** Add/Edit/Delete manual transactions.
6.  **Balance Calculation:** Function to calculate running balance from Opening Balance + Transactions.
7.  **Visualization:** Plot the balance history and projection.

### Phase 3: Projections & Recurrence
8.  **Recurrence Logic:** Implement logic to expand recurrence rules into projected transactions.
9.  **Status Toggling:** UI to switch transaction status from Projected to Actual.

### Phase 4: Bank Import & Aggregation
10. **File Parser:** Utility to read CSV/Excel and normalize data.
11. **Reconciliation UI:**
    - Split screen or step-by-step flow.
    - Checkbox selection for multiple rows.
    - "Merge" logic implementation.

### Phase 5: Refinement
12. **Styling:** Improve Streamlit UI usage (columns, expanders, metrics).
13. **Testing:** Verify calculations and aggregation logic.

## 6. File Structure Proposal
```
cashflow-dashboard/
├── .github/
│   └── implementation_plan.md
├── .streamlit/
│   ├── config.toml       # Streamlit configuration
│   └── secrets.toml      # Secrets management
├── data/
│   └── cashflow.db (created at runtime)
├── src/
│   ├── __init__.py
│   ├── database.py       # DB connection & models
│   ├── logic.py          # Core business logic (calculations, recurrence)
│   ├── importers.py      # Bank statement parsing
│   └── ui/
│       ├── dashboard.py
│       ├── projections.py
│       └── reconciliation.py
├── main.py               # App entry point
├── pyproject.toml        # Project configuration and dependencies
└── README.md
```
