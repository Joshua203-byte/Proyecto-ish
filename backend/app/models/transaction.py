"""
Transaction model for immutable financial audit log.
"""
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TransactionType:
    """Transaction type constants."""
    CREDIT = "credit"               # User added funds
    DEBIT = "debit"                 # GPU usage charge
    REFUND = "refund"               # System error refund
    RESERVATION = "reservation"     # Reserve credits for active job
    RELEASE = "release"             # Release reserved credits


class Transaction(Base):
    """
    Immutable financial transaction record.
    
    Once created, transactions are NEVER modified or deleted.
    This provides a complete audit trail for all wallet operations.
    """
    
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Transaction type
    type = Column(String(50), nullable=False, index=True)
    
    # Amount (positive for credits, negative for debits)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    
    # Balance snapshot for audit
    balance_before = Column(Numeric(precision=10, scale=2), nullable=False)
    balance_after = Column(Numeric(precision=10, scale=2), nullable=False)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Timestamp (immutable)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
    job = relationship("Job", back_populates="transactions")
    
    @property
    def is_debit(self) -> bool:
        """Check if this is a debit transaction."""
        return self.amount < 0
    
    @property
    def is_credit(self) -> bool:
        """Check if this is a credit transaction."""
        return self.amount > 0
    
    def __repr__(self) -> str:
        return f"<Transaction {self.id} type={self.type} amount={self.amount}>"
