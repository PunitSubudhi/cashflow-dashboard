# Detailed Phased Implementation Plan

This document outlines the step-by-step implementation of the Cashflow Dashboard, including specific checkpoints and testing milestones to ensure quality and progress.

## Phase 1: Foundation & Infrastructure (Current Status: Mostly Complete)
**Goal**: Establish the project structure, database schema, and basic application shell.

### Tasks
- [x] Initialize project with `uv` and `pyproject.toml`.
- [x] Create folder structure (`src/`, `data/`, `.streamlit/`).
- [x] Define Database Models (`Transaction`, `RecurrenceRule`, `BankImport`, `Setting`) in `src/database.py`.
- [x] Create basic Streamlit entry point (`main.py`) and navigation.

### Checkpoints
- [x] Application runs without errors (`uv run streamlit run main.py`).
- [x] `data/cashflow.db` is created automatically upon startup.

### Unit Testing Milestones
- **Test Suite Setup**: Create `tests/` directory.
- **Database Tests**:
    - Verify database connection.
    - Verify table creation (schema check).
    - Test creating and retrieving a dummy `Transaction`.

---

## Phase 2: Core Cashflow & Manual Entry
**Goal**: Enable manual data entry and basic balance tracking.

### Tasks
1.  **Settings Module**:
    - Create UI to set/update "Opening Balance" and "Start Date".
    - Store values in `settings` table.
2.  **Transaction CRUD**:
    - Create `src/crud.py` for database operations.
    - Implement "Add Transaction" form (Date, Description, Amount, Type, Category).
    - Implement "Edit/Delete" functionality in the UI.
3.  **Balance Logic**:
    - Implement `calculate_balance()` in `src/logic.py`.
    - Logic: `Opening Balance + Sum(Actual Inflows) - Sum(Actual Outflows)`.

### Checkpoints
- [ ] User can set an opening balance of $5,000.
- [ ] User can manually add a "Groceries" expense of $100.
- [ ] Dashboard shows current balance of $4,900.

### Unit Testing Milestones
- **Logic Tests** (`tests/test_logic.py`):
    - Test balance calculation with 0 transactions.
    - Test balance calculation with mixed inflows/outflows.
- **CRUD Tests** (`tests/test_crud.py`):
    - Test adding a transaction.
    - Test updating a transaction.
    - Test deleting a transaction.

---

## Phase 3: Projections & Recurrence Engine
**Goal**: Automate future cashflow views based on recurring rules.

### Tasks
1.  **Recurrence Management**:
    - UI to create `RecurrenceRule` (e.g., "Rent", $2000, Monthly, 1st of month).
2.  **Projection Generation**:
    - Implement `generate_projections(start_date, end_date)` in `src/logic.py`.
    - Logic: Iterate through rules and generate `Transaction` objects with `status='PROJECTED'` in memory (or temp table) for display.
    - *Alternative*: Persist projections to DB but manage them carefully to avoid duplicates.
3.  **Status Transition**:
    - UI action to "Mark as Paid/Received".
    - Updates transaction `status` from `PROJECTED` to `ACTUAL`.

### Checkpoints
- [ ] User creates a monthly "Rent" rule.
- [ ] "Projections" page shows Rent entries for the next 12 months.
- [ ] User marks this month's rent as "Paid"; it moves to "Actuals" and updates the running balance.

### Unit Testing Milestones
- **Recurrence Tests** (`tests/test_recurrence.py`):
    - Test "Monthly" expansion (correct dates).
    - Test "Weekly" expansion.
    - Test "Yearly" expansion.
- **Projection Tests**:
    - Verify projections do not duplicate existing "Actual" transactions for the same period (if logic requires).

---

## Phase 4: Bank Import & Reconciliation
**Goal**: Import real data and merge it with projections/manual entries.

### Tasks
1.  **File Parsing**:
    - Implement `src/importers.py` using `pandas` and `openpyxl`.
    - Support CSV and Excel formats.
    - Normalize columns to: `Date`, `Description`, `Amount`.
2.  **Staging Area**:
    - UI to upload file and preview data in `BankImport` table.
3.  **Reconciliation Logic**:
    - **Direct Post**: Button to move a staging row to `Transaction` (Actual).
    - **Aggregation**: Select multiple staging rows -> "Merge" -> Create 1 `Transaction`.
    - **Matching**: (Optional) Suggest matches between Staging and Projected items.

### Checkpoints
- [ ] Upload a sample bank CSV.
- [ ] Select 3 "Starbucks" entries ($5, $5, $5) and merge them into one "Coffee" transaction ($15).
- [ ] The 3 original rows are marked "MERGED" and hidden; 1 new "Actual" transaction exists.

### Unit Testing Milestones
- **Importer Tests** (`tests/test_importers.py`):
    - Test parsing a standard CSV.
    - Test handling invalid file formats.
- **Reconciliation Tests**:
    - Test aggregation math (Sum of parts == Total).
    - Test state changes (Pending -> Merged/Posted).

---

## Phase 5: Visualization & Analytics
**Goal**: Provide visual insights into financial health.

### Tasks
1.  **Cashflow Chart**:
    - Line chart showing balance over time.
    - Color coding for Past (Actual) vs Future (Projected).
2.  **Category Breakdown**:
    - Pie/Bar chart of expenses by category.
3.  **Summary Metrics**:
    - "Burn Rate", "Savings Rate", "End of Year Projected Balance".

### Checkpoints
- [ ] Chart clearly shows the "cliff" where Actuals end and Projections begin.
- [ ] Filters (Date Range, Category) update the charts instantly.

### Unit Testing Milestones
- **Analytics Tests**:
    - Verify metric calculations (e.g., Savings Rate formula).

---

## Phase 6: Polish & Deployment
**Goal**: Refine UI/UX and prepare for daily use.

### Tasks
1.  **UI Refinement**: Use Streamlit columns, expanders, and tabs for a cleaner layout.
2.  **Error Handling**: Graceful messages for DB errors or bad file uploads.
3.  **Backup**: Simple button to export `cashflow.db` or dump to CSV.

### Checkpoints
- [ ] Full end-to-end walkthrough with a fresh database feels smooth.
- [ ] No unhandled exceptions in the logs.
