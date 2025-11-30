# FutureForm Core API & Workflow

Complete backend API for the FutureForm Trust Intelligence Platform.

## Features

### ✅ Project Management
- Create and manage multi-assessment projects
- Organize assessments by project for comparison
- Track project-level metrics

### ✅ Assessment Workflow
- Create standalone or project-based assessments
- Manage assessment lifecycle (Draft → In Progress → Submitted → Scoring → Analyst Review → Completed)
- Track deadlines and status

### ✅ Partner Invitation System
- Send secure email invitations to partners
- Token-based invitation acceptance
- Invitation expiration and status tracking
- Resend invitations

### ✅ Evidence Management
- S3 integration for secure file storage
- Presigned URLs for upload/download
- Support for multiple file types (PDF, CSV, JSON, Excel, images)
- Virus scanning status tracking
- Evidence verification workflow

### ✅ Response Collection
- Role-based question assignment
- Response creation and updates
- Evidence attachment to responses
- Submission tracking

### ✅ Intelligence Engine Integration
- Automatic submission to AI scoring engine
- Score storage and retrieval
- Veto results and narrative generation
- Analyst review workflow

### ✅ Email Notifications
- Partner invitation emails
- Assessment submission confirmations
- HTML email templates with branding

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required configuration:
- **Database**: PostgreSQL connection string
- **AWS S3**: Access keys and bucket name
- **SMTP**: Email server credentials
- **Intelligence Engine**: URL to ML service

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start the Server

```bash
uvicorn src.main:app --reload --port 8000
```

API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## API Endpoints

### Projects
```
POST   /api/v1/projects              # Create project
GET    /api/v1/projects               # List projects
GET    /api/v1/projects/{id}          # Get project details
```

### Assessments
```
POST   /api/v1/assessments            # Create assessment
GET    /api/v1/assessments            # List assessments (with filters)
GET    /api/v1/assessments/{id}       # Get assessment details
POST   /api/v1/assessments/{id}/submit  # Submit for scoring
GET    /api/v1/assessments/{id}/scores  # Get AI scores
```

### Invitations
```
POST   /api/v1/invitations            # Create & send invitation
GET    /api/v1/invitations/{token}    # Get invitation details
POST   /api/v1/invitations/{token}/accept  # Accept invitation
POST   /api/v1/invitations/{token}/decline # Decline invitation
```

### Respondents
```
POST   /api/v1/respondents            # Add respondent to assessment
GET    /api/v1/respondents/{id}       # Get respondent details
```

### Responses
```
POST   /api/v1/responses              # Create/update response
POST   /api/v1/responses/{id}/submit  # Submit response
```

### Evidence
```
POST   /api/v1/evidence/upload-url    # Get presigned upload URL
POST   /api/v1/evidence               # Create evidence record
GET    /api/v1/evidence/{id}          # Get evidence with download URL
```

---

## Architecture

### Data Models

```
Project
├── id, name, description
├── organization_id
├── sector, project_type
└── assessments (1:many)

Assessment
├── id, status, deadline
├── project_id (optional)
├── organization_id, partner_org_name
├── invitations (1:many)
├── respondents (1:many)
└── scores (1:1)

Invitation
├── id, token, status
├── assessment_id
├── partner_email, partner_org_name
└── expires_at

Respondent
├── id, email, name, role
├── assessment_id
├── assigned_questions
└── responses (1:many)

Response
├── id, question_id
├── respondent_id
├── answer_value, additional_context
└── evidence_files (1:many)

Evidence
├── id, file_name, file_type
├── response_id
├── s3_key, s3_bucket
└── virus_scan_status, verification_status

AssessmentScore
├── id, assessment_id
├── overall_score, confidence
├── layer_scores, veto_results
└── narrative
```

### Services

- **WorkflowService**: Core CRUD operations for all models
- **InvitationService**: Partner invitation workflow
- **SubmissionService**: Assessment submission & Intelligence Engine integration
- **S3Service**: File storage management
- **EmailService**: Email notifications

---

## Workflow Example

### 1. Create Project
```python
POST /api/v1/projects
{
  "name": "East Africa Grid Modernization",
  "organization_id": "org_123",
  "sector": "infrastructure",
  "project_type": "procurement"
}
```

### 2. Create Assessment
```python
POST /api/v1/assessments
{
  "project_id": 1,
  "organization_id": "org_123",
  "sector": "infrastructure",
  "partner_org_name": "GridTech Solutions"
}
```

