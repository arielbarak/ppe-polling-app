from fastapi import APIRouter
from app.models.base import ApiResponse

router = APIRouter()

@router.get("/healthcheck", response_model=ApiResponse)
async def healthcheck():
    """Check if the API is healthy"""
    return {"status": "healthy"}

@router.get("/version", response_model=ApiResponse)
async def get_version():
    """Get the API version information"""
    return {
        "version": "1.0.0",  # Application version
        "api_version": "v1"   # API version
    }