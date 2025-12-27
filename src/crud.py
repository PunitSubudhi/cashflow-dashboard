"""CRUD operations for the cashflow dashboard database."""
from datetime import date
from typing import Optional, List
from src.database import get_session, Setting, Transaction, RecurrenceRule, BankImport


# ============ Settings CRUD ============

def get_setting(key: str) -> Optional[str]:
    """Get a setting value by key."""
    session = get_session()
    try:
        setting = session.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else None
    finally:
        session.close()


def set_setting(key: str, value: str) -> None:
    """Set a setting value."""
    session = get_session()
    try:
        setting = session.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            session.add(setting)
        session.commit()
    finally:
        session.close()


def get_opening_balance() -> float:
    """Get the opening balance setting."""
    value = get_setting('opening_balance')
    return float(value) if value else 0.0


def set_opening_balance(amount: float) -> None:
    """Set the opening balance."""
    set_setting('opening_balance', str(amount))


def get_opening_date() -> Optional[date]:
    """Get the opening date setting."""
    value = get_setting('opening_date')
    return date.fromisoformat(value) if value else None


def set_opening_date(d: date) -> None:
    """Set the opening date."""
    set_setting('opening_date', d.isoformat())


# ============ Transaction CRUD ============

def create_transaction(
    transaction_date: date,
    description: str,
    amount: float,
    transaction_type: str,
    status: str = 'ACTUAL',
    category: str = '',
    source: str = 'MANUAL',
    recurrence_id: Optional[int] = None
) -> Transaction:
    """Create a new transaction."""
    session = get_session()
    try:
        txn = Transaction(
            date=transaction_date,
            description=description,
            amount=abs(amount),  # Store as positive, type indicates direction
            type=transaction_type,
            status=status,
            category=category,
            source=source,
            recurrence_id=recurrence_id
        )
        session.add(txn)
        session.commit()
        session.refresh(txn)
        return txn
    finally:
        session.close()


def get_transaction(txn_id: int) -> Optional[Transaction]:
    """Get a transaction by ID."""
    session = get_session()
    try:
        return session.query(Transaction).filter(Transaction.id == txn_id).first()
    finally:
        session.close()


def get_all_transactions(
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Transaction]:
    """Get all transactions with optional filters."""
    session = get_session()
    try:
        query = session.query(Transaction)
        if status:
            query = query.filter(Transaction.status == status)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        return query.order_by(Transaction.date.desc()).all()
    finally:
        session.close()


def update_transaction(
    txn_id: int,
    transaction_date: Optional[date] = None,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None
) -> Optional[Transaction]:
    """Update an existing transaction."""
    session = get_session()
    try:
        txn = session.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            return None
        if transaction_date is not None:
            txn.date = transaction_date
        if description is not None:
            txn.description = description
        if amount is not None:
            txn.amount = abs(amount)
        if transaction_type is not None:
            txn.type = transaction_type
        if status is not None:
            txn.status = status
        if category is not None:
            txn.category = category
        session.commit()
        session.refresh(txn)
        return txn
    finally:
        session.close()


def delete_transaction(txn_id: int) -> bool:
    """Delete a transaction by ID."""
    session = get_session()
    try:
        txn = session.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            return False
        session.delete(txn)
        session.commit()
        return True
    finally:
        session.close()


def mark_transaction_as_actual(txn_id: int) -> Optional[Transaction]:
    """Mark a projected transaction as actual (paid/received)."""
    return update_transaction(txn_id, status='ACTUAL')


# ============ Recurrence Rule CRUD ============

