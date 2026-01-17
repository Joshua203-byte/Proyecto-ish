"""Wallet Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


class WalletRead(BaseModel):
    """Schema for wallet response."""
    id: UUID
    user_id: UUID
    balance: Decimal
    reserved: Decimal
    available_balance: Decimal
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True


class WalletTopUp(BaseModel):
    """Schema for adding credits to wallet."""
    amount: Decimal = Field(..., gt=0, le=10000)
    payment_reference: str | None = Field(None, max_length=255)


class WalletDebit(BaseModel):
    """Schema for debiting wallet (internal use)."""
    amount: Decimal = Field(..., gt=0)
    job_id: UUID
    description: str | None = None
