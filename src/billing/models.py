from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Float
from sqlalchemy.sql import func
import enum
from src.core.database import Base

class CreditType(str, enum.Enum):
    RESPONDENT_CREDIT = "RC"
    EVIDENCE_CREDIT = "EC"

class TransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    CONSUMPTION = "CONSUMPTION"
    REFUND = "REFUND"

class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, index=True)
    credit_type = Column(Enum(CreditType), nullable=False)
    balance = Column(Float, default=0.0)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, index=True)
    credit_type = Column(Enum(CreditType), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    description = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
