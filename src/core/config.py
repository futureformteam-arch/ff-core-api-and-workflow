from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "FutureForm Core API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5435/futureforms"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "futureform-evidence"
    
    # Email (SMTP)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@futureform.africa"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Intelligence Engine
    INTELLIGENCE_ENGINE_URL: str = "http://localhost:8000"

def get_settings():
    return Settings()

settings = get_settings()
