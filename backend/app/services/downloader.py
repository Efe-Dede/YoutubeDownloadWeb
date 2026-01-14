"""Video downloader service using yt-dlp."""

import os
import uuid
import threading
import subprocess
from typing import Dict, Optional, Callable
from datetime import datetime
import yt_dlp
import time
from urllib.parse import urlparse

from app.config import get_settings
from app.models import DownloadStatus, VideoFormat


class DownloadJob:
    """Represents a download job with progress tracking."""
    
    def __init__(self, job_id: str, url: str):
        self.job_id = job_id
        self.url = url
        self.status = DownloadStatus.PENDING
        self.progress = 0.0
        self.speed: Optional[str] = None
        self.eta: Optional[str] = None
        self.filename: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.filepath: Optional[str] = None


class DownloaderService:
    """Service for downloading videos using yt-dlp."""
    
    def __init__(self):
        self.settings = get_settings()
        self.jobs: Dict[str, DownloadJob] = {}
        self.allowed_domains = [
            'youtube.com', 'youtu.be', 'www.youtube.com',
            'instagram.com', 'www.instagram.com',
            'tiktok.com', 'www.tiktok.com', 'vm.tiktok.com'
        ]
        self._ensure_download_dir()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start a background thread for periodic cleanup."""
        def run_cleanup():
            while True:
                try:
                    self.cleanup_old_files()
                except Exception as e:
                    print(f"Cleanup error: {e}")
                # Sleep for 1 minute
                time.sleep(60)
        
        thread = threading.Thread(target=run_cleanup, daemon=True)
        thread.start()

    def is_url_allowed(self, url: str) -> bool:
        """Check if the URL is in the allowed domains list."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if not domain:
                return False
            return any(domain == d or domain.endswith('.' + d) for d in self.allowed_domains)
        except:
            return False
    
    def _ensure_download_dir(self):
        """Ensure download directory exists."""
        os.makedirs(self.settings.download_dir, exist_ok=True)
    
    def analyze_video(self, url: str) -> dict:
        """Analyze video and return metadata."""
        
        # Detect if it's a URL or search query
        is_url = url.startswith(('http://', 'https://', 'www.'))
        search_query = url if is_url else f"ytsearch:{url}"

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'default_search': 'ytsearch',
            'restrictfilenames': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                # Handle search/playlist/entries case
                if 'entries' in info:
                    # Get first entry if it's a search result or playlist
                    entries = info['entries']
                    if isinstance(entries, list) and len(entries) > 0:
                        info = entries[0]
                    elif hasattr(entries, '__iter__'):
                        # Generator case
                        try:
                            info = next(iter(entries))
                        except StopIteration:
                            pass
                
                # Ensure info is a dict
                if not isinstance(info, dict):
                    return {
                        'success': False,
                        'error': 'Video bilgisi alınamadı'
                    }
                
                formats = []
                raw_formats = info.get('formats')
                
                # Handle case where formats might be a list
                if raw_formats and isinstance(raw_formats, list):
                    seen_resolutions = set()
                    for f in raw_formats:
                        # Skip if f is not a dict
                        if not isinstance(f, dict):
                            continue
                            
                        resolution = f.get('resolution') or f.get('format_note')
                        height = f.get('height')
                        
                        # Ensure height is an integer
                        if height is not None:
                            try:
                                height = int(height)
                            except (ValueError, TypeError):
                                height = None
                        
                        # Filter for useful formats
                        if height and height >= 360:
                            quality_label = f"{height}p"
                            if quality_label not in seen_resolutions:
                                seen_resolutions.add(quality_label)
                                formats.append(VideoFormat(
                                    format_id=str(f.get('format_id', '')),
                                    ext=str(f.get('ext', 'mp4')),
                                    resolution=str(resolution) if resolution else None,
                                    filesize=f.get('filesize'),
                                    vcodec=str(f.get('vcodec', '')) if f.get('vcodec') else None,
                                    acodec=str(f.get('acodec', '')) if f.get('acodec') else None,
                                    quality_label=quality_label
                                ))
                
                # Add audio-only option
                formats.append(VideoFormat(
                    format_id='bestaudio',
                    ext='mp3',
                    resolution='audio only',
                    quality_label='MP3 Audio'
                ))
                
                # Sort by resolution (highest first)
                def get_resolution_value(x):
                    if not x.quality_label:
                        return 0
                    label = x.quality_label.replace('p', '').replace('MP3 Audio', '0')
                    try:
                        return int(label)
                    except ValueError:
                        return 0
                
                formats.sort(key=get_resolution_value, reverse=True)
                
                duration = info.get('duration', 0)
                if duration:
                    try:
                        duration = int(duration)
                    except (ValueError, TypeError):
                        duration = 0
                        
                duration_string = self._format_duration(duration) if duration else None
                
                return {
                    'success': True,
                    'title': info.get('title'),
                    'thumbnail': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url'),
                    'duration': duration,
                    'duration_string': duration_string,
                    'uploader': info.get('uploader'),
                    'formats': formats
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    def start_download(
        self,
        url: str,
        quality: str = "best",
        format_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> str:
        """Start a download job and return job_id."""
        job_id = str(uuid.uuid4())[:8]
        job = DownloadJob(job_id, url)
        self.jobs[job_id] = job
        
        # Start download in background thread
        thread = threading.Thread(
            target=self._download_worker,
            args=(job, quality, format_id, start_time, end_time)
        )
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _download_worker(
        self,
        job: DownloadJob,
        quality: str,
        format_id: Optional[str],
        start_time: Optional[int],
        end_time: Optional[int]
    ):
        """Background worker for downloading videos."""
        job.status = DownloadStatus.DOWNLOADING
        
        # Build format string based on quality
        # Use formats that include both video and audio, or merge them
        if format_id and format_id != 'bestaudio':
            format_str = f"{format_id}+bestaudio/best"
        elif quality == "audio":
            format_str = "bestaudio[ext=m4a]/bestaudio/best"
        elif quality == "1080p":
            format_str = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        elif quality == "720p":
            format_str = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        elif quality == "480p":
            format_str = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best"
        elif quality == "360p":
            format_str = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]/best"
        else:
            # Best quality with guaranteed audio
            format_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        
        output_template = os.path.join(
            self.settings.download_dir,
            f"{job.job_id}_%(title)s.%(ext)s"
        )
        
        # Build download sections for segment cutting
        download_ranges = None
        if start_time is not None or end_time is not None:
            start = start_time or 0
            end = end_time or float('inf')
            download_ranges = lambda info, ydl: [[start, end]]
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                job.progress = d.get('_percent_str', '0%').replace('%', '')
                try:
                    job.progress = float(job.progress)
                except:
                    job.progress = 0.0
                job.speed = d.get('_speed_str', '')
                job.eta = d.get('_eta_str', '')
                job.filename = d.get('filename', '')
            elif d['status'] == 'finished':
                job.progress = 100.0
                job.filepath = d.get('filename', '')
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': output_template,
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4' if quality != "audio" else 'mp3',
            'restrictfilenames': True,
        }
        
        # Add audio extraction for audio-only
        if quality == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Add download ranges if specified
        if download_ranges:
            ydl_opts['download_ranges'] = download_ranges
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([job.url])
            
            # Find the downloaded file
            for filename in os.listdir(self.settings.download_dir):
                if filename.startswith(job.job_id):
                    job.filepath = os.path.join(self.settings.download_dir, filename)
                    job.filename = filename
                    break
            
            job.status = DownloadStatus.COMPLETED
            job.progress = 100.0
            
        except Exception as e:
            job.status = DownloadStatus.FAILED
            job.error = str(e)
    
    def get_job(self, job_id: str) -> Optional[DownloadJob]:
        """Get a download job by ID."""
        return self.jobs.get(job_id)
    
    def get_file_path(self, job_id: str) -> Optional[str]:
        """Get the file path for a completed download."""
        job = self.jobs.get(job_id)
        if job and job.status == DownloadStatus.COMPLETED and job.filepath:
            return job.filepath
        return None


    def cleanup_old_files(self):
        """Delete files older than the specified minutes in config."""
        now = time.time()
        cleanup_threshold_seconds = self.settings.cleanup_after_minutes * 60
        
        if not os.path.exists(self.settings.download_dir):
            return

        for filename in os.listdir(self.settings.download_dir):
            file_path = os.path.join(self.settings.download_dir, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Check file age
            file_age = now - os.path.getmtime(file_path)
            if file_age > cleanup_threshold_seconds:
                try:
                    os.remove(file_path)
                    print(f"Cleaned up old file: {filename}")
                except Exception as e:
                    print(f"Failed to delete {filename}: {e}")

# Global service instance
downloader_service = DownloaderService()
