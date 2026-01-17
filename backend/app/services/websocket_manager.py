"""
WebSocket Connection Manager for real-time log streaming.

Handles multiple client connections per job and broadcasts log updates.
Uses Redis pub/sub for receiving logs from workers.
"""
import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from redis import asyncio as aioredis
from app.config import settings


class ConnectionManager:
    """Manages WebSocket connections for real-time log streaming."""
    
    def __init__(self):
        # job_id -> set of connected websockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def connect_redis(self):
        """Initialize Redis connection for pub/sub."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def disconnect_redis(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept a new WebSocket connection for a job."""
        await websocket.accept()
        
        if job_id not in self._connections:
            self._connections[job_id] = set()
        
        self._connections[job_id].add(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": f"Connected to log stream for job {job_id[:8]}"
        })
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection."""
        if job_id in self._connections:
            self._connections[job_id].discard(websocket)
            if not self._connections[job_id]:
                del self._connections[job_id]
    
    async def broadcast_to_job(self, job_id: str, message: dict):
        """Send a message to all clients watching a specific job."""
        if job_id not in self._connections:
            return
        
        disconnected = set()
        
        for websocket in self._connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self._connections[job_id].discard(ws)
    
    async def send_log_line(self, job_id: str, line: str, timestamp: Optional[str] = None):
        """Send a single log line to all connected clients."""
        message = {
            "type": "log",
            "job_id": job_id,
            "content": line,
        }
        if timestamp:
            message["timestamp"] = timestamp
        
        await self.broadcast_to_job(job_id, message)
    
    async def send_status_update(self, job_id: str, status: str, details: Optional[dict] = None):
        """Send a job status update to all connected clients."""
        message = {
            "type": "status",
            "job_id": job_id,
            "status": status,
        }
        if details:
            message["details"] = details
        
        await self.broadcast_to_job(job_id, message)
    
    async def start_pubsub_listener(self):
        """Start listening to Redis pub/sub for log updates."""
        if self._running:
            return
        
        await self.connect_redis()
        self._running = True
        
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe("logs:*")  # Subscribe to all job log channels
        
        try:
            async for message in pubsub.listen():
                if not self._running:
                    break
                
                if message["type"] == "pmessage":
                    # Extract job_id from channel (logs:job_id)
                    channel = message["channel"]
                    job_id = channel.split(":", 1)[1] if ":" in channel else None
                    
                    if job_id:
                        try:
                            data = json.loads(message["data"])
                            if data.get("type") == "log":
                                await self.send_log_line(
                                    job_id,
                                    data.get("content", ""),
                                    data.get("timestamp")
                                )
                            elif data.get("type") == "status":
                                await self.send_status_update(
                                    job_id,
                                    data.get("status", "unknown"),
                                    data.get("details")
                                )
                        except json.JSONDecodeError:
                            # Raw log line
                            await self.send_log_line(job_id, message["data"])
        finally:
            await pubsub.unsubscribe()
            self._running = False
    
    async def stop_pubsub_listener(self):
        """Stop the pub/sub listener."""
        self._running = False
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass
    
    def get_active_connections(self) -> Dict[str, int]:
        """Get count of active connections per job."""
        return {job_id: len(conns) for job_id, conns in self._connections.items()}


# Global connection manager instance
manager = ConnectionManager()


async def publish_log(redis: aioredis.Redis, job_id: str, content: str, log_type: str = "log"):
    """Publish a log message to Redis for broadcasting to WebSocket clients.
    
    This function is called by the worker to stream logs.
    """
    message = json.dumps({
        "type": log_type,
        "content": content,
        "job_id": job_id
    })
    await redis.publish(f"logs:{job_id}", message)


async def publish_status(redis: aioredis.Redis, job_id: str, status: str, details: Optional[dict] = None):
    """Publish a status update for a job."""
    message = json.dumps({
        "type": "status",
        "status": status,
        "job_id": job_id,
        "details": details or {}
    })
    await redis.publish(f"logs:{job_id}", message)
