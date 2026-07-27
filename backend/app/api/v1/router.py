"""API v1 Main Router."""

from fastapi import APIRouter
from app.api.v1.upload import router as upload_router
from app.api.v1.simplify import router as simplify_router

api_router = APIRouter()
api_router.include_router(upload_router)
api_router.include_router(simplify_router)



@api_router.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "healthy", "service": "PDF Summarizer API"}

