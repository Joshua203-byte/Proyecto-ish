"""
Worker configuration settings.
"""
from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Worker configuration loaded from environment."""
    
    # Celery / Redis
    REDIS_URL: str = "redis://controller.local:6379/0"
    
    # Backend API
    BACKEND_URL: str = "http://controller.local:8000"
    WORKER_SECRET: str = "change-this-worker-secret-in-production"
    
    # NFS Mount Point
    NFS_MOUNT_PATH: str = "/mnt/home-gpu-cloud"
    
    # Resource Defaults
    DEFAULT_MEMORY_LIMIT: str = "8g"
    DEFAULT_CPU_COUNT: int = 4
    DEFAULT_TIMEOUT_SECONDS: int = 3600
    MAX_TIMEOUT_SECONDS: int = 14400
    
    # Docker
    GPU_IMAGE: str = "nvidia/cuda:12.1-runtime-ubuntu22.04"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = WorkerSettings()
