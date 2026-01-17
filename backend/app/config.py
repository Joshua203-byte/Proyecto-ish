"""
Home-GPU-Cloud Backend Application Configuration.
"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Home-GPU-Cloud"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://homegpu:changeme@localhost:5432/homegpu"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "change-this-to-a-secure-random-string-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    WORKER_SECRET: str = "change-this-worker-secret-in-production"
    
    # Storage
    NFS_MOUNT_PATH: str = "/mnt/home-gpu-cloud"
    MAX_UPLOAD_SIZE_MB: int = 500
    
    # Billing
    CREDITS_PER_MINUTE: float = 1.0
    MINIMUM_BALANCE_TO_START: float = 10.0
    
    # Resource Defaults
    DEFAULT_MEMORY_LIMIT: str = "8g"
    DEFAULT_CPU_COUNT: int = 4
    DEFAULT_TIMEOUT_SECONDS: int = 3600
    MAX_TIMEOUT_SECONDS: int = 14400
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
