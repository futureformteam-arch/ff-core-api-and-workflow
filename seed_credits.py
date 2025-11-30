import sys
import os
sys.path.append(os.getcwd())
from src.core.database import SessionLocal
from src.billing.service import BillingService
from src.billing.models import CreditType, TransactionType

def seed_credits():
    db = SessionLocal()
    service = BillingService()
    organization_id = "org_portal_test"
    
    print(f"Seeding credits for {organization_id}...")
    balance = service.record_transaction(
        db, 
        organization_id, 
        CreditType.RESPONDENT_CREDIT, 
        10.0, 
        TransactionType.PURCHASE, 
        "Initial seed for testing"
    )
    print(f"New Balance: {balance}")
    db.close()

if __name__ == "__main__":
    seed_credits()
