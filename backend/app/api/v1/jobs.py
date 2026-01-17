"""
Jobs API endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from celery import Celery

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobRead
from app.services.job_service import JobService
from app.services.billing import BillingService
from app.services.storage import StorageService
from app.config import settings


router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Celery app for task submission
celery_app = Celery(
    "home-gpu-cloud",
    broker=settings.REDIS_URL,
)


@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    script_file: UploadFile = File(...),
    dataset_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new GPU job.
    
    Upload your training script (required) and dataset (optional).
    Job will be queued for execution on the GPU worker.
    """
    billing = BillingService(db)
    
    # Check minimum balance
    if not billing.can_start_job(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Minimum {settings.MINIMUM_BALANCE_TO_START} credits required."
        )
    
    # Create job
    job_service = JobService(db)
    job = job_service.create_job(
        user_id=current_user.id,
        script_name=job_data.script_name,
        docker_image=job_data.docker_image,
        resource_config=job_data.resource_config.model_dump()
    )
    
    # Save files to NFS
    storage = StorageService()
    
    # Save script
    script_content = await script_file.read()
    await storage.save_script(job.id, job_data.script_name, script_content)
    
    # Save dataset if provided
    if dataset_file:
        await storage.save_dataset(job.id, dataset_file.file, dataset_file.filename)
        job.dataset_path = f"jobs/{job.id}/input/data"
        db.commit()
    
    # Queue job for worker
    job = job_service.queue_job(job.id)
    
    # Send task to Celery queue
    celery_app.send_task(
        "worker.tasks.gpu_tasks.execute_gpu_job",
        kwargs={
            "job_id": str(job.id),
            "user_id": str(current_user.id),
            "script_name": job_data.script_name,
            "image": job_data.docker_image,
            "memory_limit": job_data.resource_config.memory_limit,
            "cpu_count": job_data.resource_config.cpu_count,
            "timeout_seconds": job_data.resource_config.timeout_seconds,
        },
        queue="gpu_jobs"
    )
    
    return job


@router.get("/", response_model=list[JobRead])
def list_jobs(
    status_filter: str = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's jobs with optional status filter."""
    job_service = JobService(db)
    return job_service.get_user_jobs(
        user_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset
    )


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job details by ID."""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return job


@router.post("/{job_id}/cancel", response_model=JobRead)
def cancel_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a running or pending job."""
    job_service = JobService(db)
    
    try:
        job = job_service.cancel_job(job_id, current_user.id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/logs")
def get_job_logs(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job execution logs."""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    storage = StorageService()
    logs = storage.get_logs(job_id)
    
    return {"logs": logs}


@router.get("/{job_id}/outputs")
def list_job_outputs(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List output files for a completed job."""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    storage = StorageService()
    files = storage.get_output_files(job_id)
    
    return {"files": files}