def create_recurrence_rule(
    description: str,
    amount: float,
    rule_type: str,
    frequency: str,
    start_date: date,
    end_date: Optional[date] = None
) -> RecurrenceRule:
    """Create a new recurrence rule."""
    session = get_session()
    try:
        rule = RecurrenceRule(
            description=description,
            amount=abs(amount),
            type=rule_type,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            last_generated_date=None
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule
    finally:
        session.close()


def get_all_recurrence_rules() -> List[RecurrenceRule]:
    """Get all recurrence rules."""
    session = get_session()
    try:
        return session.query(RecurrenceRule).order_by(RecurrenceRule.start_date).all()
    finally:
        session.close()


def get_recurrence_rule(rule_id: int) -> Optional[RecurrenceRule]:
    """Get a recurrence rule by ID."""
    session = get_session()
    try:
        return session.query(RecurrenceRule).filter(RecurrenceRule.id == rule_id).first()
    finally:
        session.close()


def update_recurrence_rule(
    rule_id: int,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    rule_type: Optional[str] = None,
    frequency: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Optional[RecurrenceRule]:
    """Update an existing recurrence rule."""
    session = get_session()
    try:
        rule = session.query(RecurrenceRule).filter(RecurrenceRule.id == rule_id).first()
        if not rule:
            return None
        if description is not None:
            rule.description = description
        if amount is not None:
            rule.amount = abs(amount)
        if rule_type is not None:
            rule.type = rule_type
        if frequency is not None:
            rule.frequency = frequency
        if start_date is not None:
            rule.start_date = start_date
        if end_date is not None:
            rule.end_date = end_date
        session.commit()
        session.refresh(rule)
        return rule
    finally:
        session.close()


def delete_recurrence_rule(rule_id: int) -> bool:
    """Delete a recurrence rule by ID."""
    session = get_session()
    try:
        rule = session.query(RecurrenceRule).filter(RecurrenceRule.id == rule_id).first()
        if not rule:
            return False
        session.delete(rule)
        session.commit()
        return True
    finally:
        session.close()


# ============ Bank Import CRUD ============

def create_bank_import(
    batch_id: str,
    import_date: date,
    description: str,
    amount: float
) -> BankImport:
    """Create a new bank import record."""
    session = get_session()
    try:
        record = BankImport(
            import_batch_id=batch_id,
            date=import_date,
            description=description,
            amount=amount,
            status='PENDING'
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def get_pending_bank_imports(batch_id: Optional[str] = None) -> List[BankImport]:
    """Get all pending bank imports, optionally filtered by batch."""
    session = get_session()
    try:
        query = session.query(BankImport).filter(BankImport.status == 'PENDING')
        if batch_id:
            query = query.filter(BankImport.import_batch_id == batch_id)
        return query.order_by(BankImport.date.desc()).all()
    finally:
        session.close()


def get_bank_imports_by_batch(batch_id: str) -> List[BankImport]:
    """Get all bank imports for a specific batch."""
    session = get_session()
    try:
        return session.query(BankImport).filter(
            BankImport.import_batch_id == batch_id
        ).order_by(BankImport.date.desc()).all()
    finally:
        session.close()


def update_bank_import_status(import_id: int, status: str) -> Optional[BankImport]:
    """Update the status of a bank import record."""
    session = get_session()
    try:
        record = session.query(BankImport).filter(BankImport.id == import_id).first()
        if not record:
            return None
        record.status = status
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def post_bank_import(import_id: int, category: str = '') -> Optional[Transaction]:
    """Post a bank import record as an actual transaction."""
    session = get_session()
    try:
        record = session.query(BankImport).filter(BankImport.id == import_id).first()
        if not record or record.status != 'PENDING':
            return None
        
        # Determine transaction type based on amount sign
        txn_type = 'INFLOW' if record.amount > 0 else 'OUTFLOW'
        
        txn = Transaction(
            date=record.date,
            description=record.description,
            amount=abs(record.amount),
            type=txn_type,
            status='ACTUAL',
            category=category,
            source='BANK_IMPORT',
            recurrence_id=None
        )
        session.add(txn)
        record.status = 'POSTED'
        session.commit()
        session.refresh(txn)
        return txn
    finally:
        session.close()


def merge_bank_imports(
    import_ids: List[int],
    description: str,
    category: str = ''
) -> Optional[Transaction]:
    """Merge multiple bank imports into a single transaction."""
    session = get_session()
    try:
        records = session.query(BankImport).filter(
            BankImport.id.in_(import_ids),
            BankImport.status == 'PENDING'
        ).all()
        
        if not records or len(records) != len(import_ids):
            return None
        
        # Calculate total amount and use the earliest date
        total_amount = sum(r.amount for r in records)
        earliest_date = min(r.date for r in records)
        txn_type = 'INFLOW' if total_amount > 0 else 'OUTFLOW'
        
        txn = Transaction(
            date=earliest_date,
            description=description,
            amount=abs(total_amount),
            type=txn_type,
            status='ACTUAL',
            category=category,
            source='BANK_IMPORT',
            recurrence_id=None
        )
        session.add(txn)
        
        # Mark all as merged
        for record in records:
            record.status = 'MERGED'
        
        session.commit()
        session.refresh(txn)
        return txn
    finally:
        session.close()


def get_unique_categories() -> List[str]:
    """Get all unique categories from transactions."""
    session = get_session()
    try:
        results = session.query(Transaction.category).distinct().all()
        return [r[0] for r in results if r[0]]
    finally:
        session.close()
