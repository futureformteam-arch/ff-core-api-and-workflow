from sqlalchemy.orm import Session
from src.workflow.models import Invitation, Assessment, InvitationStatus
from src.core.email_service import EmailService
from datetime import datetime, timedelta
import secrets
import logging

logger = logging.getLogger(__name__)

class InvitationService:
    """Service for managing partner invitations"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    def create_invitation(
        self,
        db: Session,
        assessment_id: int,
        partner_email: str,
        partner_org_name: str,
        role: str = "partner_admin",
        deadline_days: int = 14
    ) -> Invitation:
        """
        Create and send partner invitation
        
        Args:
            db: Database session
            assessment_id: ID of the assessment
            partner_email: Partner's email address
            partner_org_name: Partner organization name
            role: Role type (partner_admin or respondent)
            deadline_days: Days until invitation expires
            
        Returns:
            Created Invitation object
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Create invitation record
        invitation = Invitation(
            assessment_id=assessment_id,
            partner_email=partner_email,
            partner_org_name=partner_org_name,
            role=role,
            token=token,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=deadline_days)
        )
        
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        
        # Get assessment details for email
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        # Determine project name
        project_name = f"Assessment #{assessment_id}"
        if assessment.project:
            project_name = assessment.project.name
        
        # Send invitation email
        try:
            self.email_service.send_partner_invitation(
                to_email=partner_email,
                partner_org_name=partner_org_name,
                project_name=project_name,
                assessment_id=assessment_id,
                invitation_token=token,
                deadline=invitation.expires_at.strftime("%B %d, %Y")
            )
            logger.info(f"Invitation sent to {partner_email} for assessment {assessment_id}")
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            # Don't fail the invitation creation if email fails
            # Could implement retry logic here
        
        return invitation
    
    def accept_invitation(self, db: Session, token: str) -> Invitation:
        """
        Accept partner invitation
        
        Args:
            db: Database session
            token: Invitation token
            
        Returns:
            Accepted Invitation object
        """
        invitation = db.query(Invitation).filter(Invitation.token == token).first()
        
        if not invitation:
            raise ValueError("Invalid invitation token")
        
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError(f"Invitation already {invitation.status.value.lower()}")
        
        if datetime.utcnow() > invitation.expires_at:
            invitation.status = InvitationStatus.EXPIRED
            db.commit()
            raise ValueError("Invitation has expired")
        
        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()
        
        db.commit()
        db.refresh(invitation)
        
        logger.info(f"Invitation {invitation.id} accepted by {invitation.partner_email}")
        
        return invitation
    
    def decline_invitation(self, db: Session, token: str, reason: str = None) -> Invitation:
        """
        Decline partner invitation
        
        Args:
            db: Database session
            token: Invitation token
            reason: Optional decline reason
            
        Returns:
            Declined Invitation object
        """
        invitation = db.query(Invitation).filter(Invitation.token == token).first()
        
        if not invitation:
            raise ValueError("Invalid invitation token")
        
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError(f"Invitation already {invitation.status.value.lower()}")
        
        invitation.status = InvitationStatus.DECLINED
        
        db.commit()
        db.refresh(invitation)
        
        logger.info(f"Invitation {invitation.id} declined by {invitation.partner_email}")
        
        return invitation
    
    def get_invitation_by_token(self, db: Session, token: str) -> Invitation:
        """Get invitation by token"""
        invitation = db.query(Invitation).filter(Invitation.token == token).first()
        
        if not invitation:
            raise ValueError("Invalid invitation token")
        
        return invitation
    
    def resend_invitation(self, db: Session, invitation_id: int) -> Invitation:
        """Resend invitation email"""
        invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
        
        if not invitation:
            raise ValueError(f"Invitation {invitation_id} not found")
        
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError("Can only resend pending invitations")
        
        # Get assessment details
        assessment = invitation.assessment
        project_name = f"Assessment #{assessment.id}"
        if assessment.project:
            project_name = assessment.project.name
        
        # Resend email
        self.email_service.send_partner_invitation(
            to_email=invitation.partner_email,
            partner_org_name=invitation.partner_org_name,
            project_name=project_name,
            assessment_id=assessment.id,
            invitation_token=invitation.token,
            deadline=invitation.expires_at.strftime("%B %d, %Y")
        )
        
        logger.info(f"Resent invitation {invitation_id} to {invitation.partner_email}")
        
        return invitation
