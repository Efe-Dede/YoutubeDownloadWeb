"""Video API routes."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    DownloadRequest,
    DownloadResponse,
    ProgressResponse,
    DownloadStatus
)
from app.services.downloader import downloader_service

router = APIRouter(prefix="/api", tags=["video"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_video(request: AnalyzeRequest):
    """Analyze a video URL and return metadata."""
    result = downloader_service.analyze_video(request.url)
    return AnalyzeResponse(**result)


@router.post("/download", response_model=DownloadResponse)
async def start_download(request: DownloadRequest):
    """Start a video download job."""
    try:
        job_id = downloader_service.start_download(
            url=request.url,
            quality=request.quality or "best",
            format_id=request.format_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
        return DownloadResponse(success=True, job_id=job_id)
    except Exception as e:
        return DownloadResponse(success=False, error=str(e))


@router.get("/progress/{job_id}", response_model=ProgressResponse)
async def get_progress(job_id: str):
    """Get the progress of a download job."""
    job = downloader_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ProgressResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        speed=job.speed,
        eta=job.eta,
        filename=job.filename,
        error=job.error
    )


@router.get("/file/{job_id}")
async def get_file(job_id: str):
    """Download the completed file."""
    filepath = downloader_service.get_file_path(job_id)
    
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = os.path.basename(filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )
