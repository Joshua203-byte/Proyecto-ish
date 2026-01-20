from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Job, Wallet, Transaction
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency to check for superuser
def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    """Get global platform statistics."""
    total_users = db.query(User).count()
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.status == "running").count()
    
    # Calculate total revenue from 'credit' transactions (funds added)
    total_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "credit"
    ).scalar() or 0.0
    
    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_revenue": float(total_revenue)
    }

@router.get("/users")
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    """List all registered users."""
    users = db.query(User).offset(skip).limit(limit).all()
    
    # Enrich with wallet balance
    result = []
    for user in users:
        wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "balance": float(wallet.balance) if wallet else 0.0
        })
        
    return result
