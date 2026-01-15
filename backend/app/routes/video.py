"""Video API routes."""

from fastapi import APIRouter, HTTPException, Depends, Header
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
from app.config import get_settings
from app.limiter import limiter
from fastapi import Request

settings = get_settings()

router = APIRouter(prefix="/api", tags=["video"])

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify the API key from request headers."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key


@router.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def analyze_video(request: Request, body: AnalyzeRequest):
    """Analyze a video URL and return metadata."""
    if not downloader_service.is_url_allowed(body.url):
        raise HTTPException(status_code=400, detail="Bu platforma izin verilmiyor. Sadece YouTube, Instagram ve TikTok desteklenmektedir.")
    
    try:
        result = downloader_service.analyze_video(body.url)
        if not result.get('success'):
            print(f"Analysis Failed for {body.url}: {result.get('error')}")
        return AnalyzeResponse(**result)
    except Exception as e:
        print(f"Route Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download", response_model=DownloadResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def start_download(request: Request, body: DownloadRequest):
    """Start a video download job."""
    if not downloader_service.is_url_allowed(body.url):
        raise HTTPException(status_code=400, detail="Bu platforma izin verilmiyor. Sadece YouTube, Instagram ve TikTok desteklenmektedir.")
        
    try:
        job_id = downloader_service.start_download(
            url=body.url,
            quality=body.quality or "best",
            format_id=body.format_id,
            start_time=body.start_time,
            end_time=body.end_time
        )
        return DownloadResponse(success=True, job_id=job_id)
    except Exception as e:
        return DownloadResponse(success=False, error=str(e))


@router.get("/progress/{job_id}", response_model=ProgressResponse, dependencies=[Depends(verify_api_key)])
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


@router.get("/file/{job_id}", dependencies=[Depends(verify_api_key)])
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
