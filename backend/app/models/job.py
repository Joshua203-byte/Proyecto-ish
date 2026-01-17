"""
Job model for tracking GPU compute jobs.
"""
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class JobStatus:
    """Job status constants."""
    PENDING = "pending"                     # Waiting in queue
    PREPARING = "preparing"                 # Downloading/preparing container
    RUNNING = "running"                     # Executing on GPU
    COMPLETED = "completed"                 # Finished successfully
    FAILED = "failed"                       # Error during execution
    CANCELLED = "cancelled"                 # Cancelled by user
    KILLED_NO_CREDITS = "killed_no_credits" # Kill switch activated


class Job(Base):
    """GPU compute job model."""
    
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Status
    status = Column(String(50), default=JobStatus.PENDING, nullable=False, index=True)
    
    # Paths relative to NFS mount point
    script_path = Column(String(500), nullable=False)   # jobs/{id}/input/train.py
    dataset_path = Column(String(500), nullable=True)   # jobs/{id}/input/data/
    output_path = Column(String(500), nullable=True)    # jobs/{id}/output/
    logs_path = Column(String(500), nullable=True)      # jobs/{id}/logs/
    
    # Docker container tracking
    container_id = Column(String(64), nullable=True)
    docker_image = Column(String(255), default="nvidia/cuda:12.1-runtime-ubuntu22.04")
    
    # Resource configuration (container limits)
    resource_config = Column(JSONB, default=lambda: {
        "memory_limit": "8g",
        "cpu_count": 4,
        "gpu_memory_fraction": 1.0,
        "timeout_seconds": 3600,
        "disk_quota_gb": 50
    })
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    queued_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Billing metrics
    runtime_seconds = Column(Integer, default=0)
    total_cost = Column(Numeric(precision=10, scale=2), default=Decimal("0.00"))
    
    # Error handling
    error_message = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    transactions = relationship("Transaction", back_populates="job")
    
    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state (no more changes expected)."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.KILLED_NO_CREDITS,
        )
    
    @property
    def is_billable(self) -> bool:
        """Check if job is currently consuming billable resources."""
        return self.status in (JobStatus.PREPARING, JobStatus.RUNNING)
    
    def __repr__(self) -> str:
        return f"<Job {self.id} status={self.status}>"
