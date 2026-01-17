"""
Credit Packs API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import CREDIT_PACKS, settings


router = APIRouter(prefix="/packs", tags=["Credit Packs"])


@router.get("/")
def list_credit_packs():
    """
    Get available credit packs for purchase.
    
    Returns list of packs with pricing info for Stripe integration.
    """
    return {
        "packs": CREDIT_PACKS,
        "pricing": {
            "per_hour": settings.PRICE_PER_HOUR,
            "per_minute": settings.PRICE_PER_MINUTE,
            "currency": "USD"
        }
    }


@router.get("/{pack_id}")
def get_credit_pack(pack_id: str):
    """Get details of a specific credit pack."""
    for pack in CREDIT_PACKS:
        if pack["id"] == pack_id:
            return pack
    
    return {"error": "Pack not found"}, 404
