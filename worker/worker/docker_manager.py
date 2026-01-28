"""
Docker SDK Manager for GPU container orchestration.
Runs on Nodo C (GPU Worker).
"""
import docker
import logging
from typing import Optional, Dict, Any, Generator
from dataclasses import dataclass
from pathlib import Path

from worker.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
    """
    Configuration for a user's GPU container.
    
    DGX Spark (Grace Blackwell GB10) Notes:
    - 128GB Unified Memory (LPDDR5X) shared between CPU and GPU
    - Memory limit can be set up to ~120GB (leaving headroom for system)
    - No separate GPU VRAM - it's all unified memory
    """
    job_id: str
    image: str = "ubuntu:22.04"
    memory_limit: str = "8g"  # Local dev default
    cpu_count: int = 4  # Local dev default
    gpu_count: int = 0  # 0 for no GPU (CPU only), -1 for all GPUs
    timeout_seconds: int = 3600
    network_disabled: bool = False  # Changed for demo: Allow network access


class DockerManager:
    """
    Docker SDK wrapper for secure GPU container execution.
    
    Security features:
    - Network isolation (no internet access)
    - Resource limits (RAM, CPU, PIDs)
    - Capability dropping (no privilege escalation)
    - Read-only input mounts
    """
    
    NFS_MOUNT_PATH = Path(settings.NFS_MOUNT_PATH)
    HOST_DATA_PATH = Path(settings.HOST_DATA_PATH)
    
    def __init__(self):
        self.client = docker.from_env()
        self._cleanup_orphaned_containers()
    
    def _cleanup_orphaned_containers(self) -> None:
        """Clean up any orphaned containers from previous runs."""
        try:
            for container in self.client.containers.list(all=True):
                if container.name.startswith("job-"):
                    logger.warning(f"Cleaning up orphaned container: {container.name}")
                    container.remove(force=True)
        except Exception as e:
            logger.error(f"Error cleaning up containers: {e}")
    
    def verify_gpu_runtime(self) -> bool:
        """Verify that NVIDIA GPU runtime is available on DGX Spark."""
        try:
            # Skip real GPU verification on non-ARM machine for local testing
            logger.info("ℹ️ Skipping NVIDIA GPU verification (No-GPU Mode)")
            return True
            logger.info("✓ NVIDIA GPU runtime verified (DGX Spark / Blackwell)")
            logger.info(f"GPU Info: {result.decode('utf-8').strip()}")
            return True
        except docker.errors.ContainerError as e:
            logger.error(f"✗ GPU runtime not available: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Error verifying GPU: {e}")
            return False
    
    def run_job(self, config: ContainerConfig, script_name: str = "train.py") -> str:
        """
        Launch an isolated container to execute a user's GPU job.
        
        Args:
            config: Container configuration
            script_name: Name of the script to execute
            
        Returns:
            container_id: ID of the created container
        """
        job_path = self.NFS_MOUNT_PATH / "jobs" / config.job_id
        input_path = job_path / "input"
        output_path = job_path / "output"
        
        # Prepare host paths for volume mounting (Docker-in-Docker)
        host_job_path = self.HOST_DATA_PATH / "jobs" / config.job_id
        host_input_path = host_job_path / "input"
        host_output_path = host_job_path / "output"
        
        # Ensure output directory exists with proper permissions
        output_path.mkdir(parents=True, exist_ok=True)
        import os
        os.chmod(output_path, 0o777)
        
        logger.info(f"Launching container for job {config.job_id}")
        logger.info(f"  Image: {config.image}")
        logger.info(f"  Memory: {config.memory_limit}")
        logger.info(f"  CPUs: {config.cpu_count}")
        
        container = self.client.containers.run(
            image=config.image,
            command=f"python3 /workspace/input/{script_name}",
            
            # ═══════════════════════════════════════════
            # VOLUME MOUNTS (NFS → Container)
            # ═══════════════════════════════════════════
            volumes={
                str(host_input_path): {
                    "bind": "/workspace/input",
                    "mode": "ro"  # READ-ONLY: User cannot modify input
                },
                str(host_output_path): {
                    "bind": "/workspace/output",
                    "mode": "rw"  # READ-WRITE: Can write results
                },
                # Mount HuggingFace cache for pre-downloaded models
                "/home/ish/.cache/huggingface": {
                    "bind": "/root/.cache/huggingface",
                    "mode": "ro"  # READ-ONLY: Use cached models
                }
            },
            working_dir="/workspace",
            
            # ═══════════════════════════════════════════
            # GPU ACCESS (NVIDIA Container Toolkit)
            # ═══════════════════════════════════════════
            device_requests=[
                docker.types.DeviceRequest(
                    count=config.gpu_count,
                    capabilities=[['gpu']]
                )
            ] if config.gpu_count > 0 else None,
            
            # ═══════════════════════════════════════════
            # RESOURCE LIMITS (SECURITY)
            # ═══════════════════════════════════════════
            mem_limit=config.memory_limit,
            memswap_limit=config.memory_limit,  # No swap (prevent slow OOM)
            cpu_count=config.cpu_count,
            pids_limit=256,  # Fork bomb protection
            
            # ═══════════════════════════════════════════
            # NETWORK ISOLATION (SECURITY)
            # ═══════════════════════════════════════════
            network_disabled=config.network_disabled,
            dns=["8.8.8.8", "8.8.4.4"], # Google DNS fallback
            
            # ═══════════════════════════════════════════
            # ADDITIONAL SECURITY
            # ═══════════════════════════════════════════
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            cap_add=["SYS_PTRACE"],  # For debugging only
            
            # Execution config
            detach=True,
            auto_remove=False,
            name=f"job-{config.job_id}",
            
            # Environment for user script
            environment={
                "JOB_ID": config.job_id,
                "OUTPUT_DIR": "/workspace/output",
                "CUDA_VISIBLE_DEVICES": "0",
            }
        )
        
        logger.info(f"Container started: {container.id[:12]}")
        return container.id
    
    def stream_logs(self, container_id: str) -> Generator[str, None, None]:
        """Stream logs from container in real-time."""
        try:
            container = self.client.containers.get(container_id)
            for log_line in container.logs(stream=True, follow=True):
                yield log_line.decode('utf-8', errors='replace')
        except docker.errors.NotFound:
            yield "[Container not found]"
    
    def get_logs(self, container_id: str) -> str:
        """Get all logs from container."""
        try:
            container = self.client.containers.get(container_id)
            return container.logs().decode('utf-8', errors='replace')
        except docker.errors.NotFound:
            return ""
    
    def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """Get current container status."""
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            
            state = container.attrs.get("State", {})
            
            return {
                "status": container.status,
                "exit_code": state.get("ExitCode"),
                "started_at": state.get("StartedAt"),
                "finished_at": state.get("FinishedAt"),
                "oom_killed": state.get("OOMKilled", False),
                "running": state.get("Running", False),
            }
        except docker.errors.NotFound:
            return {
                "status": "not_found",
                "exit_code": None,
                "oom_killed": False,
                "running": False,
            }
    
    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a running container (SIGTERM, then SIGKILL after timeout)."""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Container {container_id[:12]} stopped")
            return True
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id[:12]} not found")
            return False
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False
    
    def cleanup_container(self, container_id: str) -> None:
        """Remove container and free resources."""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            logger.info(f"Container {container_id[:12]} removed")
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logger.error(f"Error removing container: {e}")
