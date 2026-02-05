from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult
from app.api.deps import get_current_user
from app.models.user import User
from app.tasks.celery_app import celery_app
from app.config import settings

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def get_system_status(current_user: User = Depends(get_current_user)):
    """
    Get real-time system status from the Worker Node.
    Dispatches a Celery task and waits (short timeout) for the result.
    """
    try:
        # Dispatch Celery task
        # We use a short soft timeout since this is a UI blocking request
        task = celery_app.send_task(
            "worker.tasks.monitor.get_system_stats",
            queue="gpu_jobs",
            expires=5 # Task expires if not picked up in 5s
        )
        
        # Wait for result (max 3 seconds)
        try:
            stats = task.get(timeout=3.0)
            return stats
        except Exception as e:
            # If timeout or error, return partial/error data but don't crash
            return {
                "status": "partial_outage", 
                "error": "Worker not responding (Timeout)",
                "details": str(e)
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Monitor service unavailable: {str(e)}"
        )
