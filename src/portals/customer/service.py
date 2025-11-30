from sqlalchemy.orm import Session
from src.workflow.models import Assessment, AssessmentStatus
from src.workflow.service import WorkflowService
from src.billing.service import BillingService
from src.billing.models import CreditType, TransactionType

class CustomerPortalService:
    def __init__(self):
        self.workflow_service = WorkflowService()
        self.billing_service = BillingService()

    def list_assessments(self, db: Session, organization_id: str):
        """List all assessments for an organization."""
        return db.query(Assessment).filter(Assessment.organization_id == organization_id).all()

    def get_assessment_details(self, db: Session, assessment_id: int, organization_id: str):
        """Get details of a specific assessment."""
        assessment = self.workflow_service.get_assessment(db, assessment_id)
        if assessment and assessment.organization_id == organization_id:
            return assessment
        return None

    def create_assessment(self, db: Session, organization_id: str, sector: str):
        """Create a new assessment (wraps workflow service)."""
        # In a real scenario, we might check for credits here or just allow creation
        return self.workflow_service.create_assessment(db, organization_id, sector)

    def add_respondent(self, db: Session, assessment_id: int, organization_id: str, email: str, role: str):
        """Add a respondent to an assessment."""
        # Verify ownership
        assessment = self.get_assessment_details(db, assessment_id, organization_id)
        if not assessment:
            return None
        
        # Check credits (Example: 1 RC per respondent)
        balance = self.billing_service.get_balance(db, organization_id, CreditType.RESPONDENT_CREDIT)
        if balance < 1:
            raise ValueError("Insufficient Respondent Credits")

        # Deduct credit
        self.billing_service.record_transaction(
            db, organization_id, CreditType.RESPONDENT_CREDIT, 1.0, 
            TransactionType.CONSUMPTION, f"Added respondent {email} to assessment {assessment_id}"
        )

        # Add respondent
        return self.workflow_service.add_respondent(db, assessment_id, email, role)
