"""
Wallet API endpoints.
"""
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.schemas.wallet import WalletRead, WalletTopUp
from app.schemas.transaction import TransactionRead, TransactionList
from app.services.billing import BillingService


router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/", response_model=WalletRead)
def get_wallet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's wallet."""
    billing = BillingService(db)
    wallet = billing.get_wallet(current_user.id)
    
    if not wallet:
        # Create wallet if it doesn't exist
        wallet = billing.create_wallet(current_user.id)
    
    return wallet


@router.post("/topup", response_model=TransactionRead)
def add_credits(
    topup: WalletTopUp,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add credits to wallet.
    
    Note: In production, this would integrate with a payment gateway.
    For MVP, we simulate successful payment.
    """
    billing = BillingService(db)
    wallet = billing.get_wallet(current_user.id)
    
    if not wallet:
        wallet = billing.create_wallet(current_user.id)
    
    description = f"Credit top-up"
    if topup.payment_reference:
        description += f" (ref: {topup.payment_reference})"
    
    transaction = billing.add_credits(
        wallet_id=wallet.id,
        amount=topup.amount,
        description=description
    )
    
    return transaction


@router.get("/transactions", response_model=TransactionList)
def list_transactions(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List wallet transactions."""
    billing = BillingService(db)
    wallet = billing.get_wallet(current_user.id)
    
    if not wallet:
        return TransactionList(items=[], total=0, page=page, page_size=page_size)
    
    # Query transactions
    query = db.query(Transaction).filter(Transaction.wallet_id == wallet.id)
    total = query.count()
    
    transactions = (
        query
        .order_by(Transaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return TransactionList(
        items=transactions,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get wallet balance summary."""
    billing = BillingService(db)
    wallet = billing.get_wallet(current_user.id)
    
    if not wallet:
        return {
            "balance": Decimal("0.00"),
            "reserved": Decimal("0.00"),
            "available": Decimal("0.00")
        }
    
    return {
        "balance": wallet.balance,
        "reserved": wallet.reserved,
        "available": wallet.available_balance
    }
