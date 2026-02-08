"""
Home-GPU-Cloud FastAPI Application.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
import os

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

# CORS middleware
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ VALIDATION ERROR: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Datos de entrada inválidos. Revisa el formato.", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"🔥 UNHANDLED ERROR: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor. Inténtalo de nuevo más tarde."},
    )

# Include API routes
app.include_router(api_router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Mount frontend static files
# Priority: 1. React Dist (New), 2. Frontend folder (Legacy)
# Mount Uploads for Ads - ALWAYS mount this regardless of frontend presence
# Use path relative to main.py to work in both Docker and Local
uploads_path = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_path, exist_ok=True)
print(f"📂 Mounting /uploads from: {uploads_path}")
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# Mount frontend static files
# Priority: 1. Embedded Frontend (Monolith Deploy)
react_dist_path = os.path.join(os.path.dirname(__file__), "frontend_dist")

if os.path.exists(react_dist_path):
    print(f"📦 Serving Embedded React Frontend from: {react_dist_path}")
    # Mount assets and other static files first
    app.mount("/assets", StaticFiles(directory=os.path.join(react_dist_path, "assets")), name="assets")
    
    # Explicit favicon route (before catch-all)
    @app.get("/favicon.ico")
    async def serve_favicon():
        favicon_path = os.path.join(react_dist_path, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path, media_type="image/x-icon")
        raise HTTPException(status_code=404, detail="Favicon not found")
    
    # Catch-all for SPA routing
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # First check if the file exists in frontend_dist (for favicon, etc.)
        file_path = os.path.join(react_dist_path, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Ignore API and docs paths
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("uploads/"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        # Serve index.html with NO CACHE to ensure updates propagate immediately
        response = FileResponse(os.path.join(react_dist_path, "index.html"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# reload trigger
# Force Deploy v37
