"""
GPU Tasks - Celery tasks for GPU job execution.
Runs on Nodo C (GPU Worker) - NVIDIA DGX Spark (Grace Blackwell ARM64).
"""
import time
import platform
import logging
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from celery import Task
from worker.celery_app import celery_app
from worker.docker_manager import DockerManager, ContainerConfig
from worker.config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# ARCHITECTURE VERIFICATION (DGX Spark ARM64)
# ═══════════════════════════════════════════════════════════════════
def log_system_info():
    """Log system architecture info at startup."""
    arch = platform.machine()
    system = platform.system()
    python_version = platform.python_version()
    
    logger.info("=" * 60)
    logger.info("HOME-GPU-CLOUD WORKER STARTUP")
    logger.info("=" * 60)
    logger.info(f"  Architecture: {arch}")
    logger.info(f"  System: {system}")
    logger.info(f"  Python: {python_version}")
    
    if arch == "aarch64":
        logger.info("  ✓ Running on ARM64 (DGX Spark / Grace Blackwell)")
    elif arch == "x86_64":
        logger.warning("  ⚠ Running on x86_64 - Not DGX Spark target architecture!")
    else:
        logger.warning(f"  ⚠ Unexpected architecture: {arch}")
    
    logger.info("=" * 60)

# Log on module import
log_system_info()


class GPUTask(Task):
    """Base task class with persistent Docker manager."""
    _docker_manager: Optional[DockerManager] = None
    
    @property
    def docker_manager(self) -> DockerManager:
        if self._docker_manager is None:
            self._docker_manager = DockerManager()
        return self._docker_manager


