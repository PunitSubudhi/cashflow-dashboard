import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Ensure data directory exists
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'cashflow.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

Base = declarative_base()

def get_engine():
    return create_engine(DATABASE_URL, echo=False)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)

# Define models here based on the plan
class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    value = Column(String)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    description = Column(String)
    amount = Column(Float)
    type = Column(String) # 'INFLOW' or 'OUTFLOW'
    status = Column(String) # 'PROJECTED' or 'ACTUAL'
    category = Column(String)
    source = Column(String) # 'MANUAL', 'RECURRING', 'BANK_IMPORT'
    recurrence_id = Column(Integer, nullable=True)

class RecurrenceRule(Base):
    __tablename__ = 'recurrence_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String)
    amount = Column(Float)
    type = Column(String)
    frequency = Column(String) # 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    last_generated_date = Column(Date, nullable=True)

class BankImport(Base):
    __tablename__ = 'bank_imports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    import_batch_id = Column(String)
    date = Column(Date)
    description = Column(String)
    amount = Column(Float)
    status = Column(String) # 'PENDING', 'MERGED', 'POSTED', 'IGNORED'
