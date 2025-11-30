from sqlalchemy.orm import Session
from src.workflow.models import (
    Assessment, AssessmentStatus, Respondent, Response, Evidence,
    Project, Invitation, AssessmentScore
)
from src.workflow.invitation_service import InvitationService
from src.workflow.submission_service import SubmissionService
from src.core.s3_service import S3Service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WorkflowService:
    """Enhanced workflow service for managing assessments"""
    
    def __init__(self):
        self.invitation_service = InvitationService()
        self.submission_service = SubmissionService()
        self.s3_service = S3Service()
    
    # ===== PROJECT MANAGEMENT =====
    
    def create_project(
        self,
        db: Session,
        name: str,
        organization_id: str,
        description: str = None,
        sector: str = None,
        project_type: str = None,
        created_by: str = None
    ) -> Project:
        """Create a new project"""
        project = Project(
            name=name,
            description=description,
            organization_id=organization_id,
            sector=sector,
            project_type=project_type,
            created_by=created_by
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        logger.info(f"Created project {project.id}: {name}")
        return project
    
    def get_project(self, db: Session, project_id: int) -> Project:
        """Get project by ID"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project
    
    def list_projects(self, db: Session, organization_id: str) -> list[Project]:
        """List all projects for an organization"""
        return db.query(Project).filter(
            Project.organization_id == organization_id
        ).order_by(Project.created_at.desc()).all()
    
    # ===== ASSESSMENT MANAGEMENT =====
    
    def create_assessment(
        self,
        db: Session,
        organization_id: str,
        sector: str,
        project_id: int = None,
        partner_org_name: str = None,
        deadline: datetime = None
    ) -> Assessment:
        """Create a new assessment"""
        assessment = Assessment(
            project_id=project_id,
            organization_id=organization_id,
            partner_org_name=partner_org_name,
            sector=sector,
            status=AssessmentStatus.DRAFT,
            deadline=deadline
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        logger.info(f"Created assessment {assessment.id}")
        return assessment
    
    def get_assessment(self, db: Session, assessment_id: int) -> Assessment:
        """Get assessment by ID with all relationships"""
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        return assessment
    
    def list_assessments(
        self,
        db: Session,
        organization_id: str = None,
        project_id: int = None,
        status: AssessmentStatus = None
    ) -> list[Assessment]:
        """List assessments with optional filters"""
        query = db.query(Assessment)
        
        if organization_id:
            query = query.filter(Assessment.organization_id == organization_id)
        if project_id:
            query = query.filter(Assessment.project_id == project_id)
        if status:
            query = query.filter(Assessment.status == status)
        
        return query.order_by(Assessment.created_at.desc()).all()
    
    def update_assessment_status(
        self,
        db: Session,
        assessment_id: int,
        status: AssessmentStatus
    ) -> Assessment:
        """Update assessment status"""
        assessment = self.get_assessment(db, assessment_id)
        assessment.status = status
        db.commit()
        db.refresh(assessment)
        
        logger.info(f"Updated assessment {assessment_id} status to {status.value}")
        return assessment
    
    # ===== RESPONDENT MANAGEMENT =====
    
    def add_respondent(
        self,
        db: Session,
        assessment_id: int,
        email: str,
        role: str,
        name: str = None,
        seniority: str = None,
        assigned_questions: list = None
    ) -> Respondent:
        """Add a respondent to an assessment"""
        respondent = Respondent(
            assessment_id=assessment_id,
            email=email,
            name=name,
            role=role,
            seniority=seniority,
            assigned_questions=assigned_questions or []
        )
        db.add(respondent)
        db.commit()
        db.refresh(respondent)
        
        logger.info(f"Added respondent {email} to assessment {assessment_id}")
        return respondent
    
    def get_respondent(self, db: Session, respondent_id: int) -> Respondent:
        """Get respondent by ID"""
        respondent = db.query(Respondent).filter(Respondent.id == respondent_id).first()
        if not respondent:
            raise ValueError(f"Respondent {respondent_id} not found")
        return respondent
    
    # ===== RESPONSE MANAGEMENT =====
    
    def create_response(
        self,
        db: Session,
        respondent_id: int,
        question_id: str,
        answer_value: dict,
        additional_context: str = None
    ) -> Response:
        """Create or update a response"""
        # Check if response already exists
        existing_response = db.query(Response).filter(
            Response.respondent_id == respondent_id,
            Response.question_id == question_id
        ).first()
        
        if existing_response:
            # Update existing response
            existing_response.answer_value = answer_value
            existing_response.additional_context = additional_context
            existing_response.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_response)
            return existing_response
        else:
            # Create new response
            response = Response(
                respondent_id=respondent_id,
                question_id=question_id,
                answer_value=answer_value,
                additional_context=additional_context
            )
            db.add(response)
            db.commit()
            db.refresh(response)
            
            logger.info(f"Created response for question {question_id}")
            return response
    
    def submit_response(self, db: Session, response_id: int) -> Response:
        """Mark response as submitted"""
        response = db.query(Response).filter(Response.id == response_id).first()
        if not response:
            raise ValueError(f"Response {response_id} not found")
        
        response.submitted_at = datetime.utcnow()
        db.commit()
        db.refresh(response)
        
        return response
    
    # ===== EVIDENCE MANAGEMENT =====
    
    def create_evidence_record(
        self,
        db: Session,
        response_id: int,
        file_name: str,
        file_type: str,
        file_size: int,
        s3_key: str,
        s3_bucket: str,
        uploaded_by: str
    ) -> Evidence:
        """Create evidence record after file upload"""
        evidence = Evidence(
            response_id=response_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            s3_key=s3_key,
            s3_bucket=s3_bucket,
            uploaded_by=uploaded_by
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        
        logger.info(f"Created evidence record for {file_name}")
        return evidence
    
    def get_evidence(self, db: Session, evidence_id: int) -> Evidence:
        """Get evidence by ID"""
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found")
        return evidence
