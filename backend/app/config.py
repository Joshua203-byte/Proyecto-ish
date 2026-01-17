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
    
    # Billing (DGX Spark pricing: $0.50 USD/hour = $0.00833/minute)
    CREDITS_PER_MINUTE: float = 0.00833  # $0.50/hour in credits per minute
    MINIMUM_BALANCE_TO_START: float = 1.0  # Minimum $1.00 to start
    
    # Resource Defaults (DGX Spark: 128GB unified memory)
    # Recommend max 120GB to leave headroom for system
    DEFAULT_MEMORY_LIMIT: str = "120g"
    DEFAULT_CPU_COUNT: int = 12  # Grace CPU has many ARM cores
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
