"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum


class VideoFormat(BaseModel):
    """Video format information."""
    format_id: str
    ext: str
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    quality_label: Optional[str] = None


class AnalyzeRequest(BaseModel):
    """Request model for video analysis."""
    url: str


class AnalyzeResponse(BaseModel):
    """Response model for video analysis."""
    success: bool
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    webpage_url: Optional[str] = None
    duration: Optional[int] = None  # seconds
    duration_string: Optional[str] = None
    uploader: Optional[str] = None
    formats: List[VideoFormat] = []
    error: Optional[str] = None


class DownloadRequest(BaseModel):
    """Request model for starting a download."""
    url: str
    format_id: Optional[str] = None
    quality: Optional[str] = "best"  # best, 1080p, 720p, 480p, 360p, audio
    start_time: Optional[int] = None  # seconds
    end_time: Optional[int] = None  # seconds


class DownloadStatus(str, Enum):
    """Download job status."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadResponse(BaseModel):
    """Response model for download initiation."""
    success: bool
    job_id: Optional[str] = None
    error: Optional[str] = None


class ProgressResponse(BaseModel):
    """Response model for download progress."""
    job_id: str
    status: DownloadStatus
    progress: float = 0.0  # 0-100
    speed: Optional[str] = None
    eta: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str = "1.0.0"
