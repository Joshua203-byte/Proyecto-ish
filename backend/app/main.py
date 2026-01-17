"""
Home-GPU-Cloud FastAPI Application.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import router as api_router
from app.services.websocket_manager import manager

# NOTE: Database tables are managed by Alembic migrations
# Run: alembic upgrade head


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup: Initialize database tables
    from app.database import init_db
    init_db()
    
    # Start WebSocket pub/sub listener (ignore Redis errors for local dev)
    try:
        pubsub_task = asyncio.create_task(manager.start_pubsub_listener())
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        pubsub_task = None
    
    yield
    
    # Shutdown: Stop pub/sub listener and disconnect Redis
    if pubsub_task:
        await manager.stop_pubsub_listener()
        await manager.disconnect_redis()
        pubsub_task.cancel()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="GPU Compute-as-a-Service Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware - Allow all origins for development (file:// protocol)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
def root():
    """Root endpoint - health check."""
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

