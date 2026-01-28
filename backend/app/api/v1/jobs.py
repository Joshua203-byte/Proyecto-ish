from uuid import UUID
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

router = APIRouter(prefix="/jobs", tags=["Jobs"])

async def simulate_job_execution(job_id: UUID, script_name: str):
    """Simulate job lifecycle for local development without workers."""
    db = SessionLocal()
    try:
        job_service = JobService(db)
        storage = StorageService()
        log_file = storage.nfs_path / "jobs" / str(job_id) / "logs" / "output.log"
        
        def append_log(text):
            with open(log_file, "a") as f:
                f.write(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {text}\n")

        # 1. Preparing
        await asyncio.sleep(3)
        print(f"🛠️ [SIM] Job {job_id} preparing...")
        job_service.update_status(job_id, JobStatus.PREPARING)
        append_log("Status: PREPARING")
        append_log("System: Downloading docker image: nvidia/cuda:12.1...")
        
        # 2. Running
        await asyncio.sleep(5)
        print(f"🏃 [SIM] Job {job_id} running...")
        job_service.update_status(job_id, JobStatus.RUNNING)
        append_log("Status: RUNNING")
        append_log(f"System: Executing script: {script_name}")
        append_log("System: Starting training loop...")
        append_log("User Code: Epoch 1/10 - loss: 0.8521 - accuracy: 0.6210")
        await asyncio.sleep(5)
        append_log("User Code: Epoch 5/10 - loss: 0.3241 - accuracy: 0.8842")
        await asyncio.sleep(5)
        append_log("User Code: Epoch 10/10 - loss: 0.1215 - accuracy: 0.9650")
        
        # 3. Completed
        await asyncio.sleep(3)
        print(f"✅ [SIM] Job {job_id} completed!")
        job_service.update_status(job_id, JobStatus.COMPLETED, runtime_seconds=18)
        append_log("User Code: Process finished with exit code 0")
        append_log("System: Training completed. Saving outputs...")
        append_log("Status: COMPLETED")
        
        # Create a dummy output file
        output_dir = storage.nfs_path / "jobs" / str(job_id) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "model.pt", "w") as f:
            f.write("DUMMY_MODEL_WEIGHTS")
            
    except Exception as e:
        print(f"❌ [SIM] Error simulating job: {e}")
    finally:
        db.close()

# Celery app for task submission
celery_app = Celery(
    "home-gpu-cloud",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
# Disable eager mode to use real asynchronous workers
celery_app.conf.task_always_eager = False
celery_app.conf.task_eager_propagates = False
celery_app.conf.broker_connection_retry_on_startup = True

@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    background_tasks: BackgroundTasks,
    script_file: UploadFile = File(...),
    dataset_file: UploadFile = File(None),
    memory: str = Form("8g"),
    timeout: int = Form(3600),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new GPU job.
    """
    try:
        print(f"🚀 [JOBS] Starting job creation for user: {current_user.email}")
        billing = BillingService(db)
        
        # Check minimum balance
        print("🔍 [JOBS] Checking balance...")
        if not billing.can_start_job(current_user.id):
            print("❌ [JOBS] Insufficient balance")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient balance. Minimum {settings.MINIMUM_BALANCE_TO_START} credits required."
            )
        
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
