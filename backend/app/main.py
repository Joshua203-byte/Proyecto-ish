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
    try:
        from app.database import init_db
        init_db()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        # We don't exit here to allow the app to start even if DB is down (e.g. for maintenance page)
    
    # Start WebSocket pub/sub listener
    pubsub_task = None
    try:
        # Check if Redis is reachable before starting listener
        await manager.connect_redis()
        pubsub_task = asyncio.create_task(manager.start_pubsub_listener())
        print("✅ WebSocket manager started")
    except Exception as e:
        print(f"⚠️  Redis not available (WebSocket disabled): {e}")
    
    yield
    
    # Shutdown: Stop pub/sub listener and disconnect Redis
    try:
        if pubsub_task:
            await manager.stop_pubsub_listener()
            pubsub_task.cancel()
            try:
                await pubsub_task
            except asyncio.CancelledError:
                pass
        await manager.disconnect_redis()
    except Exception as e:
        print(f"⚠️  Error during shutdown: {e}")


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