@celery_app.task(
    bind=True,
    base=GPUTask,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def execute_gpu_job(
    self,
    job_id: str,
    user_id: str,
    script_name: str = "train.py",
    image: str = "ubuntu:22.04",
    memory_limit: str = "4g",
    cpu_count: int = 2,
    timeout_seconds: int = 3600,
) -> dict:
    """
    Main task: Execute user's GPU job in an isolated container.
    
    Flow:
    1. Notify backend: status = PREPARING
    2. Launch container with resource limits
    3. Monitor execution (logs + heartbeats)
    4. Send billing heartbeat every 60 seconds
    5. On completion: status = COMPLETED/FAILED
    
    Kill Switch: If billing returns should_continue=False,
    immediately stop the container.
    """
    container_id = None
    start_time = datetime.utcnow()
    
    try:
        # ═══════════════════════════════════════════
        # PHASE 1: Preparation
        # ═══════════════════════════════════════════
        logger.info(f"Starting job {job_id}")
        _update_job_status(job_id, "preparing")
        
        config = ContainerConfig(
            job_id=job_id,
            image=image,
            memory_limit=memory_limit,
            cpu_count=cpu_count,
            timeout_seconds=timeout_seconds,
        )
        
        # ═══════════════════════════════════════════
        # PHASE 2: Launch Container
        # ═══════════════════════════════════════════
        container_id = self.docker_manager.run_job(config, script_name)
        _update_job_status(job_id, "running", container_id=container_id)
        
        # ═══════════════════════════════════════════
        # PHASE 3: Monitoring with Billing Loop
        # ═══════════════════════════════════════════
        deadline = start_time + timedelta(seconds=timeout_seconds)
        last_billing_check = start_time
        billing_interval = timedelta(seconds=60)
        
        while True:
            # Check container status
            status = self.docker_manager.get_container_status(container_id)
            
            if not status["running"]:
                logger.info(f"Container exited for job {job_id}")
                break
            
            # Check timeout
            if datetime.utcnow() > deadline:
                logger.warning(f"Job {job_id} timeout reached")
                self.docker_manager.stop_container(container_id)
                _update_job_status(job_id, "failed", error="Timeout exceeded")
                break
            
            # ═══════════════════════════════════════════
            # BILLING HEARTBEAT (every 60 seconds)
            # ═══════════════════════════════════════════
            if datetime.utcnow() - last_billing_check >= billing_interval:
                last_billing_check = datetime.utcnow()
                runtime_minutes = (datetime.utcnow() - start_time).seconds // 60
                
                should_continue = _billing_heartbeat(job_id, runtime_minutes)
                
                if not should_continue:
                    # ═══════════════════════════════════════════
                    # KILL SWITCH ACTIVATED!
                    # ═══════════════════════════════════════════
                    logger.warning(f"Job {job_id} - Kill switch: insufficient credits")
                    self.docker_manager.stop_container(container_id)
                    _update_job_status(job_id, "killed_no_credits")
                    
                    return {
                        "success": False,
                        "reason": "insufficient_credits",
                        "runtime_seconds": (datetime.utcnow() - start_time).seconds
                    }
            
            # Small pause to avoid CPU saturation
            time.sleep(5)
        
        # ═══════════════════════════════════════════
        # PHASE 4: Finalization
        # ═══════════════════════════════════════════
        final_status = self.docker_manager.get_container_status(container_id)
        runtime_seconds = (datetime.utcnow() - start_time).seconds
        
        # Save logs to NFS
        logs = self.docker_manager.get_logs(container_id)
        _save_logs(job_id, logs)
        
        if final_status.get("oom_killed"):
            _update_job_status(job_id, "failed", error="Out of Memory (OOM)")
            return {
                "success": False,
                "reason": "oom_killed",
                "runtime_seconds": runtime_seconds
            }
        
        exit_code = final_status.get("exit_code", -1)
        
        if exit_code == 0:
            _update_job_status(job_id, "completed", runtime_seconds=runtime_seconds)
            return {
                "success": True,
                "runtime_seconds": runtime_seconds
            }
        else:
            _update_job_status(
                job_id, "failed",
                error=f"Exit code: {exit_code}",
                runtime_seconds=runtime_seconds
            )
            return {
                "success": False,
                "exit_code": exit_code,
                "runtime_seconds": runtime_seconds
            }
    
    except Exception as e:
        logger.exception(f"Error executing job {job_id}")
        _update_job_status(job_id, "failed", error=str(e))
        raise
    
    finally:
        # Always cleanup container
        if container_id:
            self.docker_manager.cleanup_container(container_id)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (API Communication)
# ═══════════════════════════════════════════════════════════════════

def _update_job_status(
    job_id: str,
    status: str,
    container_id: str = None,
    error: str = None,
    runtime_seconds: int = None
) -> None:
    """Notify backend of job status change."""
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(
                f"{settings.BACKEND_URL}/api/v1/webhooks/job-status",
                json={
                    "job_id": job_id,
                    "status": status,
                    "container_id": container_id,
                    "error_message": error,
                    "runtime_seconds": runtime_seconds,
                    "worker_secret": settings.WORKER_SECRET,
                }
            )
            response.raise_for_status()
            logger.info(f"Job {job_id} status updated to: {status}")
    except Exception as e:
        logger.error(f"Error updating job status: {e}")


def _billing_heartbeat(job_id: str, runtime_minutes: int) -> bool:
    """
    Send billing heartbeat to backend.
    
    Returns:
        should_continue: False triggers kill switch
    """
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(
                f"{settings.BACKEND_URL}/api/v1/webhooks/billing-heartbeat",
                json={
                    "job_id": job_id,
                    "runtime_minutes": runtime_minutes,
                    "worker_secret": settings.WORKER_SECRET,
                }
            )
            data = response.json()
            should_continue = data.get("should_continue", False)
            
            if not should_continue:
                logger.warning(f"Billing: {data.get('message', 'Kill signal received')}")
            
            return should_continue
    except Exception as e:
        logger.error(f"Billing heartbeat error: {e}")
        # Fail-open: continue on communication error
        return True


def _save_logs(job_id: str, logs: str) -> None:
    """Save container logs to NFS."""
    try:
        log_dir = Path(settings.NFS_MOUNT_PATH) / "jobs" / job_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "output.log"
        with open(log_file, "w") as f:
            f.write(logs)
        
        logger.info(f"Logs saved to {log_file}")
    except Exception as e:
        logger.error(f"Error saving logs: {e}")
