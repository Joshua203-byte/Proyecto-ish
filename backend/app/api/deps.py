"""
API dependencies for authentication and database sessions.
"""
from typing import Generator
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import decode_access_token, verify_worker_secret


# HTTP Bearer scheme for JWT
security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.
    MOCKED FOR GUEST MODE: Always returns a default guest user.
    """
    # Simply return a persistent guest user
    # Try to find existing guest user or create one
    guest_email = "guest@gpu-cloud.local"
    user = db.query(User).filter(User.email == guest_email).first()
    
    if not user:
        from app.utils.security import hash_password
        user = User(
            email=guest_email,
            hashed_password=hash_password("guest123"),
            full_name="Guest User",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Ensure guest has a wallet with credits
    from app.models.wallet import Wallet
    if not user.wallet:
        # Create new wallet with 1000 credits
        wallet = Wallet(user_id=user.id, balance=1000.0)
        db.add(wallet)
        db.commit()
    elif user.wallet.balance < 1.0:
        # Top up if empty
        user.wallet.balance = 1000.0
        db.commit()
        
    return user


def verify_worker(worker_secret: str) -> bool:
    """Verify worker authentication for webhooks."""
    if not verify_worker_secret(worker_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid worker secret",
        )
    return True
