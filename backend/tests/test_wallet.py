"""
Tests for Wallet API endpoints.
"""
import pytest


class TestGetWallet:
    """Tests for GET /api/v1/wallet/"""
    
    def test_get_wallet_success(self, auth_client, test_user):
        """Test getting user wallet."""
        response = auth_client.get("/api/v1/wallet/")
        
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "reserved" in data
        assert float(data["balance"]) == 100.00  # From fixture
    
    def test_get_wallet_unauthorized(self, client):
        """Test wallet requires authentication."""
        response = client.get("/api/v1/wallet/")
        
        assert response.status_code == 401


class TestTopUp:
    """Tests for POST /api/v1/wallet/topup"""
    
    def test_top_up_success(self, auth_client, test_user, db):
        """Test adding credits to wallet."""
        initial_balance = 100.00
        top_up_amount = 50.00
        
        response = auth_client.post(
            "/api/v1/wallet/topup",
            json={"amount": top_up_amount}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance_after"]) == initial_balance + top_up_amount
    
    def test_top_up_negative_amount(self, auth_client):
        """Test top-up fails with negative amount."""
        response = auth_client.post(
            "/api/v1/wallet/topup",
            json={"amount": -50.00}
        )
        
        assert response.status_code == 422
    
    def test_top_up_zero_amount(self, auth_client):
        """Test top-up fails with zero amount."""
        response = auth_client.post(
            "/api/v1/wallet/topup",
            json={"amount": 0}
        )
        
        assert response.status_code == 422


class TestTransactions:
    """Tests for GET /api/v1/wallet/transactions"""
    
    def test_get_transactions_empty(self, auth_client, test_user):
        """Test getting empty transaction history."""
        response = auth_client.get("/api/v1/wallet/transactions")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_get_transactions_after_topup(self, auth_client, test_user):
        """Test transactions appear after top-up."""
        # First top-up
        auth_client.post(
            "/api/v1/wallet/topup",
            json={"amount": 25.00}
        )
        
        # Get transactions
        response = auth_client.get("/api/v1/wallet/transactions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        
        # Check transaction details
        if data["items"]:
            tx = data["items"][0]
            assert "amount" in tx
            assert "type" in tx
            assert "created_at" in tx
    
    def test_transactions_pagination(self, auth_client, test_user):
        """Test transaction pagination."""
        # Create multiple transactions
        for i in range(5):
            auth_client.post(
                "/api/v1/wallet/topup",
                json={"amount": 10.00}
            )
        
        # Get with pagination
        response = auth_client.get("/api/v1/wallet/transactions?page=1&per_page=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) <= 3
