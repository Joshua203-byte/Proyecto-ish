"""
Payments API endpoints.
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from decimal import Decimal
import logging
import json

from app.api.deps import get_db
from app.services.billing import BillingService
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def wompi_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook for Wompi payment notifications.
    Wompi sends: Monto, IdTransaccion, ResultadoTransaccion, EnlacePago, etc.
    """
    try:
        data = await request.json()
        print(f"💰 WOMPI WEBHOOK RECEIVED: {json.dumps(data, indent=2, default=str)}")
        
        # Wompi uses PascalCase field names
        # ResultadoTransaccion can be: "ExitosaAprobada", "Rechazada", etc.
        resultado = data.get('ResultadoTransaccion') or data.get('resultadoTransaccion') or data.get('estado') or ''
        
        print(f"📊 Transaction result: {resultado}")
        
        # Check for success
        success_results = ["ExitosaAprobada", "Exitosa", "Aprobada", "aprobada", "success", "approved"]
        if resultado not in success_results:
            print(f"⏭️ Ignoring non-success result: {resultado}")
            return {"status": "ignored", "reason": f"Result is {resultado}"}

        # Get amount - Wompi uses "Monto" (capital M)
        monto = data.get('Monto') or data.get('monto') or 0
        amount_float = float(monto)
        
        # Get transaction ID
        transaction_id = data.get('IdTransaccion') or data.get('idTransaccion') or 'unknown'
        
        # Get EnlacePago info if available
        enlace_pago = data.get('EnlacePago') or {}
        enlace_id = enlace_pago.get('IdentificadorEnlaceComercio') or data.get('identificadorEnlaceComercio') or 'unknown'
        
        print(f"💵 Amount: ${amount_float}, TransactionID: {transaction_id}, EnlaceID: {enlace_id}")
        
        if amount_float <= 0:
            print("⚠️ Amount is 0 or negative, skipping")
            return {"status": "ignored", "reason": "Amount is 0"}
        
        # For this MVP/Demo, credit the first user
        user = db.query(User).first()
        if not user:
            print("❌ No user found in database!")
            return {"status": "error", "message": "No user found"}
        
        print(f"👤 Found user: {user.email}")

        billing = BillingService(db)
        
        # Get or create wallet
        wallet = billing.get_wallet(user.id)
        if not wallet:
            wallet = billing.create_wallet(user.id)
            print(f"🆕 Created new wallet for user")
        
        print(f"💳 Wallet ID: {wallet.id}, Current balance: {wallet.balance}")
        
        # Check for duplicate transaction
        from app.models.transaction import Transaction
        existing = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id,
            Transaction.description.contains(transaction_id)
        ).first()
        
        if existing:
            print(f"⚠️ Transaction {transaction_id} already processed")
            return {"status": "already_processed", "message": "Transaction already credited"}
        
        # Add credits
        billing.add_credits(
            wallet_id=wallet.id,
            amount=Decimal(str(amount_float)),
            description=f"Wompi Payment TX:{transaction_id}"
        )
        
        # Refresh wallet to get new balance
        db.refresh(wallet)
        
        print(f"✅ SUCCESS! Credited ${amount_float} to user {user.email}")
        print(f"💰 New balance: {wallet.balance}")
        
        return {"status": "success", "credited": amount_float, "new_balance": str(wallet.balance)}

    except Exception as e:
        import traceback
        print(f"❌ Webhook Error: {e}")
        print(traceback.format_exc())
        # Return 200 to stop Wompi from retrying endlessly on internal code errors
        return {"status": "error", "message": str(e)}


@router.get("/test-webhook")
async def test_webhook_endpoint(db: Session = Depends(get_db)):
    """
    Test endpoint to simulate a successful payment webhook.
    Use this to verify the webhook logic works.
    """
    # Simulate a $5 payment
    user = db.query(User).first()
    if not user:
        return {"error": "No user found"}
    
    billing = BillingService(db)
    wallet = billing.get_wallet(user.id)
    if not wallet:
        wallet = billing.create_wallet(user.id)
    
    old_balance = wallet.balance
    
    billing.add_credits(
        wallet_id=wallet.id,
        amount=Decimal("5.00"),
        description="Test payment webhook"
    )
    
    db.refresh(wallet)
    
    return {
        "status": "success",
        "user": user.email,
        "old_balance": str(old_balance),
        "new_balance": str(wallet.balance),
        "credited": 5.00
    }


@router.post("/confirm")
async def confirm_payment(request: Request, db: Session = Depends(get_db)):
    """
    Frontend calls this when user returns from Wompi with payment=success.
    Uses the URL parameters (monto, idTransaccion, etc.) to credit the user.
    This bypasses the webhook dependency entirely.
    """
    try:
        data = await request.json()
        print(f"💳 PAYMENT CONFIRM REQUEST: {json.dumps(data, indent=2, default=str)}")
        
        # Extract parameters from frontend (from URL query params)
        monto = float(data.get('monto') or 0)
        transaction_id = data.get('idTransaccion') or data.get('transactionId') or 'unknown'
        enlace_id = data.get('idEnlace') or data.get('identificadorEnlaceComercio') or 'unknown'
        
        if monto <= 0:
            return {"status": "error", "message": "Invalid amount"}
        
        # Get current user (for demo, use first user)
        user = db.query(User).first()
        if not user:
            return {"status": "error", "message": "No user found"}
        
        billing = BillingService(db)
        wallet = billing.get_wallet(user.id)
        if not wallet:
            wallet = billing.create_wallet(user.id)
        
        # Check if this transaction was already processed (prevent duplicates)
        # Simple check: look for recent transaction with same description
        from app.models.transaction import Transaction
        existing = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id,
            Transaction.description.contains(transaction_id)
        ).first()
        
        if existing:
            print(f"⚠️ Transaction {transaction_id} already processed")
            db.refresh(wallet)
            return {
                "status": "already_processed",
                "message": "Payment already credited",
                "balance": str(wallet.balance)
            }
        
        old_balance = wallet.balance
        
        # Credit the amount
        billing.add_credits(
            wallet_id=wallet.id,
            amount=Decimal(str(monto)),
            description=f"Wompi Payment TX:{transaction_id}"
        )
        
        db.refresh(wallet)
        
        print(f"✅ PAYMENT CONFIRMED! Credited ${monto} to {user.email}")
        print(f"💰 Balance: {old_balance} → {wallet.balance}")
        
        return {
            "status": "success",
            "credited": monto,
            "old_balance": str(old_balance),
            "new_balance": str(wallet.balance)
        }
        
    except Exception as e:
        import traceback
        print(f"❌ Confirm Error: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

