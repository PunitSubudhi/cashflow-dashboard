"""Data export and import functionality for cashflow dashboard portability."""
import json
from datetime import date, datetime
from typing import Optional
from src.database import get_session, Setting, Transaction, RecurrenceRule, BankImport, init_db


EXPORT_VERSION = "1.0"


def _serialize_date(d: Optional[date]) -> Optional[str]:
    """Serialize a date to ISO format string."""
    return d.isoformat() if d else None


def _deserialize_date(s: Optional[str]) -> Optional[date]:
    """Deserialize an ISO format string to date."""
    return date.fromisoformat(s) if s else None


def export_all_data() -> dict:
    """
    Export all data from the database into a dictionary.
    
    Returns:
        dict: All data from settings, transactions, recurrence rules, and bank imports.
    """
    session = get_session()
    try:
        # Export settings
        settings = session.query(Setting).all()
        settings_data = [{"key": s.key, "value": s.value} for s in settings]
        
        # Export transactions
        transactions = session.query(Transaction).all()
        transactions_data = [
            {
                "id": t.id,
                "date": _serialize_date(t.date),
                "description": t.description,
                "amount": t.amount,
                "type": t.type,
                "status": t.status,
                "category": t.category,
                "source": t.source,
                "recurrence_id": t.recurrence_id
            }
            for t in transactions
        ]
        
        # Export recurrence rules
        rules = session.query(RecurrenceRule).all()
        rules_data = [
            {
                "id": r.id,
                "description": r.description,
                "amount": r.amount,
                "type": r.type,
                "frequency": r.frequency,
                "start_date": _serialize_date(r.start_date),
                "end_date": _serialize_date(r.end_date),
                "last_generated_date": _serialize_date(r.last_generated_date)
            }
            for r in rules
        ]
        
        # Export bank imports
        bank_imports = session.query(BankImport).all()
        bank_imports_data = [
            {
                "id": b.id,
                "import_batch_id": b.import_batch_id,
                "date": _serialize_date(b.date),
                "description": b.description,
                "amount": b.amount,
                "status": b.status
            }
            for b in bank_imports
        ]
        
        return {
            "export_version": EXPORT_VERSION,
            "export_timestamp": datetime.now().isoformat(),
            "data": {
                "settings": settings_data,
                "transactions": transactions_data,
                "recurrence_rules": rules_data,
                "bank_imports": bank_imports_data
            }
        }
    finally:
        session.close()


def export_to_json() -> str:
    """
    Export all data to a JSON string.
    
    Returns:
        str: JSON string containing all exported data.
    """
    data = export_all_data()
    return json.dumps(data, indent=2)


def import_from_json(json_str: str, clear_existing: bool = True) -> dict:
    """
    Import data from a JSON string.
    
    Args:
        json_str: JSON string containing exported data.
        clear_existing: If True, clears all existing data before import.
                       If False, merges with existing data (may cause conflicts).
    
    Returns:
        dict: Summary of imported records with counts.
    
    Raises:
        ValueError: If the JSON format is invalid or incompatible.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    
    # Validate structure
    if "export_version" not in data or "data" not in data:
        raise ValueError("Invalid export file format. Missing required fields.")
    
    # Version check (for future compatibility)
    version = data.get("export_version", "unknown")
    if version not in ["1.0"]:
        raise ValueError(f"Unsupported export version: {version}")
    
    export_data = data["data"]
    
    # Ensure database is initialized
    init_db()
    
    session = get_session()
    try:
        # Clear existing data if requested
        if clear_existing:
            session.query(BankImport).delete()
            session.query(Transaction).delete()
            session.query(RecurrenceRule).delete()
            session.query(Setting).delete()
            session.commit()
        
        counts = {
            "settings": 0,
            "transactions": 0,
            "recurrence_rules": 0,
            "bank_imports": 0
        }
        
        # Import settings
        for s in export_data.get("settings", []):
            setting = Setting(key=s["key"], value=s["value"])
            session.merge(setting)  # merge handles both insert and update
            counts["settings"] += 1
        
        # Import recurrence rules first (transactions may reference them)
        id_mapping_rules = {}  # old_id -> new_id
        for r in export_data.get("recurrence_rules", []):
            old_id = r.get("id")
            rule = RecurrenceRule(
                description=r["description"],
                amount=r["amount"],
                type=r["type"],
                frequency=r["frequency"],
                start_date=_deserialize_date(r["start_date"]),
                end_date=_deserialize_date(r.get("end_date")),
                last_generated_date=_deserialize_date(r.get("last_generated_date"))
            )
            session.add(rule)
            session.flush()  # Get the new ID
            if old_id:
                id_mapping_rules[old_id] = rule.id
            counts["recurrence_rules"] += 1
        
        # Import transactions
        for t in export_data.get("transactions", []):
            # Map old recurrence_id to new one
            old_recurrence_id = t.get("recurrence_id")
            new_recurrence_id = id_mapping_rules.get(old_recurrence_id) if old_recurrence_id else None
            
            txn = Transaction(
                date=_deserialize_date(t["date"]),
                description=t["description"],
                amount=t["amount"],
                type=t["type"],
                status=t["status"],
                category=t.get("category", ""),
                source=t.get("source", "MANUAL"),
                recurrence_id=new_recurrence_id
            )
            session.add(txn)
            counts["transactions"] += 1
        
        # Import bank imports
        for b in export_data.get("bank_imports", []):
            bank_import = BankImport(
                import_batch_id=b["import_batch_id"],
                date=_deserialize_date(b["date"]),
                description=b["description"],
                amount=b["amount"],
                status=b["status"]
            )
            session.add(bank_import)
            counts["bank_imports"] += 1
        
        session.commit()
        
        return {
            "success": True,
            "counts": counts,
            "export_timestamp": data.get("export_timestamp"),
            "export_version": version
        }
    
    except Exception as e:
        session.rollback()
        raise ValueError(f"Import failed: {e}")
    finally:
        session.close()


def get_data_summary() -> dict:
    """
    Get a summary of current data in the database.
    
    Returns:
        dict: Counts of records in each table.
    """
    session = get_session()
    try:
        return {
            "settings": session.query(Setting).count(),
            "transactions": session.query(Transaction).count(),
            "recurrence_rules": session.query(RecurrenceRule).count(),
            "bank_imports": session.query(BankImport).count()
        }
    finally:
        session.close()
