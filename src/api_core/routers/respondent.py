from fastapi import APIRouter

router = APIRouter()

@router.post("/respondents/register")
async def register_respondent():
    return {"message": "Register respondent"}

@router.get("/respondents/{respondent_id}/questions")
async def get_questions(respondent_id: str):
    return {"message": "Get questions"}
