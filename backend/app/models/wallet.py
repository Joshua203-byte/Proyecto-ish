"""
Wallet model for credit management.
"""
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.config import settings
from app.utils.types import GUID


class Wallet(Base):
    """
    User wallet with optimistic locking for atomic balance operations.
    
    The 'version' field prevents race conditions in concurrent debit operations.
    Each update must increment the version; if versions don't match, the
    operation is retried.
    """
    
    __tablename__ = "wallets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(), 
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Balance: 2 decimal places, max 999,999.99
    balance = Column(
        Numeric(precision=10, scale=2), 
        default=Decimal("0.00"), 
        nullable=False
    )
    
    # Reserved: Credits reserved for active jobs (not available for new jobs)
    reserved = Column(
        Numeric(precision=10, scale=2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    # Optimistic locking version
    version = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")

    @property
    def available_balance(self) -> Decimal:
        """Get balance available for spending (total minus reserved)."""
        return self.balance - self.reserved
    
    def can_start_job(self, minimum_balance: Decimal) -> bool:
        """Check if wallet has enough available balance to start a job."""
        return self.available_balance >= minimum_balance
    
    def __repr__(self) -> str:
        return f"<Wallet user_id={self.user_id} balance={self.balance}>"
