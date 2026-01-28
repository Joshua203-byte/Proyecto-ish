"""
Worker configuration settings.
"""
from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Worker configuration loaded from environment."""
    
    # Celery / Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Backend API
    BACKEND_URL: str = "http://localhost:8000"
    WORKER_SECRET: str = "secret123"
    
    # NFS Mount Point
    NFS_MOUNT_PATH: str = "C:/mnt/home-gpu-cloud"
    HOST_DATA_PATH: str = "C:/mnt/home-gpu-cloud"  # Path on the Host OS (Windows)
    
    # Resource Defaults
    DEFAULT_MEMORY_LIMIT: str = "8g"
    DEFAULT_CPU_COUNT: int = 4
    DEFAULT_TIMEOUT_SECONDS: int = 3600
    MAX_TIMEOUT_SECONDS: int = 14400
    
    # Docker
    GPU_IMAGE: str = "python:3.11-slim"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = WorkerSettings()
