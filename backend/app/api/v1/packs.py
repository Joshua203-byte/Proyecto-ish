"""
Credit Packs API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

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


import httpx

@router.post("/{pack_id}/checkout")
async def create_checkout_session(pack_id: str, db: Session = Depends(get_db)):
    """
    Generate a payment link for a specific credit pack using Wompi SV API.
    """
    try:
        # Find pack
        selected_pack = None
        for pack in CREDIT_PACKS:
            if pack["id"] == pack_id:
                selected_pack = pack
                break
                
        if not selected_pack:
            return {"detail": "Pack not found"}, 404

        # 1. Get Wompi SV Auth Token
        async with httpx.AsyncClient(timeout=30.0) as client:
            auth_response = await client.post(
                "https://id.wompi.sv/connect/token",
                data={
                    "grant_type": "client_credentials",
                    "audience": "wompi_api",
                    "client_id": settings.WOMPI_SV_APP_ID,
                    "client_secret": settings.WOMPI_SV_API_SECRET
                }
            )
            
            if auth_response.status_code != 200:
                print(f"WOMPI AUTH ERROR: {auth_response.text}")
                raise HTTPException(status_code=500, detail=f"Global Payment Auth Failed: {auth_response.text}")
                
            token = auth_response.json().get("access_token")

            # 2. Create Payment Link
            link_payload = {
                "identificadorEnlaceComercio": f"HG-{uuid.uuid4().hex[:8]}",
                "monto": selected_pack["price_usd"],
                "nombreProducto": f"HomeGPU - {selected_pack['name']}",
                "descripcionProducto": selected_pack['description'],
                "configuracion": {
                    "urlRedirect": f"{settings.FRONTEND_URL}/dashboard/wallet?payment=success",
                    "urlWebhook": f"{settings.BACKEND_URL}/api/v1/payments/webhook",
                    "esMontoEditable": False,
                    "esCantidadEditable": False,
                    "emailsNotificacion": "pagos@homegpu.cloud"
                }
            }
            
            print(f"DEBUG WOMPI PAYLOAD: {link_payload}")
            
            link_response = await client.post(
                "https://api.wompi.sv/EnlacePago",
                json=link_payload,
                headers={"Authorization": f"Bearer {token}"}
            )

            if link_response.status_code != 200:
                print(f"WOMPI LINK ERROR: {link_response.text}")
                # Use 400 for bad request from Wompi
                raise HTTPException(status_code=400, detail=f"Wompi Link Error: {link_response.text}")

            # Get the URL from the response
            data = link_response.json()
            print(f"DEBUG WOMPI RESPONSE: {data}")  # LEAVE THIS FOR DEBUGGING
            
            payment_url = data.get("urlEnlace") or data.get("url") or data.get("enlace")
            
            # Fallback: Construct URL if we have ID but no URL
            if not payment_url and data.get("idEnlace"):
                payment_url = f"https://lk.wompi.sv/{data.get('idEnlace')}"
            
            if not payment_url:
                import json
                # FORCE ERROR WITH JSON PAYLOAD VISIBLE TO USER
                raise HTTPException(status_code=400, detail=f"DEBUG INFO: {json.dumps(data)}")
                
            return {"payment_url": payment_url}

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        error_details = f"{type(e).__name__}: {str(e)}"
        print(f"ERROR generating checkout link: {error_details}")
        print(traceback.format_exc())
        # Return strict JSONResponse for 500 if needed, or just raise HTTPException
        raise HTTPException(status_code=500, detail=f"Payment Error: {error_details}")
