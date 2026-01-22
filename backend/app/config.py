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
    NFS_MOUNT_PATH: str = "C:/Users/HOME/OneDrive/Desktop/Machine learning de ISH/home-gpu-cloud/data"
    MAX_UPLOAD_SIZE_MB: int = 500

    # Payment (Wompi)
    WOMPI_SV_APP_ID: str = ""
    WOMPI_SV_API_SECRET: str = ""
    WOMPI_PUB_KEY: str = "pub_test_Q5yDA9Nsa6vdsdf" # Default dev key (Fixed typo)
    
    # Frontend public URL
    FRONTEND_URL: str = "http://localhost:8000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # ═══════════════════════════════════════════════════════════════════
    # BILLING (DGX Spark Pricing Strategy)
    # ═══════════════════════════════════════════════════════════════════
    # Base Rate: $0.50 USD per GPU hour
    PRICE_PER_HOUR: float = 0.50
    PRICE_PER_MINUTE: float = 0.50 / 60  # $0.008333...
    PRICE_PER_SECOND: float = 0.50 / 3600  # $0.000138...
    
    # Minimum balance required to start a job (1 hour minimum)
    MINIMUM_BALANCE_TO_START: float = 0.50
    
    # Legacy compatibility
    CREDITS_PER_MINUTE: float = 0.50 / 60
    
    # Resource Defaults (Local Development Defaults)
    DEFAULT_GPU_IMAGE: str = "python:3.11-slim"
    DEFAULT_MEMORY_LIMIT: str = "4g"
    DEFAULT_CPU_COUNT: int = 2
    DEFAULT_TIMEOUT_SECONDS: int = 3600
    MAX_TIMEOUT_SECONDS: int = 14400
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# ═══════════════════════════════════════════════════════════════════════════
# CREDIT PACKS (Products for Stripe/Frontend)
# ═══════════════════════════════════════════════════════════════════════════
CREDIT_PACKS = [
    {
        "id": "pack_pilot",
        "name": "Pilot",
        "price_usd": 5.00,
        "hours": 10,
        "credits": 5.00,
        "description": "Perfect for testing and small experiments",
        "popular": False,
        "features": [
            "Standard Priority",
            "1 GPU Instance",
            "16GB VRAM",
            "Basic Support"
        ]
    },
    {
        "id": "pack_researcher",
        "name": "Researcher",
        "price_usd": 20.00,
        "hours": 45,
        "credits": 22.50,
        "description": "Best value for regular training runs",
        "popular": True,
        "bonus_hours": 5,
        "features": [
            "High Priority Queue",
            "Up to 2 Concurrent Jobs",
            "32GB VRAM",
            "5 Bonus Hours Included"
        ]
    },
    {
        "id": "pack_lab",
        "name": "Lab",
        "price_usd": 50.00,
        "hours": 120,
        "credits": 60.00,
        "description": "Everything in Researcher + Priority Queue",
        "popular": False,
        "bonus_hours": 20,
        "features": [
            "Highest Priority",
            "Multiple GPUs",
            "128GB Unified Memory",
            "20 Bonus Hours Included",
            "Real-time Logs",
            "API Access",
            "Priority Queue",
            "Dedicated Support"
        ]
    },
]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
