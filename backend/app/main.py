import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.services.cleanup_service import periodic_cleanup_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch periodic background cleanup for 24h expired artifacts
    cleanup_task = asyncio.create_task(periodic_cleanup_task(interval_seconds=3600))
    yield
    # Shutdown: Cancel background cleanup task
    cleanup_task.cancel()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint welcoming users."""
    return {
        "message": "Welcome to PDF Summarizer API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
