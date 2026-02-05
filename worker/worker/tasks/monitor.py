
import psutil
import shutil
import platform
import logging
import random # For mocking GPU data in dev
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="worker.tasks.monitor.get_system_stats")
def get_system_stats() -> dict:
    """
    Gather system resources statistics from the Worker Node.
    Returns JSON with CPU, RAM, Disk, and GPU metrics.
    """
    try:
        # 1. System Metrics (Real)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024**3), 1)
        ram_used_gb = round(mem.used / (1024**3), 1)
        ram_percent = mem.percent
        
        disk = shutil.disk_usage("/")
        disk_total_gb = round(disk.total / (1024**3), 1)
        disk_used_gb = round(disk.used / (1024**3), 1)
        disk_percent = round((disk.used / disk.total) * 100, 1)

        # 2. GPU Metrics (Mocked for dev, or nvidia-smi if available)
        # In a real scenario, we would use pynvml or run nvidia-smi
        gpu_stats = {
            "name": "NVIDIA DGX Spark (Simulated)",
            "temperature": random.randint(35, 75),
            "utilization": random.randint(0, 100),
            "memory_total": 128, # GB Unified
            "memory_used": random.randint(2, 64),
            "memory_percent": 0 # Calc below
        }
        gpu_stats["memory_percent"] = round((gpu_stats["memory_used"] / gpu_stats["memory_total"]) * 100, 1)

        # Detect if we are on ARM64 (Grace Blackwell environment check)
        arch = platform.machine()
        is_arm = arch == "aarch64"

        return {
            "status": "online",
            "architecture": arch,
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "ram": {
                "total_gb": ram_total_gb,
                "used_gb": ram_used_gb,
                "percent": ram_percent
            },
            "disk": {
                "total_gb": disk_total_gb,
                "used_gb": disk_used_gb,
                "percent": disk_percent
            },
            "gpu": gpu_stats,
            "is_dgx": is_arm # Flag to show specific UI branding
        }

    except Exception as e:
        logger.error(f"Error gathering stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
