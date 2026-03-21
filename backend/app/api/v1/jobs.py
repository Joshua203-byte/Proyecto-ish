from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from celery import Celery
import asyncio
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.database import SessionLocal
from app.models.user import User
from app.models.job import Job, JobStatus
from app.schemas.job import JobRead
from app.services.job_service import JobService
from app.services.billing import BillingService
from app.services.storage import StorageService
from app.config import settings
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    background_tasks: BackgroundTasks,
    script_file: UploadFile = File(...),
    dataset_file: UploadFile = File(None),
    email: str = Form(None),
    memory: str = Form("8g"),
    timeout: int = Form(3600),
    launch_command: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new GPU job.
    """
    try:
        print(f"🚀 [JOBS] Starting job creation for user: {current_user.email}")
        
        # Update guest email if provided
        if email and current_user.email.startswith("guest-"):
            try:
                print(f"👤 [JOBS] Updating guest email to: {email}")
                current_user.email = email
                db.add(current_user)
                db.commit()
                db.refresh(current_user)
            except Exception as e:
                print(f"⚠️ [JOBS] Failed to update email (likely exists): {e}")
                db.rollback()
                # Continue execution even if email update fails
        
        # PAYMENT DISABLED - uncomment to re-enable billing checks
        # billing = BillingService(db)
        #
        # # Check minimum balance
        # print("🔍 [JOBS] Checking balance...")
        # if not billing.can_start_job(current_user.id):
        #     print("❌ [JOBS] Insufficient balance")
        #     raise HTTPException(
        #         status_code=status.HTTP_402_PAYMENT_REQUIRED,
        #         detail=f"Insufficient balance. Minimum {settings.MINIMUM_BALANCE_TO_START} credits required."
        #     )
        #
        # start_cost = Decimal(str(settings.CREDITS_PER_MINUTE)) * Decimal("5")
        # try:
        #      billing.debit_for_job(
        #         wallet_id=current_user.wallet.id,
        #         job_id=None,
        #         amount=start_cost,
        #         description=f"Job reservation (5 mins)"
        #     )
        # except Exception as e:
        #      raise HTTPException(status_code=402, detail=f"Payment failed: {str(e)}")
        
        # Create job
        print("📝 [JOBS] Creating DB record...")
        job_service = JobService(db)
        job = job_service.create_job(
            user_id=current_user.id,
            script_name=script_file.filename,
            docker_image=settings.DEFAULT_GPU_IMAGE, # Use unified setting
            resource_config={
                "memory_limit": memory,
                "cpu_count": settings.DEFAULT_CPU_COUNT,
                "timeout_seconds": timeout
            }
        )
        print(f"✅ [JOBS] Job created in DB with ID: {job.id}")
        
        # Save files to NFS
        print("💾 [JOBS] Saving files...")
        storage = StorageService()
        
        # Save script
        script_content = await script_file.read()
        await storage.save_script(job.id, script_file.filename, script_content)
        print("✅ [JOBS] Script saved")
        
        # Create log dir and dummy log for eager mode
        log_dir = storage.nfs_path / "jobs" / str(job.id) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "output.log"
        with open(log_file, "w") as f:
            f.write(f"--- Job {job.id} initialized ---\n")
            f.write(f"User: {current_user.email}\n")
            f.write(f"Script: {script_file.filename}\n")
            f.write(f"Mode: Real Infrastructure (Production Mode)\n")
            f.write(f"Status: Job Queued in Redis (gpu_jobs)\n")
            f.write(f"Note: Worker is preparing the Docker container...\n")
        
        # Make log file writable by everyone (so worker can overwrite it)
        try:
            import os
            os.chmod(log_file, 0o666)
        except Exception as e:
            print(f"⚠️ Failed to set log permissions: {e}")
        
        # Save dataset if provided
        if dataset_file:
            print("💾 [JOBS] Saving dataset...")
            await storage.save_dataset(job.id, dataset_file.file, dataset_file.filename)
            job.dataset_path = f"jobs/{job.id}/input/data"
            db.commit()
            print("✅ [JOBS] Dataset saved")
        
        # Queue job for worker
        print("🔄 [JOBS] Queuing job...")
        job = job_service.queue_job(job.id)
        
        # Start real worker job (Simulation disabled)
        # if background_tasks:
        #     print("⚡ [JOBS] Starting background simulation...")
        #     background_tasks.add_task(simulate_job_execution, job.id, script_file.filename)
        
        # Send task to Celery queue
        print("⚡ [JOBS] Sending to Celery (ASYNC MODE)...")
        try:
            celery_app.send_task(
                "worker.tasks.gpu_tasks.execute_gpu_job",
                kwargs={
                    "job_id": str(job.id),
                    "user_id": str(current_user.id),
                    "script_name": script_file.filename,
                    "image": job.docker_image,
                    "memory_limit": memory,
                    "cpu_count": settings.DEFAULT_CPU_COUNT,
                    "timeout_seconds": timeout,
                    "launch_args": launch_command,
                },
                queue="gpu_jobs"
            )
            print("✅ [JOBS] Celery task sent")
        except Exception as cel_err:
            print(f"⚠️ [JOBS] Celery error (ignored in eager mode): {cel_err}")
        
        return job

    except HTTPException:
        raise
    except FileNotFoundError as e:
        print(f"❌ [JOBS] Resource not found: {str(e)}")
        raise HTTPException(status_code=404, detail="Recurso del sistema no encontrado (NFS/Directorio).")
    except OSError as e:
        print(f"❌ [JOBS] Disk/IO Error: {str(e)}")
        raise HTTPException(status_code=503, detail="Error de disco o almacenamiento. ¿Está montado el NFS?")
    except Exception as e:
        print(f"🔥 [JOBS] CRITICAL ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado al crear el trabajo: {str(e)}"
        )


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


@router.get("/{job_id}/", response_model=JobRead)
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


@router.post("/{job_id}/cancel/", response_model=JobRead)
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


@router.delete("/{job_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job and its files."""
    job_service = JobService(db)
    
    try:
        success = job_service.delete_job(job_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        print(f"🔥 Error deleting job: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar el trabajo: {str(e)}")


@router.get("/{job_id}/download-input/")
def download_input_files(
    job_id: UUID,
    worker_secret: str = None,
    db: Session = Depends(get_db),
):
    """Download job input files (for worker use). Accepts worker_secret for auth."""
    from app.config import settings
    
    # Allow worker access via secret
    if worker_secret != settings.WORKER_SECRET:
        raise HTTPException(status_code=403, detail="Invalid worker secret")
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    storage = StorageService()
    input_dir = storage.nfs_path / "jobs" / str(job_id) / "input"
    
    if not input_dir.exists():
        raise HTTPException(status_code=404, detail="Input directory not found")
    
    # Create a zip of the input directory
    import zipfile
    import io
    import tempfile
    
    zip_path = tempfile.mktemp(suffix=".zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in input_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(input_dir))
    
    return FileResponse(
        path=zip_path,
        filename=f"job_{job_id}_input.zip",
        media_type='application/zip'
    )


@router.post("/{job_id}/upload-logs/")
def upload_logs(
    job_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
):
    """Upload logs from worker to backend storage."""
    from app.config import settings
    
    if payload.get("worker_secret") != settings.WORKER_SECRET:
        raise HTTPException(status_code=403, detail="Invalid worker secret")
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    storage = StorageService()
    log_dir = storage.nfs_path / "jobs" / str(job_id) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "output.log"
    
    with open(log_file, "w") as f:
        f.write(payload.get("logs", ""))
    
    return {"status": "ok"}


@router.post("/{job_id}/upload-outputs/")
def upload_outputs(
    job_id: UUID,
    file: UploadFile = File(...),
    worker_secret: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload output files from worker to backend storage."""
    from app.config import settings
    
    if worker_secret != settings.WORKER_SECRET:
        raise HTTPException(status_code=403, detail="Invalid worker secret")
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    storage = StorageService()
    output_dir = storage.nfs_path / "jobs" / str(job_id) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract zip contents into output directory
    import zipfile
    import io
    
    content = file.file.read()
    with zipfile.ZipFile(io.BytesIO(content), 'r') as zf:
        zf.extractall(output_dir)
    
    return {"status": "ok"}


@router.get("/{job_id}/logs/")
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
    
    try:
        storage = StorageService()
        logs = storage.get_logs(job_id)
        return {"logs": logs}
    except Exception as e:
        print(f"⚠️ Error fetching logs: {e}")
        return {"logs": f"Error al leer logs: {str(e)}"}


@router.get("/{job_id}/outputs/")
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


@router.get("/{job_id}/download")
def download_job_results(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download zipped job results."""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if job.status != JobStatus.COMPLETED:
         raise HTTPException(status_code=400, detail="Job is not completed yet.")

    try:
        storage = StorageService()
        zip_path = storage.create_results_archive(job_id)
        
        return FileResponse(
            path=zip_path,
            filename=f"job_{job_id}_results.zip",
            media_type='application/zip'
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No results found to download")
    except Exception as e:
        print(f"Error downloading results: {e}")
        raise HTTPException(status_code=500, detail=f"Error preparing download: {str(e)}")
