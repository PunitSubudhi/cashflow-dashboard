# Cashflow Dashboard - Copilot Instructions

## Project Overview
Personal cashflow management dashboard built with Streamlit and SQLite. Tracks actuals vs. projections, handles recurring payments, and supports bank statement imports.

## Architecture & Patterns
- **Frontend**: Streamlit (`main.py` entry point).
- **Backend**: SQLite database (`data/cashflow.db`) accessed via SQLAlchemy ORM (`src/database.py`).
- **Dependency Management**: `uv` (configured in `pyproject.toml`).

### Code Structure
- `main.py`: Application entry point. Handles sidebar navigation and page routing.
- `src/ui/`: UI modules for each page.
    - **Pattern**: Each module (e.g., `dashboard.py`) must export a `render()` function that contains the Streamlit layout code.
- `src/database.py`: Database configuration and SQLAlchemy models.
    - **Pattern**: Use `get_session()` to obtain a DB session. Always close sessions or use context managers.
- `src/logic.py`: Business logic (calculations, recurrence expansion).
- `src/importers.py`: File parsing logic for bank statements.

### Database Conventions
- **Models**: Defined in `src/database.py` inheriting from `Base`.
- **Session**: Use `src.database.get_session()` for all DB operations.
- **Schema**:
    - `Transaction`: Core record for both actual and projected items.
    - `RecurrenceRule`: Templates for generating projected transactions.
    - `BankImport`: Staging area for raw statement data.

## Development Workflow
- **Run App**: `uv run streamlit run main.py`
- **Add Dependencies**: `uv add <package>` (updates `pyproject.toml`)
- **Sync Environment**: `uv sync`

## UI Guidelines
- Use `st.set_page_config(layout="wide")` in `main.py`.
- Modularize pages into `src/ui/` to keep `main.py` clean.
- Use Streamlit's native components for forms and data display (`st.dataframe`, `st.metric`).
