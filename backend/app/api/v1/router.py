"""
API v1 Router - aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.websocket import router as websocket_router
from app.api.v1.packs import router as packs_router


router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(jobs_router)
router.include_router(wallet_router)
router.include_router(webhooks_router)
router.include_router(websocket_router)
router.include_router(packs_router)


