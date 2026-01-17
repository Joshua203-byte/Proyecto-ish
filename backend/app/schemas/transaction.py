"""Transaction Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel


class TransactionRead(BaseModel):
    """Schema for transaction response."""
    id: UUID
    wallet_id: UUID
    job_id: UUID | None
    type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionList(BaseModel):
    """Schema for paginated transaction list."""
    items: list[TransactionRead]
    total: int
    page: int
    page_size: int
