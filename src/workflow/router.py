from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from src.core.database import get_db
from src.workflow.service import WorkflowService
from src.workflow.invitation_service import InvitationService
from src.workflow.submission_service import SubmissionService
from src.core.s3_service import S3Service
from src.core.s3_service import S3Service
from src.workflow.models import AssessmentStatus
from src.core.security import get_current_user, TokenData

router = APIRouter()
workflow_service = WorkflowService()
invitation_service = InvitationService()
submission_service = SubmissionService()
s3_service = S3Service()

# ===== PYDANTIC MODELS =====

class ProjectCreate(BaseModel):
    name: str
    organization_id: str
    description: Optional[str] = None
    sector: Optional[str] = None
    project_type: Optional[str] = None
    created_by: Optional[str] = None

class AssessmentCreate(BaseModel):
    organization_id: str
    sector: str
    project_id: Optional[int] = None
    partner_org_name: Optional[str] = None
    deadline: Optional[datetime] = None

class RespondentCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: str
    seniority: Optional[str] = None
    assigned_questions: Optional[List[str]] = None

class ResponseCreate(BaseModel):
    respondent_id: int
    question_id: str
    answer_value: dict
    additional_context: Optional[str] = None

class InvitationCreate(BaseModel):
    assessment_id: int
    partner_email: EmailStr
    partner_org_name: str
    role: str = "partner_admin"
    deadline_days: int = 14

class EvidenceUploadRequest(BaseModel):
    assessment_id: int
    evidence_type: str
    file_name: str
    content_type: str = "application/octet-stream"

class EvidenceCreate(BaseModel):
    response_id: int
    file_name: str
    file_type: str
    file_size: int
    s3_key: str
    s3_bucket: str
    uploaded_by: str

# ===== PROJECT ENDPOINTS =====

@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """Create a new project"""
    try:
        return workflow_service.create_project(
            db=db,
            name=project.name,
            organization_id=project.organization_id,
            description=project.description,
            sector=project.sector,
            project_type=project.project_type,
            created_by=project.created_by
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """Get project by ID"""
    try:
        return workflow_service.get_project(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/projects")
def list_projects(organization_id: str, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """List all projects for an organization"""
    return workflow_service.list_projects(db, organization_id)

# ===== ASSESSMENT ENDPOINTS =====

@router.post("/assessments", status_code=status.HTTP_201_CREATED)
def create_assessment(assessment: AssessmentCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """Create a new assessment"""
    try:
        return workflow_service.create_assessment(
            db=db,
            organization_id=assessment.organization_id,
            sector=assessment.sector,
            project_id=assessment.project_id,
            partner_org_name=assessment.partner_org_name,
            deadline=assessment.deadline
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/assessments/{assessment_id}")
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    # Note: This is used by both User Dashboard (Auth) and Partner Dashboard (Public/Token)
    # For MVP, leaving public or we need dual auth support. 
    # To keep it simple for Partner Dashboard which doesn't have JWT, we'll leave it open or check for token in query param if we wanted to be strict.
    # But User Dashboard sends token. 
    # Let's make it optional or leave it open for now to avoid breaking Partner Dashboard.
    pass
    """Get assessment by ID with all details"""
    try:
        return workflow_service.get_assessment(db, assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/assessments")
def list_assessments(
    organization_id: Optional[str] = None,
    project_id: Optional[int] = None,
    status: Optional[AssessmentStatus] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List assessments with optional filters"""
    return workflow_service.list_assessments(
        db=db,
        organization_id=organization_id,
        project_id=project_id,
        status=status
    )

# ===== INVITATION ENDPOINTS =====

@router.post("/invitations", status_code=status.HTTP_201_CREATED)
def create_invitation(invitation: InvitationCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """Create and send partner invitation"""
    try:
        return invitation_service.create_invitation(
            db=db,
            assessment_id=invitation.assessment_id,
            partner_email=invitation.partner_email,
            partner_org_name=invitation.partner_org_name,
            role=invitation.role,
            deadline_days=invitation.deadline_days
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/invitations/{token}/accept")
def accept_invitation(token: str, db: Session = Depends(get_db)):
    """Accept partner invitation"""
    try:
        return invitation_service.accept_invitation(db, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/invitations/{token}/decline")
def decline_invitation(token: str, reason: Optional[str] = None, db: Session = Depends(get_db)):
    """Decline partner invitation"""
    try:
        return invitation_service.decline_invitation(db, token, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/invitations/{token}")
def get_invitation(token: str, db: Session = Depends(get_db)):
    """Get invitation details by token"""
    try:
        return invitation_service.get_invitation_by_token(db, token)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ===== RESPONDENT ENDPOINTS =====

@router.post("/respondents", status_code=status.HTTP_201_CREATED)
def add_respondent(respondent: RespondentCreate, assessment_id: int, db: Session = Depends(get_db)):
    """Add a respondent to an assessment"""
    try:
        return workflow_service.add_respondent(
            db=db,
            assessment_id=assessment_id,
            email=respondent.email,
            name=respondent.name,
            role=respondent.role,
            seniority=respondent.seniority,
            assigned_questions=respondent.assigned_questions
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/respondents/{respondent_id}")
def get_respondent(respondent_id: int, db: Session = Depends(get_db)):
    """Get respondent by ID"""
    try:
        return workflow_service.get_respondent(db, respondent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ===== RESPONSE ENDPOINTS =====

@router.post("/responses", status_code=status.HTTP_201_CREATED)
def create_response(response: ResponseCreate, db: Session = Depends(get_db)):
    """Create or update a response"""
    try:
        return workflow_service.create_response(
            db=db,
            respondent_id=response.respondent_id,
            question_id=response.question_id,
            answer_value=response.answer_value,
            additional_context=response.additional_context
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/responses/{response_id}/submit")
def submit_response(response_id: int, db: Session = Depends(get_db)):
    """Mark response as submitted"""
    try:
        return workflow_service.submit_response(db, response_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ===== EVIDENCE ENDPOINTS =====

@router.post("/evidence/upload-url")
def get_evidence_upload_url(request: EvidenceUploadRequest):
    """Generate presigned URL for evidence upload"""
    try:
        return s3_service.generate_presigned_upload_url(
            assessment_id=request.assessment_id,
            evidence_type=request.evidence_type,
            file_name=request.file_name,
            content_type=request.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/evidence", status_code=status.HTTP_201_CREATED)
def create_evidence(evidence: EvidenceCreate, db: Session = Depends(get_db)):
    """Create evidence record after file upload"""
    try:
        return workflow_service.create_evidence_record(
            db=db,
            response_id=evidence.response_id,
            file_name=evidence.file_name,
            file_type=evidence.file_type,
            file_size=evidence.file_size,
            s3_key=evidence.s3_key,
            s3_bucket=evidence.s3_bucket,
            uploaded_by=evidence.uploaded_by
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: int, db: Session = Depends(get_db)):
    """Get evidence by ID"""
    try:
        evidence = workflow_service.get_evidence(db, evidence_id)
        # Generate download URL
        download_url = s3_service.generate_presigned_download_url(evidence.s3_key)
        return {
            **evidence.__dict__,
            "download_url": download_url
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ===== SUBMISSION ENDPOINTS =====

@router.post("/assessments/{assessment_id}/submit")
def submit_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Submit assessment for AI scoring"""
    try:
        return submission_service.submit_assessment(db, assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assessments/{assessment_id}/scores")
def get_assessment_scores(assessment_id: int, db: Session = Depends(get_db)):
    """Get AI-generated scores for an assessment"""
    try:
        return submission_service.get_assessment_scores(db, assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
