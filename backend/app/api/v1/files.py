"""
File upload API endpoints.
"""
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User


router = APIRouter(prefix="/files", tags=["Files"])


class FileUploadResponse(BaseModel):
    """Response for file upload."""
    filename: str
    path: str
    size: int


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file (script or dataset) to user storage.
    
    The file will be stored in: {NFS_PATH}/users/{user_id}/uploads/{filename}
    """
    
    # Validate file extension
    allowed_extensions = {'.py', '.ipynb', '.zip', '.txt', '.json', '.csv'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create user directory if not exists
    base_path = Path(settings.NFS_MOUNT_PATH)
    user_upload_dir = base_path / "users" / str(current_user.id) / "uploads"
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Secure filename
    safe_filename = Path(file.filename).name
    file_path = user_upload_dir / safe_filename
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get relative path for Job reference
        # We need the path relative to NFS root so the worker can find it
        relative_path = file_path.relative_to(base_path)
        
        return FileUploadResponse(
            filename=safe_filename,
            path=str(relative_path).replace("\\", "/"),  # Normalize for cross-platform
            size=file_path.stat().st_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )


@router.get("/list", response_model=List[FileUploadResponse])
def list_files(current_user: User = Depends(get_current_user)):
    """List uploaded files."""
    base_path = Path(settings.NFS_MOUNT_PATH)
    user_upload_dir = base_path / "users" / str(current_user.id) / "uploads"
    
    if not user_upload_dir.exists():
        return []
        
    files = []
    for f in user_upload_dir.glob("*"):
        if f.is_file():
            files.append(FileUploadResponse(
                filename=f.name,
                path=str(f.relative_to(base_path)).replace("\\", "/"),
                size=f.stat().st_size
            ))
            
    return files
