import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.core.config import settings
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.frontend_url = settings.FRONTEND_URL
    
    def send_partner_invitation(
        self,
        to_email: str,
        partner_org_name: str,
        project_name: str,
        assessment_id: int,
        invitation_token: str,
        deadline: str
    ):
        """Send invitation email to partner organization"""
        
        accept_url = f"{self.frontend_url}/partner/accept/{invitation_token}"
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #fafafa;">
            <div style="background: white; border-radius: 12px; padding: 40px; border: 1px solid #e5e7eb;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 16px;">
                        <span style="color: white; font-weight: 700; font-size: 20px;">FF</span>
                    </div>
                    <h1 style="font-size: 24px; font-weight: 600; color: #111827; margin: 0;">FutureForm Trust Assessment</h1>
                </div>
                
                <p style="font-size: 15px; color: #374151; line-height: 1.6; margin-bottom: 20px;">
                    Hello <strong>{{ partner_org_name }}</strong>,
                </p>
                
                <p style="font-size: 15px; color: #374151; line-height: 1.6; margin-bottom: 20px;">
                    You have been invited to complete a Trust Diagnostic assessment for <strong>{{ project_name }}</strong>.
                </p>
                
                <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 24px 0;">
                    <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">What You Need to Do:</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #374151; font-size: 14px; line-height: 1.8;">
                        <li>Review the assessment requirements</li>
                        <li>Assign team members to respond to role-specific questions</li>
                        <li>Upload supporting evidence documents</li>
                        <li>Submit your responses by the deadline</li>
                    </ul>
                </div>
                
                <p style="font-size: 15px; color: #374151; line-height: 1.6; margin-bottom: 8px;">
                    <strong>Deadline:</strong> {{ deadline }}
                </p>
                
                <p style="font-size: 15px; color: #374151; line-height: 1.6; margin-bottom: 30px;">
                    <strong>Estimated Time:</strong> 60-90 minutes (you can save and return anytime)
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ accept_url }}" 
                       style="background: #2563eb; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 500; font-size: 15px;">
                        Accept & Start Assessment
                    </a>
                </div>
                
                <p style="font-size: 13px; color: #6b7280; line-height: 1.6; margin-top: 30px;">
                    If you have questions or need assistance, please contact us at 
                    <a href="mailto:support@futureform.africa" style="color: #2563eb; text-decoration: none;">support@futureform.africa</a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                
                <p style="color: #9ca3af; font-size: 12px; text-align: center; margin: 0;">
                    © 2025 FutureForm. All rights reserved.<br>
                    FutureForm Trust Diagnostic™ is a proprietary tool.
                </p>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(
            partner_org_name=partner_org_name,
            project_name=project_name,
            deadline=deadline,
            accept_url=accept_url
        )
        
        self._send_email(
            to_email=to_email,
            subject=f"Trust Assessment Invitation - {project_name}",
            html_content=html_content
        )
        
        logger.info(f"Sent partner invitation to {to_email}")
    
    def send_assessment_submitted_notification(
        self,
        to_email: str,
        partner_org_name: str,
        assessment_id: int
    ):
        """Notify partner that assessment was successfully submitted"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <body style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: white; border-radius: 12px; padding: 40px; border: 1px solid #e5e7eb;">
                <h2 style="color: #111827; font-size: 24px; margin-bottom: 20px;">Assessment Submitted Successfully</h2>
                
                <p style="font-size: 15px; color: #374151; line-height: 1.6;">
                    Thank you, <strong>{{ partner_org_name }}</strong>!
                </p>
                
                <p style="font-size: 15px; color: #374151; line-height: 1.6;">
                    Your assessment (ID: {{ assessment_id }}) has been successfully submitted.
                </p>
                
                <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 16px; margin: 24px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px; color: #1e40af; font-weight: 500;">What happens next:</p>
                    <ul style="margin: 12px 0 0 0; padding-left: 20px; color: #1e40af; font-size: 14px;">
                        <li>Our team will review your evidence (2-5 business days)</li>
                        <li>We may request clarifications or additional documentation</li>
                        <li>You'll receive your preliminary Trust Profile once validation is complete</li>
                    </ul>
                </div>
                
                <p style="font-size: 13px; color: #6b7280; margin-top: 30px;">
                    Questions? Contact us at support@futureform.africa
                </p>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(
            partner_org_name=partner_org_name,
            assessment_id=assessment_id
        )
        
        self._send_email(
            to_email=to_email,
            subject=f"Assessment #{assessment_id} Submitted Successfully",
            html_content=html_content
        )
        
        logger.info(f"Sent submission confirmation to {to_email}")
    
    def _send_email(self, to_email: str, subject: str, html_content: str):
        """Internal method to send email via SMTP"""
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise Exception(f"Failed to send email: {str(e)}")
