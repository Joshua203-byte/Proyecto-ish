"""
Storage service for file operations on NFS.
"""
import os
import aiofiles
import zipfile
from pathlib import Path
from uuid import UUID
from typing import BinaryIO

from app.config import settings


class StorageService:
    """Service for file storage operations on NFS."""
    
    def __init__(self):
        self.nfs_path = Path(settings.NFS_MOUNT_PATH)
        self.max_upload_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    async def save_script(
        self,
        job_id: UUID,
        filename: str,
        content: bytes
    ) -> str:
        """Save user script to NFS."""
        input_dir = self.nfs_path / "jobs" / str(job_id) / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = input_dir / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return str(file_path.relative_to(self.nfs_path))
    
    async def save_dataset(
        self,
        job_id: UUID,
        file: BinaryIO,
        filename: str
    ) -> str:
        """Save and extract dataset archive to NFS."""
        input_dir = self.nfs_path / "jobs" / str(job_id) / "input"
        data_dir = input_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if it's a zip file
        if filename.endswith('.zip'):
            # Save temporarily
            temp_path = input_dir / filename
            
            async with aiofiles.open(temp_path, 'wb') as f:
                content = file.read()
                if len(content) > self.max_upload_size:
                    raise ValueError(
                        f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                await f.write(content)
            
            # Extract
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(data_dir)
            
            # Remove temp zip
            os.remove(temp_path)
            
            return str(data_dir.relative_to(self.nfs_path))
        else:
            # Save file directly
            file_path = data_dir / filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = file.read()
                if len(content) > self.max_upload_size:
                    raise ValueError(
                        f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                await f.write(content)
            
            return str(file_path.relative_to(self.nfs_path))
    
    def get_output_files(self, job_id: UUID) -> list[dict]:
        """List output files for a job."""
        output_dir = self.nfs_path / "jobs" / str(job_id) / "output"
        
        if not output_dir.exists():
            return []
        
        files = []
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(output_dir)),
                    "size": file_path.stat().st_size,
                })
        
        return files
    
    def get_logs(self, job_id: UUID) -> str:
        """Get job logs from NFS."""
        log_file = self.nfs_path / "jobs" / str(job_id) / "logs" / "output.log"
        
        if not log_file.exists():
            return ""
        
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    
    
    def get_file_path(self, job_id: UUID, relative_path: str) -> Path:
        """Get absolute path for a job file (for downloads)."""
        return self.nfs_path / "jobs" / str(job_id) / "output" / relative_path

    def create_results_archive(self, job_id: UUID) -> Path:
        """Create a zip archive of the job output directory."""
        job_path = self.nfs_path / "jobs" / str(job_id)
        output_dir = job_path / "output"
        zip_path = job_path / "results.zip"
        
        # Determine if outputs exist
        if not output_dir.exists() or not any(output_dir.iterdir()):
             raise FileNotFoundError("No output files found to download.")

        # Create zip file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = Path(root) / file
                    # Relative path inside zip
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)
                    
        return zip_path
