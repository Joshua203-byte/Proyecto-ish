import time
import os
import shutil
import zipfile
import requests
from pathlib import Path
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

# Backend URL for downloading files (Heroku production)
BACKEND_URL = os.environ.get("BACKEND_URL", "https://www.epochly.co")
WORKER_SECRET = os.environ.get("WORKER_SECRET", "secret123")

def download_input_files(job_id: str, storage: StorageService):
    """Download input files from the backend API if not present locally."""
    input_dir = storage.nfs_path / "jobs" / str(job_id) / "input"
    
    if input_dir.exists() and any(input_dir.iterdir()):
        print(f"📁 Input files already exist at {input_dir}")
        return True
    
    # Create directories
    input_dir.mkdir(parents=True, exist_ok=True)
    log_dir = storage.nfs_path / "jobs" / str(job_id) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    output_dir = storage.nfs_path / "jobs" / str(job_id) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download from backend API
    url = f"{BACKEND_URL}/api/v1/jobs/{job_id}/download-input/?worker_secret={WORKER_SECRET}"
    print(f"⬇️  Downloading input files from {BACKEND_URL}...")
    
    try:
        resp = requests.get(url, timeout=300)
        if resp.status_code != 200:
            print(f"❌ Failed to download input files: HTTP {resp.status_code}")
            return False
        
        # Save and extract zip
        zip_path = input_dir / "_input.zip"
        with open(zip_path, "wb") as f:
            f.write(resp.content)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(input_dir)
        
        zip_path.unlink()  # Remove zip after extraction
        print(f"✅ Input files downloaded and extracted to {input_dir}")
        return True
    except Exception as e:
        print(f"❌ Error downloading input files: {e}")
        return False

@celery_app.task(bind=True, name="worker.tasks.gpu_tasks.execute_gpu_job")
def execute_gpu_job(self, job_id: str, user_id: str, script_name: str, image: str, memory_limit: str, cpu_count: int, timeout_seconds: int, launch_args: str):
    """
    Execute a GPU job (Simulated or Real).
    """
    db = SessionLocal()
    log_path = None
    job = None
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

        # 2. Setup Storage & Download files
        storage = StorageService()
        
        # Ensure directories exist
        log_dir = storage.nfs_path / "jobs" / str(job.id) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "output.log"
        
        def log(message):
            with open(log_path, "a") as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")

        log(f"--- Worker started execution ---")
        log(f"Image: {image}")
        log(f"Script: {script_name}")
        log(f"Allocated: {memory_limit} RAM, {cpu_count} CPUs")
        
        # 3. Download input files from backend if not present
        log("📥 Checking/downloading input files from cloud...")
        if not download_input_files(job_id, storage):
            log("❌ Failed to download input files from backend")
            raise FileNotFoundError("Could not download input files from backend")
        log("✅ Input files ready")
        
        # 4. Real Execution using Subprocess
        log(f"--- Launching Process ---")
        
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
            bufsize=1,
            cwd=script_full_path.parent
        )
        
        # Stream logs
        with open(log_path, "a") as f:
            for line in process.stdout:
                f.write(line)
                f.flush()
                
        process.wait()
        
        if process.returncode == 0:
            log("✅ Execution completed successfully.")
        else:
            log(f"⚠️ Process exited with code {process.returncode}")
            raise Exception(f"Script failed with exit code {process.returncode}")
        
        # 5. Success Completion
        job.status = JobStatus.COMPLETED
        job.completed_at = func.now()
        db.commit()
        
        return "Completed"

    except Exception as e:
        print(f"🔥 Job failed: {e}")
        try:
            if log_path:
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
