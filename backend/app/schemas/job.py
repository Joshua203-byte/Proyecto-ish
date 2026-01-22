"""Job Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Dict, Any
from pydantic import BaseModel, Field


class ResourceConfig(BaseModel):
    """Resource configuration for a job."""
    memory_limit: str = Field(default="8g", pattern=r"^\d+[gm]$")
    cpu_count: int = Field(default=4, ge=1, le=16)
    timeout_seconds: int = Field(default=3600, ge=60, le=14400)


class JobCreate(BaseModel):
    """Schema for job submission."""
    script_name: str = Field(default="train.py", max_length=255)
    docker_image: str = Field(
        default="nvidia/cuda:12.1-runtime-ubuntu22.04",
        max_length=255
    )
    resource_config: ResourceConfig = Field(default_factory=ResourceConfig)


class JobRead(BaseModel):
    """Schema for job response."""
    id: UUID
    user_id: UUID
    status: str
    script_path: str
    dataset_path: str | None
    output_path: str | None
    logs_path: str | None
    container_id: str | None
    docker_image: str
    resource_config: Dict[str, Any]
    created_at: datetime
    queued_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    runtime_seconds: int
    total_cost: Decimal
    error_message: str | None
    exit_code: int | None
    
    class Config:
        from_attributes = True


class JobStatusUpdate(BaseModel):
    """Schema for worker status updates (webhook)."""
    job_id: UUID
    status: str
    container_id: str | None = None
    error_message: str | None = None
    runtime_seconds: int | None = None
    worker_secret: str


class BillingHeartbeat(BaseModel):
    """Schema for worker billing heartbeat."""
    job_id: UUID
    runtime_minutes: int
    worker_secret: str


class BillingHeartbeatResponse(BaseModel):
    """Response for billing heartbeat."""
    should_continue: bool
    current_balance: Decimal
    message: str | None = None
