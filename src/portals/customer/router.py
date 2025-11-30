from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from src.core.database import get_db
from src.portals.customer.service import CustomerPortalService

router = APIRouter()
service = CustomerPortalService()

class AssessmentResponse(BaseModel):
    id: int
    organization_id: str
    sector: str
    status: str
    
    class Config:
        from_attributes = True

class AssessmentCreate(BaseModel):
    organization_id: str
    sector: str

class RespondentCreate(BaseModel):
    email: str
    role: str

@router.get("/assessments", response_model=List[AssessmentResponse])
def list_assessments(organization_id: str, db: Session = Depends(get_db)):
    return service.list_assessments(db, organization_id)

@router.post("/assessments", response_model=AssessmentResponse)
def create_assessment(assessment: AssessmentCreate, db: Session = Depends(get_db)):
    return service.create_assessment(db, assessment.organization_id, assessment.sector)

@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: int, organization_id: str, db: Session = Depends(get_db)):
    assessment = service.get_assessment_details(db, assessment_id, organization_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment

@router.post("/assessments/{assessment_id}/respondents")
def add_respondent(assessment_id: int, organization_id: str, respondent: RespondentCreate, db: Session = Depends(get_db)):
    try:
        result = service.add_respondent(db, assessment_id, organization_id, respondent.email, respondent.role)
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
