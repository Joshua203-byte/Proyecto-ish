"""
Job service for job management.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus
from app.models.user import User
from app.config import settings


class JobService:
    """Service for job lifecycle management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.nfs_path = Path(settings.NFS_MOUNT_PATH)
    
    def create_job(
        self,
        user_id: UUID,
        script_name: str = "train.py",
        docker_image: str = "nvidia/cuda:12.1-runtime-ubuntu22.04",
        resource_config: dict = None
    ) -> Job:
        """
        Create a new job and prepare NFS directories.
        """
        job = Job(
            user_id=user_id,
            script_path="",  # Will be set after upload
            docker_image=docker_image,
            resource_config=resource_config or {}
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Create NFS directories
        job_dir = self.nfs_path / "jobs" / str(job.id)
        input_dir = job_dir / "input"
        output_dir = job_dir / "output"
        logs_dir = job_dir / "logs"
        
        for d in [input_dir, output_dir, logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Update paths
        job.script_path = f"jobs/{job.id}/input/{script_name}"
        job.output_path = f"jobs/{job.id}/output"
        job.logs_path = f"jobs/{job.id}/logs"
        
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID."""
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def get_user_jobs(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Job]:
        """Get jobs for a user with optional status filter."""
        query = self.db.query(Job).filter(Job.user_id == user_id)
        
        if status:
            query = query.filter(Job.status == status)
        
        return query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
    
    def update_status(
        self,
        job_id: UUID,
        status: str,
        container_id: str = None,
        error_message: str = None,
        runtime_seconds: int = None,
        exit_code: int = None
    ) -> Optional[Job]:
        """Update job status (called by worker webhook)."""
        job = self.get_job(job_id)
        if not job:
            return None
        
        job.status = status
        
        if container_id:
            job.container_id = container_id
        
        if error_message:
            job.error_message = error_message
        
        if runtime_seconds is not None:
            job.runtime_seconds = runtime_seconds
        
        if exit_code is not None:
            job.exit_code = exit_code
        
        # Set timestamps based on status
        now = datetime.utcnow()
        
        if status == JobStatus.PENDING:
            job.queued_at = now
        elif status == JobStatus.RUNNING:
            if not job.started_at:
                job.started_at = now
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, 
                        JobStatus.CANCELLED, JobStatus.KILLED_NO_CREDITS):
            job.completed_at = now
        
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def queue_job(self, job_id: UUID) -> Optional[Job]:
        """Mark job as queued and ready for worker."""
        return self.update_status(job_id, JobStatus.PENDING)
    
    def cancel_job(self, job_id: UUID, user_id: UUID) -> Optional[Job]:
        """
        Cancel a job (user-initiated).
        Only works if job is not yet completed.
        """
        job = self.get_job(job_id)
        if not job:
            return None
        
        if job.user_id != user_id:
            raise PermissionError("Cannot cancel another user's job")
        
        if job.is_terminal:
            raise ValueError("Cannot cancel a completed job")
        
        return self.update_status(job_id, JobStatus.CANCELLED)
    
    def cleanup_job_files(self, job_id: UUID) -> bool:
        """Delete job files from NFS (admin only)."""
        job_dir = self.nfs_path / "jobs" / str(job_id)
        
        if job_dir.exists():
            shutil.rmtree(job_dir)
            return True
        
        return False
    
    def get_job_input_path(self, job_id: UUID) -> Path:
        """Get absolute path to job input directory."""
        return self.nfs_path / "jobs" / str(job_id) / "input"
    
    def get_job_output_path(self, job_id: UUID) -> Path:
        """Get absolute path to job output directory."""
        return self.nfs_path / "jobs" / str(job_id) / "output"
    
    def get_job_logs_path(self, job_id: UUID) -> Path:
        """Get absolute path to job logs directory."""
        return self.nfs_path / "jobs" / str(job_id) / "logs"
