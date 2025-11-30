from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from src.core.database import get_db
from src.portals.respondent.service import RespondentPortalService

router = APIRouter()
service = RespondentPortalService()

class ResponseSubmit(BaseModel):
    question_id: str
    answer_value: Dict[str, Any]
    evidence_files: List[str] = []

class UploadRequest(BaseModel):
    filename: str

@router.get("/context/{respondent_id}")
def get_context(respondent_id: int, db: Session = Depends(get_db)):
    context = service.get_respondent_context(db, respondent_id)
    if not context:
        raise HTTPException(status_code=404, detail="Respondent not found")
    return context

@router.post("/responses/{respondent_id}")
def submit_response(respondent_id: int, response: ResponseSubmit, db: Session = Depends(get_db)):
    return service.submit_response(db, respondent_id, response.question_id, response.answer_value, response.evidence_files)

@router.post("/upload/{respondent_id}")
def get_upload_url(respondent_id: int, request: UploadRequest):
    return service.get_upload_url(respondent_id, request.filename)
