"""
Webhook endpoints for worker communication.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from fastapi import Depends

from app.api.deps import get_db, verify_worker
from app.schemas.job import JobStatusUpdate, BillingHeartbeat, BillingHeartbeatResponse
from app.services.job_service import JobService
from app.services.billing import BillingService


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/job-status")
def update_job_status(
    payload: JobStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Webhook for worker to update job status.
    Called when job transitions between states.
    """
    # Verify worker authentication
    verify_worker(payload.worker_secret)
    
    job_service = JobService(db)
    job = job_service.update_status(
        job_id=payload.job_id,
        status=payload.status,
        container_id=payload.container_id,
        error_message=payload.error_message,
        runtime_seconds=payload.runtime_seconds
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"status": "updated", "job_id": str(job.id)}


@router.post("/billing-heartbeat", response_model=BillingHeartbeatResponse)
def billing_heartbeat(
    payload: BillingHeartbeat,
    db: Session = Depends(get_db)
):
    """
    Webhook for worker billing heartbeat.
    
    Called every minute during job execution.
    Returns should_continue=False to trigger kill switch.
    """
    # Verify worker authentication
    verify_worker(payload.worker_secret)
    
    billing = BillingService(db)
    should_continue, balance = billing.check_and_bill(
        job_id=payload.job_id,
        runtime_minutes=payload.runtime_minutes
    )
    
    message = None
    if not should_continue:
        message = "Insufficient credits - kill switch activated"
    
    return BillingHeartbeatResponse(
        should_continue=should_continue,
        current_balance=balance,
        message=message
    )


@router.get("/download-files/{job_id}")
def download_job_files(
    job_id: str,
    worker_secret: str,
    db: Session = Depends(get_db)
):
    """
    Webhook for worker to download job input files.
    
    Returns the files as a zip archive containing all input files.
    Worker should extract this to its local input directory before execution.
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    import zipfile
    import tempfile
    from app.config import settings
    
    # Verify worker authentication
    verify_worker(worker_secret)
    
    # Get job info
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Build path to job input directory
    input_path = Path(settings.NFS_MOUNT_PATH) / "jobs" / job_id / "input"
    
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Job input files not found")
    
    # Create a temporary zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in input_path.iterdir():
            if file_path.is_file():
                zf.write(file_path, file_path.name)
    
    return FileResponse(
        temp_zip.name,
        media_type="application/zip",
        filename=f"job-{job_id}-input.zip"
    )


@router.post("/upload-logs/{job_id}")
def upload_job_logs(
    job_id: str,
    worker_secret: str,
    logs: str,
    db: Session = Depends(get_db)
):
    """
    Webhook for worker to upload job logs after execution.
    
    This allows the frontend to display logs even though
    the job ran on a remote worker (DGX).
    """
    from pathlib import Path
    from app.config import settings
    
    # Verify worker authentication
    verify_worker(worker_secret)
    
    # Get job info
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Save logs to storage
    logs_path = Path(settings.NFS_MOUNT_PATH) / "jobs" / job_id / "logs"
    logs_path.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_path / "output.log"
    with open(log_file, "w") as f:
        f.write(logs)
    
    return {"status": "uploaded", "job_id": job_id}


@router.post("/upload-results/{job_id}")
async def upload_job_results(
    job_id: str,
    worker_secret: str,
    results_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Webhook for worker to upload job results after execution.
    
    Receives a zip file containing output files from the worker.
    """
    from fastapi import UploadFile, File
    from pathlib import Path
    from app.config import settings
    import shutil
    
    # Verify worker authentication
    verify_worker(worker_secret)
    
    # Get job info
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Save results zip to storage
    output_path = Path(settings.NFS_MOUNT_PATH) / "jobs" / job_id / "output"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save the uploaded zip file
    zip_file_path = output_path / "results.zip"
    with open(zip_file_path, "wb") as f:
        shutil.copyfileobj(results_file.file, f)
    
    return {"status": "uploaded", "job_id": job_id}



