"""
WebSocket API endpoint for real-time log streaming.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import jwt

from app.config import settings
from app.database import get_db
from app.models import Job
from app.services.websocket_manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


async def verify_ws_token(token: str) -> dict:
    """Verify JWT token from WebSocket connection."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.InvalidTokenError:
        return None


@router.websocket("/logs/{job_id}")
async def websocket_job_logs(
    websocket: WebSocket,
    job_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for streaming job logs in real-time.
    
    Connect with: ws://host/api/v1/ws/logs/{job_id}?token=<jwt_token>
    
    Messages received:
    - {"type": "connected", "job_id": "...", "message": "..."}
    - {"type": "log", "job_id": "...", "content": "...", "timestamp": "..."}
    - {"type": "status", "job_id": "...", "status": "running|completed|failed"}
    - {"type": "error", "message": "..."}
    """
    # Verify token
    payload = await verify_ws_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    
    # Verify job exists and belongs to user
    db = next(get_db())
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            await websocket.close(code=4004, reason="Job not found")
            return
        
        if str(job.user_id) != user_id:
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Accept connection and add to manager
        await manager.connect(websocket, job_id)
        
        # Send initial job status
        await manager.send_status_update(job_id, job.status, {
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
        })
        
        # If job has existing logs, send them first
        if job.logs:
            for line in job.logs.split('\n'):
                if line.strip():
                    await manager.send_log_line(job_id, line)
        
        # Keep connection alive and listen for client messages
        try:
            while True:
                # Wait for messages from client (ping/pong, close, etc.)
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(websocket, job_id)
            
    finally:
        db.close()


@router.get("/connections")
async def get_active_connections():
    """Get count of active WebSocket connections per job (admin endpoint)."""
    return {
        "connections": manager.get_active_connections(),
        "total": sum(manager.get_active_connections().values())
    }
