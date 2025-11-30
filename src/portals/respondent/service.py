from sqlalchemy.orm import Session
from src.workflow.models import Response, Respondent
from src.core.storage import StorageService
import uuid

class RespondentPortalService:
    def __init__(self):
        self.storage_service = StorageService()

    def get_respondent_context(self, db: Session, respondent_id: int):
        """Get context for a respondent (assessment info)."""
        return db.query(Respondent).filter(Respondent.id == respondent_id).first()

    def submit_response(self, db: Session, respondent_id: int, question_id: str, answer_value: dict, evidence_files: list):
        """Submit a response to a question."""
        # Check if response exists
        response = db.query(Response).filter(
            Response.respondent_id == respondent_id,
            Response.question_id == question_id
        ).first()

        if not response:
            response = Response(
                respondent_id=respondent_id,
                question_id=question_id
            )
            db.add(response)
        
        response.answer_value = answer_value
        response.evidence_files = evidence_files
        db.commit()
        db.refresh(response)
        return response

    def get_upload_url(self, respondent_id: int, filename: str):
        """Generate a presigned URL for uploading evidence."""
        key = f"evidence/{respondent_id}/{uuid.uuid4()}_{filename}"
        url = self.storage_service.generate_presigned_url(key)
        return {"upload_url": url, "key": key}
