"""
Billing service for credit management.
Handles atomic wallet operations with optimistic locking.
"""
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType
from app.models.job import Job
from app.config import settings


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits."""
    pass


class OptimisticLockError(Exception):
    """Raised when concurrent update detected."""
    pass


class BillingService:
    """Service for wallet and billing operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_wallet(self, user_id: UUID) -> Wallet:
        """Get user's wallet."""
        return self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
    
    def create_wallet(self, user_id: UUID) -> Wallet:
        """Create wallet for new user."""
        wallet = Wallet(user_id=user_id)
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet
    
    def add_credits(
        self,
        wallet_id: UUID,
        amount: Decimal,
        description: str = "Credit top-up"
    ) -> Transaction:
        """
        Add credits to wallet (top-up).
        Returns the created transaction.
        """
        wallet = self.db.query(Wallet).filter(Wallet.id == wallet_id).with_for_update().first()
        if not wallet:
            raise ValueError("Wallet not found")
        
        balance_before = wallet.balance
        wallet.balance += amount
        wallet.version += 1
        
        transaction = Transaction(
            wallet_id=wallet_id,
            type=TransactionType.CREDIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            description=description
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction
    
    def debit_for_job(
        self,
        wallet_id: UUID,
        job_id: UUID,
        amount: Decimal,
        description: str = "GPU usage charge"
    ) -> Transaction:
        """
        Debit credits for job usage.
        Uses optimistic locking to prevent race conditions.
        """
        wallet = self.db.query(Wallet).filter(Wallet.id == wallet_id).with_for_update().first()
        if not wallet:
            raise ValueError("Wallet not found")
        
        if wallet.available_balance < amount:
            raise InsufficientCreditsError(
                f"Insufficient balance: {wallet.available_balance} < {amount}"
            )
        
        balance_before = wallet.balance
        wallet.balance -= amount
        wallet.version += 1
        
        transaction = Transaction(
            wallet_id=wallet_id,
            job_id=job_id,
            type=TransactionType.DEBIT,
            amount=-amount,  # Negative for debit
            balance_before=balance_before,
            balance_after=wallet.balance,
            description=description
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction
    
    def check_and_bill(
        self,
        job_id: UUID,
        runtime_minutes: int
    ) -> tuple[bool, Decimal]:
        """
        Check if user has credits and bill for runtime.
        
        Returns:
            (should_continue, current_balance)
            should_continue is False if credits <= 0 (kill switch)
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False, Decimal("0.00")
        
        wallet = self.get_wallet(job.user_id)
        if not wallet:
            return False, Decimal("0.00")
        
        # Calculate cost for this billing period
        cost = Decimal(str(settings.CREDITS_PER_MINUTE))
        
        try:
            self.debit_for_job(
                wallet_id=wallet.id,
                job_id=job_id,
                amount=cost,
                description=f"GPU minute {runtime_minutes}"
            )
            
            # Update job total cost
            job.total_cost += cost
            job.runtime_seconds = runtime_minutes * 60
            self.db.commit()
            
            # Refresh wallet to get current balance
            self.db.refresh(wallet)
            
            # Kill switch: if balance is now zero or negative  
            if wallet.available_balance <= 0:
                return False, wallet.balance
            
            return True, wallet.balance
            
        except InsufficientCreditsError:
            return False, wallet.balance
    
    def can_start_job(self, user_id: UUID) -> bool:
        """Check if user has minimum balance to start a job."""
        wallet = self.get_wallet(user_id)
        if not wallet:
            return False
        
        minimum = Decimal(str(settings.MINIMUM_BALANCE_TO_START))
        return wallet.can_start_job(minimum)
