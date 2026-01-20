"""
Wompi El Salvador Payment API endpoints.
Uses OAuth 2.0 Client Credentials flow for authentication.
"""
import hashlib
import uuid
import httpx
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.billing import BillingService
from app.config import settings, CREDIT_PACKS


router = APIRouter(prefix="/payments", tags=["Payments"])


# ═══════════════════════════════════════════════════════════════════════════════
# TOKEN CACHE (Simple in-memory cache)
# ═══════════════════════════════════════════════════════════════════════════════

_token_cache = {
    "access_token": None,
    "expires_at": None
}


async def get_wompi_token() -> str:
    """
    Get Wompi access token using OAuth 2.0 Client Credentials flow.
    Caches the token until it expires.
    """
    global _token_cache
    
    # Check if we have a valid cached token
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.utcnow() < _token_cache["expires_at"]:
            return _token_cache["access_token"]
    
    # Request new token
    token_url = "https://id.wompi.sv/connect/token"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "audience": "wompi_api",
                "client_id": settings.WOMPI_SV_APP_ID,
                "client_secret": settings.WOMPI_SV_API_SECRET
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to authenticate with Wompi: {response.text}"
            )
        
        data = response.json()
        
        # Cache the token
        _token_cache["access_token"] = data["access_token"]
        # Expire 5 minutes before actual expiry for safety
        expires_in = data.get("expires_in", 3600) - 300
        _token_cache["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
        
        return _token_cache["access_token"]


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class PaymentLinkRequest(BaseModel):
    """Request for creating a payment link."""
    pack_id: str  # pack_pilot, pack_researcher, pack_lab


class PaymentLinkResponse(BaseModel):
    """Response with payment link URL."""
    payment_url: str
    reference: str
    amount_usd: float
    pack_name: str


# ═══════════════════════════════════════════════════════════════════════════════
# CREATE PAYMENT LINK ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/create-link", response_model=PaymentLinkResponse)
async def create_payment_link(
    request: PaymentLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Wompi payment link for purchasing credits.
    
    Returns a URL that the user can use to complete payment.
    """
    # Find pack
    pack = next((p for p in CREDIT_PACKS if p["id"] == request.pack_id), None)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pack_id: {request.pack_id}"
        )
    
    # Generate unique reference
    reference = f"GPU-{current_user.id}-{uuid.uuid4().hex[:8]}"
    
    # Get OAuth token
    try:
        token = await get_wompi_token()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment service unavailable: {str(e)}"
        )
    
    # Create payment link via Wompi SV API
    # Wompi El Salvador uses /EnlacePago endpoint
    api_url = "https://api.wompi.sv/EnlacePago"
    
    # Amount in cents (USD)
    amount_cents = int(pack["price_usd"] * 100)
    
    # Create a random ID for the link reference
    random_id = str(uuid.uuid4())[:8]
    
    # Wompi SV payload format
    payload = {
        # Put user_id back in reference so we know who to credit!
        "identificadorEnlaceComercio": f"GPU-{current_user.id}-{random_id}",
        "monto": float(pack["price_usd"]),  # Ensure float
        "nombreProducto": "Creditos GPU"  # Very simple name
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            api_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code not in [200, 201]:
            print(f"Wompi error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create payment link: {response.text}"
            )
        
        data = response.json()
        print(f"Wompi response: {data}")
        
        # Get the payment URL from response
        # Wompi SV returns links like: https://lk.wompi.sv/xxxxx
        payment_url = data.get("urlEnlace") or data.get("url") or f"https://lk.wompi.sv/{data.get('idEnlace', '')}"
        
        return PaymentLinkResponse(
            payment_url=payment_url,
            reference=reference,
            amount_usd=pack["price_usd"],
            pack_name=pack["name"]
        )


# ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOK ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/webhook")
async def wompi_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Wompi El Salvador webhook events.
    
    Wompi SV sends webhooks with this structure:
    {
        "ResultadoTransaccion": "ExitosaAprobada",
        "Monto": 20,
        "EnlacePago": {
            "IdentificadorEnlaceComercio": "GPU-{user_id}-{random}"
        }
    }
    """
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    print(f"📨 Wompi webhook received: {event}")
    
    # Wompi El Salvador format (Pascal case)
    resultado = event.get("ResultadoTransaccion", "")
    monto = event.get("Monto", 0)  # Amount in USD (not cents)
    cantidad = event.get("Cantidad", 1)
    es_productiva = event.get("EsProductiva", False)
    
    # Get reference from EnlacePago
    enlace_pago = event.get("EnlacePago", {})
    reference = enlace_pago.get("IdentificadorEnlaceComercio", "")
    
    print(f"   Resultado: {resultado}")
    print(f"   Monto: ${monto}, Cantidad: {cantidad}")
    print(f"   Reference: {reference}")
    print(f"   Productiva: {es_productiva}")
    
    # Check for successful transaction
    success_results = ["ExitosaAprobada", "APPROVED", "SUCCESS", "Exitosa"]
    
    if resultado in success_results:
        print(f"✅ Transaction approved!")
        
        # Extract user_id from reference (format: GPU-{user_id}-{random})
        # Reference example: GPU-89fb0979-6e89-4286-aa99-d01565441c3c-eab2ef5b
        user_id = None
        if reference and reference.startswith("GPU-"):
            # Remove prefix
            ref_content = reference[4:] # Remove "GPU-"
            # Check if it has the random suffix (last 9 chars: -xxxxxxxx)
            if len(ref_content) > 36: # UUID is 36 chars
                user_id = ref_content[:36]
            else:
                user_id = ref_content
        
        # Calculate amount in cents for matching
        # Ensure monto is treated as float first (Wompi might send string)
        try:
            monto_float = float(monto)
            amount_cents = int(monto_float * 100)
        except (ValueError, TypeError):
            print(f"❌ Error converting amount: {monto}")
            amount_cents = 0
        
        # Find pack by amount
        credits_to_add = 0
        pack_name = "Credits"
        
        for pack in CREDIT_PACKS:
            pack_amount = int(pack["price_usd"] * 100)
            # Allow some variance in amount matching
            if abs(pack_amount - amount_cents) < 100:
                credits_to_add = pack["credits"]
                pack_name = pack["name"]
                break
        
        print(f"   User ID: {user_id}, Credits to add: {credits_to_add}")
        
        if user_id and credits_to_add > 0:
            try:
                billing = BillingService(db)
                # First get the wallet for this user
                wallet = billing.get_wallet(user_id)
                if not wallet:
                    wallet = billing.create_wallet(user_id)
                
                # Now add credits using wallet_id
                billing.add_credits(
                    wallet_id=wallet.id,
                    amount=Decimal(str(credits_to_add)),
                    description=f"Wompi payment - {pack_name}"
                )
                print(f"💰 Credited ${credits_to_add} hours to user {user_id}")
                return {"status": "success", "credited": credits_to_add, "user_id": user_id}
            except Exception as e:
                print(f"❌ Error adding credits: {e}")
                return {"status": "error", "message": str(e)}
        else:
            print(f"⚠️ Could not process: user_id={user_id}, credits={credits_to_add}")
            return {"status": "incomplete", "user_id": user_id, "credits": credits_to_add}
    else:
        print(f"ℹ️ Non-approved result: {resultado}")
        return {"status": "ignored", "result": resultado}


# ═══════════════════════════════════════════════════════════════════════════════
# PACKS ENDPOINT (Public info)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/packs")
def get_packs():
    """Get available credit packs for purchase."""
    return {
        "packs": CREDIT_PACKS,
        "currency": "USD",
        "country": "El Salvador"
    }
