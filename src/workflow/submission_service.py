import requests
from sqlalchemy.orm import Session
from src.workflow.models import Assessment, AssessmentStatus, AssessmentScore, Response, Evidence
from src.core.config import settings
from src.core.email_service import EmailService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SubmissionService:
    """Service for assessment submission and Intelligence Engine integration"""
    
    def __init__(self):
        self.intelligence_engine_url = settings.INTELLIGENCE_ENGINE_URL
        self.email_service = EmailService()
    
    def submit_assessment(self, db: Session, assessment_id: int) -> Assessment:
        """
        Submit assessment for AI scoring
        
        Args:
            db: Database session
            assessment_id: ID of the assessment to submit
            
        Returns:
            Updated Assessment object
        """
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        if assessment.status not in [AssessmentStatus.DRAFT, AssessmentStatus.IN_PROGRESS]:
            raise ValueError(f"Assessment status is {assessment.status.value}, cannot submit")
        
        # Update status
        assessment.status = AssessmentStatus.SUBMITTED
        assessment.submitted_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Assessment {assessment_id} submitted for scoring")
        
        # Trigger scoring (in production, this would be async via Celery)
        try:
            self._trigger_scoring(db, assessment_id)
        except Exception as e:
            logger.error(f"Scoring failed for assessment {assessment_id}: {str(e)}")
            # Don't revert submission status - analyst can manually trigger
        
        # Send confirmation email
        try:
            if assessment.partner_org_name:
                # Get partner email from invitations
                invitation = assessment.invitations[0] if assessment.invitations else None
                if invitation:
                    self.email_service.send_assessment_submitted_notification(
                        to_email=invitation.partner_email,
                        partner_org_name=assessment.partner_org_name,
                        assessment_id=assessment_id
                    )
        except Exception as e:
            logger.error(f"Failed to send submission confirmation: {str(e)}")
        
        return assessment
    
    def _trigger_scoring(self, db: Session, assessment_id: int):
        """Trigger Intelligence Engine scoring"""
        
        # Prepare assessment data
        assessment_data = self._prepare_assessment_data(db, assessment_id)
        
        try:
            # Call Intelligence Engine API
            logger.info(f"Calling Intelligence Engine for assessment {assessment_id}")
            
            response = requests.post(
                f"{self.intelligence_engine_url}/api/v1/score",
                json=assessment_data,
                timeout=300  # 5 minutes
            )
            
            if response.status_code == 200:
                score_data = response.json()
                self._save_scores(db, assessment_id, score_data)
                logger.info(f"Scoring completed for assessment {assessment_id}")
            else:
                raise Exception(f"Intelligence Engine returned {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error(f"Intelligence Engine timeout for assessment {assessment_id}")
            raise Exception("Scoring timeout - assessment is queued for retry")
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Intelligence Engine")
            raise Exception("Intelligence Engine unavailable")
        except Exception as e:
            logger.error(f"Scoring error for assessment {assessment_id}: {str(e)}")
            raise
    
    def _prepare_assessment_data(self, db: Session, assessment_id: int) -> dict:
        """
        Prepare assessment data for Intelligence Engine
        
        This collects all responses and evidence files
        """
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        
        # Collect all responses with evidence
        responses_data = []
        for respondent in assessment.respondents:
            for response in respondent.responses:
                evidence_files = []
                for evidence in response.evidence_files:
                    evidence_files.append({
                        "file_name": evidence.file_name,
                        "file_type": evidence.file_type,
                        "s3_key": evidence.s3_key,
                        "s3_bucket": evidence.s3_bucket
                    })
                
                responses_data.append({
                    "question_id": response.question_id,
                    "answer": response.answer_value,
                    "context": response.additional_context,
                    "evidence": evidence_files,
                    "respondent_role": respondent.role
                })
        
        return {
            "assessment_id": assessment_id,
            "organization_id": assessment.organization_id,
            "sector": assessment.sector,
            "responses": responses_data
        }
    
    def _save_scores(self, db: Session, assessment_id: int, score_data: dict):
        """Save AI-generated scores to database"""
        
        # Check if scores already exist
        existing_score = db.query(AssessmentScore).filter(
            AssessmentScore.assessment_id == assessment_id
        ).first()
        
        if existing_score:
            # Update existing
            existing_score.overall_score = score_data.get("overall_score")
            existing_score.confidence = score_data.get("confidence")
            existing_score.layer_scores = score_data.get("layer_scores")
            existing_score.veto_results = score_data.get("veto_results")
            existing_score.narrative = score_data.get("narrative")
            existing_score.generated_at = datetime.utcnow()
        else:
            # Create new
            score_record = AssessmentScore(
                assessment_id=assessment_id,
                overall_score=score_data.get("overall_score"),
                confidence=score_data.get("confidence"),
                layer_scores=score_data.get("layer_scores"),
                veto_results=score_data.get("veto_results"),
                narrative=score_data.get("narrative"),
                generated_at=datetime.utcnow(),
                analyst_reviewed=False
            )
            db.add(score_record)
        
        # Update assessment status
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        assessment.status = AssessmentStatus.ANALYST_REVIEW
        
        db.commit()
        
        logger.info(f"Scores saved for assessment {assessment_id}")
    
    def get_assessment_scores(self, db: Session, assessment_id: int) -> AssessmentScore:
        """Get scores for an assessment"""
        scores = db.query(AssessmentScore).filter(
            AssessmentScore.assessment_id == assessment_id
        ).first()
        
        if not scores:
            raise ValueError(f"No scores found for assessment {assessment_id}")
        
        return scores
