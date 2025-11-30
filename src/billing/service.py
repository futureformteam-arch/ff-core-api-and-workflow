from sqlalchemy.orm import Session
from src.billing.models import CreditLedger, Transaction, CreditType, TransactionType

class BillingService:
    def get_balance(self, db: Session, organization_id: str, credit_type: CreditType):
        """Get current balance for an organization."""
        ledger = db.query(CreditLedger).filter(
            CreditLedger.organization_id == organization_id,
            CreditLedger.credit_type == credit_type
        ).first()
        return ledger.balance if ledger else 0.0

    def record_transaction(self, db: Session, organization_id: str, credit_type: CreditType, 
                          amount: float, transaction_type: TransactionType, description: str):
        """Record a transaction and update balance."""
        # 1. Update Ledger
        ledger = db.query(CreditLedger).filter(
            CreditLedger.organization_id == organization_id,
            CreditLedger.credit_type == credit_type
        ).first()
        
        if not ledger:
            ledger = CreditLedger(
                organization_id=organization_id,
                credit_type=credit_type,
                balance=0.0
            )
            db.add(ledger)
        
        if transaction_type == TransactionType.CONSUMPTION:
            ledger.balance -= amount
        else:
            ledger.balance += amount
            
        # 2. Create Transaction Record
        transaction = Transaction(
            organization_id=organization_id,
            credit_type=credit_type,
            amount=amount,
            transaction_type=transaction_type,
            description=description
        )
        db.add(transaction)
        
        db.commit()
        return ledger.balance
