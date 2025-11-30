from pydantic import BaseModel

class AssessmentMetadata(BaseModel):
    assessment_id: str
    status: str
    respondent_count: int
