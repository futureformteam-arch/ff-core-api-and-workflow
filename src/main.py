from fastapi import FastAPI
from src.core.config import settings
from src.workflow.router import router as workflow_router
from src.portals.customer.router import router as customer_router
from src.portals.respondent.router import router as respondent_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include routers
app.include_router(workflow_router, prefix=f"{settings.API_V1_STR}/workflow", tags=["workflow"])
app.include_router(customer_router, prefix=f"{settings.API_V1_STR}/customer", tags=["customer-portal"])
app.include_router(respondent_router, prefix=f"{settings.API_V1_STR}/respondent", tags=["respondent-portal"])

@app.get("/")
def root():
    return {"message": "Welcome to FutureForm Core API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
