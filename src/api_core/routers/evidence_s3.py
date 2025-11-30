from fastapi import APIRouter

router = APIRouter()

@router.post("/evidence/upload-url")
async def get_upload_url():
    return {"message": "Get S3 upload URL"}
