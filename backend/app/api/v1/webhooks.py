"""
Webhook endpoints for worker communication.
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Depends

from app.api.deps import get_db, verify_worker
from app.schemas.job import JobStatusUpdate, BillingHeartbeat, BillingHeartbeatResponse
from app.services.job_service import JobService
from app.services.billing import BillingService


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/job-status")
def update_job_status(
    payload: JobStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Webhook for worker to update job status.
    Called when job transitions between states.
    """
    # Verify worker authentication
    verify_worker(payload.worker_secret)
    
    job_service = JobService(db)
    job = job_service.update_status(
        job_id=payload.job_id,
        status=payload.status,
        container_id=payload.container_id,
        error_message=payload.error_message,
        runtime_seconds=payload.runtime_seconds
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"status": "updated", "job_id": str(job.id)}


@router.post("/billing-heartbeat", response_model=BillingHeartbeatResponse)
def billing_heartbeat(
    payload: BillingHeartbeat,
    db: Session = Depends(get_db)
):
    """
    Webhook for worker billing heartbeat.
    
    Called every minute during job execution.
    Returns should_continue=False to trigger kill switch.
    """
    # Verify worker authentication
    verify_worker(payload.worker_secret)
    
    billing = BillingService(db)
    should_continue, balance = billing.check_and_bill(
        job_id=payload.job_id,
        runtime_minutes=payload.runtime_minutes
    )
    
    message = None
    if not should_continue:
        message = "Insufficient credits - kill switch activated"
    
    return BillingHeartbeatResponse(
        should_continue=should_continue,
        current_balance=balance,
        message=message
    )
