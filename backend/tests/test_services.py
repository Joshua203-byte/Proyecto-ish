"""
Tests for service layer - billing and security.
"""
import pytest
from datetime import datetime, timedelta
import uuid

from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.services.billing import BillingService
from app.models import Wallet, Transaction


class TestPasswordHashing:
    """Tests for password hashing utilities."""
    
    def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
    
    def test_wrong_password_fails(self):
        """Test verification fails with wrong password."""
        hashed = get_password_hash("CorrectPassword123!")
        
        assert not verify_password("WrongPassword123!", hashed)
    
    def test_same_password_different_hashes(self):
        """Test same password produces different hashes (salt)."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Tests for JWT token creation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are fairly long
    
    def test_token_with_expiry(self):
        """Test token with custom expiry."""
        token = create_access_token(
            data={"sub": "test"},
            expires_delta=timedelta(hours=24)
        )
        
        assert token is not None


class TestBillingService:
    """Tests for billing service logic."""
    
    def test_get_wallet(self, db, test_user):
        """Test getting user wallet."""
        billing = BillingService(db)
        wallet = billing.get_wallet(test_user.id)
        
        assert wallet is not None
        assert float(wallet.balance) == 100.00
    
    def test_add_credits(self, db, test_user):
        """Test adding credits to wallet."""
        billing = BillingService(db)
        wallet = billing.get_wallet(test_user.id)
        
        from decimal import Decimal
        initial_balance = float(wallet.balance)
        top_up_amount = Decimal("50.00")
        
        transaction = billing.add_credits(
            wallet_id=wallet.id,
            amount=top_up_amount,
            description="Test top-up"
        )
        
        db.refresh(wallet)
        assert float(wallet.balance) == initial_balance + float(top_up_amount)
        assert transaction.type == "credit"
    
    def test_can_start_job(self, db, test_user):
        """Test checking if user can start a job."""
        billing = BillingService(db)
        
        # Has 100 credits from fixture, minimum is 10
        assert billing.can_start_job(test_user.id) is True


class TestTransactionRecords:
    """Tests for transaction record creation."""
    
    def test_topup_creates_transaction(self, auth_client, test_user, db):
        """Test that top-up creates a transaction record."""
        auth_client.post(
            "/api/v1/wallet/topup",
            json={"amount": 50.00}
        )
        
        transactions = db.query(Transaction).all()
        assert len(transactions) >= 1
        
        tx = transactions[-1]
        assert tx.type == "credit"
        assert float(tx.amount) == 50.00