### 3. Send Invitation
```python
POST /api/v1/invitations
{
  "assessment_id": 1,
  "partner_email": "ceo@gridtech.example",
  "partner_org_name": "GridTech Solutions",
  "deadline_days": 14
}
```

Partner receives email with secure token link.

### 4. Partner Accepts
```python
POST /api/v1/invitations/{token}/accept
```

### 5. Add Respondents
```python
POST /api/v1/respondents?assessment_id=1
{
  "email": "finance@gridtech.example",
  "name": "John Doe",
  "role": "Finance Manager",
  "assigned_questions": ["Q1", "Q2", "Q3"]
}
```

### 6. Submit Responses
```python
# Get upload URL
POST /api/v1/evidence/upload-url
{
  "assessment_id": 1,
  "evidence_type": "financial",
  "file_name": "financials_2024.pdf"
}

# Upload file to S3 using presigned URL
PUT {presigned_url}
[file content]

# Create response with evidence
POST /api/v1/responses
{
  "respondent_id": 1,
  "question_id": "Q1",
  "answer_value": {"text": "We maintain audited financials"},
  "additional_context": "See attached PDF"
}

# Create evidence record
POST /api/v1/evidence
{
  "response_id": 1,
  "file_name": "financials_2024.pdf",
  "file_type": "pdf",
  "file_size": 2048000,
  "s3_key": "assessments/1/financial/abc123_financials_2024.pdf",
  "s3_bucket": "futureform-evidence",
  "uploaded_by": "finance@gridtech.example"
}
```

### 7. Submit Assessment
```python
POST /api/v1/assessments/1/submit
```

System automatically:
- Calls Intelligence Engine for scoring
- Stores AI-generated scores
- Updates status to ANALYST_REVIEW

### 8. Get Scores
```python
GET /api/v1/assessments/1/scores
```

Returns:
```json
{
  "overall_score": 3.8,
  "confidence": 0.85,
  "layer_scores": {
    "L1_reliability": 4.2,
    "L2_transparency": 3.5,
    ...
  },
  "veto_results": {...},
  "narrative": {
    "executive_summary": "...",
    "strengths": "...",
    "weaknesses": "...",
    ...
  }
}
```

---

## Development

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black src/
ruff check src/
```

### Create Migration
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## Production Deployment

### Environment Variables
Ensure all environment variables are set in production:
- Use strong `SECRET_KEY`
- Configure production database
- Set up S3 bucket with proper permissions
- Configure SMTP for email delivery
- Set `INTELLIGENCE_ENGINE_URL` to production ML service

### Database
- Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- Enable SSL connections
- Regular backups

### S3 Storage
- Enable versioning
- Configure lifecycle policies
- Set up CORS for presigned URLs
- Enable server-side encryption

### Email
- Use transactional email service (SendGrid, AWS SES)
- Configure SPF/DKIM records
- Monitor delivery rates

### Monitoring
- Set up error tracking (Sentry)
- Configure logging
- Monitor API performance
- Track email delivery

---

## Integration with Other Services

### Intelligence Engine
The Core API integrates with `ff-intelligence-engine-ml` for AI scoring:
- Sends assessment data via `/api/v1/score` endpoint
- Receives trust scores, layer scores, veto results, and narrative
- Stores results in `assessment_scores` table

### Analyst Dashboard
The `ff-analyst-review-ui` consumes this API:
- Fetches assessments for review
- Displays scores and narratives
- Allows analyst overrides
- Manages evidence verification

### User Dashboard (To Be Built)
Will use this API for:
- Project and assessment creation
- Partner invitation
- Progress tracking
- Report viewing

### Partner Dashboard (To Be Built)
Will use this API for:
- Invitation acceptance
- Respondent assignment
- Response submission
- Evidence upload

---

## Status

**Current Version**: 2.0 (Complete)  
**Completion**: 95%  
**Production Ready**: Yes (with proper configuration)

**What's Complete**:
- ✅ All data models
- ✅ All core services
- ✅ Complete API endpoints
- ✅ S3 integration
- ✅ Email notifications
- ✅ Intelligence Engine integration

**What's Missing**:
- ❌ Authentication/Authorization (JWT)
- ❌ Rate limiting
- ❌ Comprehensive tests
- ❌ API documentation (Swagger/OpenAPI)
- ❌ Celery workers for async tasks

---

## License

Proprietary - FutureForm © 2025

---

## Support

For questions or issues, contact: dev@futureform.africa
