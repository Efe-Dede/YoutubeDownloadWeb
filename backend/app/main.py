"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.video import router as video_router
from app.models import HealthResponse

settings = get_settings()

app = FastAPI(
    title="Video Downloader API",
    description="API for downloading videos from YouTube, TikTok, Instagram",
    version="1.0.0"
)

# CORS middleware
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(video_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Video Downloader API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
