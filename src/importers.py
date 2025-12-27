"""Bank statement import utilities."""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import io


def parse_bank_statement(
    file_content: bytes,
    file_name: str,
    date_column: str = 'Date',
    description_column: str = 'Description',
    amount_column: str = 'Amount',
    date_format: str = '%Y-%m-%d'
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Parse a bank statement file (CSV or Excel) and normalize to standard format.
    
    Returns:
        Tuple of (DataFrame, error_message)
        DataFrame has columns: date, description, amount
        error_message is None if successful
    """
    try:
        # Determine file type and read
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            return None, f"Unsupported file format: {file_name}. Use CSV or Excel files."
        
        if df.empty:
            return None, "The file is empty."
        
        # Check for required columns
        available_columns = df.columns.tolist()
        
        # Try to find matching columns (case-insensitive)
        col_mapping = {}
        for target, source in [(date_column, 'Date'), (description_column, 'Description'), (amount_column, 'Amount')]:
            matched = False
            for col in available_columns:
                if col.lower() == target.lower() or col.lower() == source.lower():
                    col_mapping[source.lower()] = col
                    matched = True
                    break
            if not matched:
                return None, f"Could not find column '{target}'. Available columns: {available_columns}"
        
        # Normalize the data
        normalized = pd.DataFrame()
        
        # Parse date
        date_col = col_mapping.get('date')
        if date_col:
            try:
                normalized['date'] = pd.to_datetime(df[date_col], format=date_format, errors='coerce')
            except:
                # Try without format
                normalized['date'] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Description
        desc_col = col_mapping.get('description')
        if desc_col:
            normalized['description'] = df[desc_col].astype(str)
        
        # Amount
        amount_col = col_mapping.get('amount')
        if amount_col:
            # Handle various amount formats
            amount_series = df[amount_col]
            if amount_series.dtype == object:
                # Remove currency symbols and commas
                amount_series = amount_series.str.replace(r'[$,£€]', '', regex=True)
                amount_series = amount_series.str.replace(r'\(([^)]+)\)', r'-\1', regex=True)  # Handle (100) as -100
            normalized['amount'] = pd.to_numeric(amount_series, errors='coerce')
        
        # Drop rows with missing required data
        normalized = normalized.dropna(subset=['date', 'amount'])
        
        if normalized.empty:
            return None, "No valid data found after parsing. Check date and amount formats."
        
        # Convert date to Python date objects
        normalized['date'] = normalized['date'].dt.date
        
        return normalized, None
        
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"


def detect_columns(file_content: bytes, file_name: str) -> Dict[str, List[str]]:
    """
    Detect potential column mappings from a bank statement file.
    
    Returns dict with suggested mappings for date, description, and amount columns.
    """
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content), nrows=5)
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content), nrows=5)
        else:
            return {'error': 'Unsupported file format'}
        
        columns = df.columns.tolist()
        
        # Detect date columns
        date_keywords = ['date', 'time', 'posted', 'transaction']
        date_candidates = [c for c in columns if any(k in c.lower() for k in date_keywords)]
        
        # Detect description columns
        desc_keywords = ['description', 'memo', 'narrative', 'details', 'payee', 'name']
        desc_candidates = [c for c in columns if any(k in c.lower() for k in desc_keywords)]
        
        # Detect amount columns
        amount_keywords = ['amount', 'value', 'debit', 'credit', 'sum', 'total']
        amount_candidates = [c for c in columns if any(k in c.lower() for k in amount_keywords)]
        
        return {
            'all_columns': columns,
            'date_candidates': date_candidates or columns[:1],
            'description_candidates': desc_candidates or columns[1:2] if len(columns) > 1 else [],
            'amount_candidates': amount_candidates or columns[-1:],
            'preview': df.head().to_dict('records')
        }
        
    except Exception as e:
        return {'error': str(e)}


def generate_batch_id() -> str:
    """Generate a unique batch ID for bank imports."""
    import uuid
    return str(uuid.uuid4())[:8]
