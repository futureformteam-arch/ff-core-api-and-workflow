from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Enum, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.core.database import Base

class AssessmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    SCORING = "SCORING"
    ANALYST_REVIEW = "ANALYST_REVIEW"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

class InvitationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

class EvidenceStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    VIRUS_SCAN_PENDING = "VIRUS_SCAN_PENDING"
    VIRUS_SCAN_CLEAN = "VIRUS_SCAN_CLEAN"
    VIRUS_SCAN_INFECTED = "VIRUS_SCAN_INFECTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class Project(Base):
    """Project can contain multiple assessments for comparison"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    organization_id = Column(String, index=True, nullable=False)
    sector = Column(String)
    project_type = Column(String)  # due_diligence, procurement, portfolio_monitoring, governance_audit
    assessment_mode = Column(String)  # a_priori, post_hoc, joint
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assessments = relationship("Assessment", back_populates="project")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # Nullable for standalone assessments
    organization_id = Column(String, index=True)
    partner_org_name = Column(String)
    sector = Column(String, nullable=False)
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.DRAFT)
    deadline = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True))
    
    # Relationships
    project = relationship("Project", back_populates="assessments")
    respondents = relationship("Respondent", back_populates="assessment")
    invitations = relationship("Invitation", back_populates="assessment")
    scores = relationship("AssessmentScore", back_populates="assessment", uselist=False)

class Invitation(Base):
    """Partner invitation tracking with secure tokens"""
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    partner_email = Column(String, nullable=False, index=True)
    partner_org_name = Column(String)
    role = Column(String, default="partner_admin")  # partner_admin, respondent
    token = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)
    
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="invitations")

class Respondent(Base):
    __tablename__ = "respondents"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    email = Column(String, index=True)
    name = Column(String)
    role = Column(String)  # e.g., "CTO", "Compliance Officer", "Finance Manager"
    seniority = Column(String)  # junior, mid, senior, executive
    assigned_questions = Column(JSON)  # List of question IDs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assessment = relationship("Assessment", back_populates="respondents")
    responses = relationship("Response", back_populates="respondent")

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    respondent_id = Column(Integer, ForeignKey("respondents.id"))
    question_id = Column(String, index=True, nullable=False)
    answer_value = Column(JSON)  # Stores the actual answer (text, choice, etc.)
    additional_context = Column(Text)  # Optional explanation
    
    submitted_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    respondent = relationship("Respondent", back_populates="responses")
    evidence_files = relationship("Evidence", back_populates="response")

class Evidence(Base):
    """Evidence file tracking with S3 storage"""
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String)  # pdf, csv, json, xlsx, jpg, png
    file_size = Column(Integer)  # bytes
    s3_key = Column(String, nullable=False, unique=True)
    s3_bucket = Column(String)
    
    uploaded_by = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    virus_scan_status = Column(Enum(EvidenceStatus), default=EvidenceStatus.VIRUS_SCAN_PENDING)
    verification_status = Column(String)  # pending, verified, rejected
    verified_by = Column(String)
    verified_at = Column(DateTime(timezone=True))
    
    # Relationships
    response = relationship("Response", back_populates="evidence_files")

class AssessmentScore(Base):
    """AI-generated scores from Intelligence Engine"""
    __tablename__ = "assessment_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), unique=True, nullable=False)
    
    overall_score = Column(Float)
    confidence = Column(Float)
    
    # Layer scores as JSON: {L1_reliability: 3.8, L2_transparency: 3.2, ...}
    layer_scores = Column(JSON)
    
    # Veto results
    veto_results = Column(JSON)
    
    # AI-generated narrative
    narrative = Column(JSON)  # {executive_summary: "...", strengths: "...", weaknesses: "...", ...}
    
    generated_at = Column(DateTime(timezone=True))
    analyst_reviewed = Column(Boolean, default=False)
    analyst_notes = Column(Text)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="scores")
