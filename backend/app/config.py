"""Application configuration using environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server settings
    port: int = 8000
    host: str = "0.0.0.0"
    
    # CORS settings
    allowed_origins: str = "*"
    
    # Download settings
    download_dir: str = "/app/downloads"
    max_download_size_mb: int = 500
    cleanup_after_hours: int = 24
    
    # yt-dlp settings
    default_format: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    
    class Config:
        env_prefix = ""
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
