import time
import os
import shutil
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models.job import Job, JobStatus
from app.tasks.celery_app import celery_app
from app.services.storage import StorageService
from app.services.billing import BillingService
from app.models.user import User

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@celery_app.task(bind=True, name="worker.tasks.gpu_tasks.execute_gpu_job")
def execute_gpu_job(self, job_id: str, user_id: str, script_name: str, image: str, memory_limit: str, cpu_count: int, timeout_seconds: int, launch_args: str):
    """
    Execute a GPU job (Simulated or Real).
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"❌ Job {job_id} not found in DB")
            return "Job not found"

        print(f"🚀 Starting Job {job_id}")
        
        # 1. Update Status to RUNNING
        job.status = JobStatus.RUNNING
        job.started_at = func.now()
        db.commit()

        # 2. Setup Logging
        storage = StorageService()
        log_path = storage.nfs_path / "jobs" / str(job.id) / "logs" / "output.log"
        
        def log(message):
            with open(log_path, "a") as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")

        log(f"--- Worker started execution ---")
        log(f"Image: {image}")
        log(f"Script: {script_name}")
        log(f"Allocated: {memory_limit} RAM, {cpu_count} CPUs")
        
        # 3. Real Execution using Subprocess
        log(f"--- Launching Process ---")
        
        # Construct path to script
        # NFS mount path inside worker is /mnt/home-gpu-cloud
        # Script is at jobs/{job_id}/input/{script_name}
        script_full_path = storage.nfs_path / "jobs" / str(job.id) / "input" / script_name
        
        if not script_full_path.exists():
            log(f"❌ Script not found at: {script_full_path}")
            raise FileNotFoundError(f"Script not found: {script_full_path}")
            
        import subprocess
        
        # Prepare command
        cmd = ["python", str(script_full_path)]
        if launch_args:
            cmd.extend(launch_args.split())
            
        log(f"Command: {' '.join(cmd)}")
        
        # Execute
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1, # Line buffered
            cwd=script_full_path.parent # Run from input dir so data is accessible
        )
        
        # Stream logs
        with open(log_path, "a") as f:
            for line in process.stdout:
                # Check cancellation during execution
                # (Optimization: Don't check DB on every line, maybe every N seconds or lines)
                f.write(line)
                f.flush()
                
        process.wait()
        
        if process.returncode == 0:
            log("✅ Execution completed successfully.")
        else:
            log(f"⚠️ Process exited with code {process.returncode}")
            raise Exception(f"Script failed with exit code {process.returncode}")
        
        # 4. Success Completion
        job.status = JobStatus.COMPLETED
        job.completed_at = func.now()
        db.commit()
        
        return "Completed"

    except Exception as e:
        print(f"🔥 Job failed: {e}")
        # Try to log failure
        try:
            with open(log_path, "a") as f:
                f.write(f"\n❌ FATAL ERROR: {str(e)}\n")
        except:
            pass
            
        if job:
            job.status = JobStatus.FAILED
            db.commit()
        
        raise e
    finally:
        db.close()
