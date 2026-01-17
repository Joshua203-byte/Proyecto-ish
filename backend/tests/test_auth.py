"""
Tests for Authentication API endpoints.
"""
import pytest


class TestRegister:
    """Tests for POST /api/v1/auth/register"""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration fails with existing email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPassword123!",
                "full_name": "Duplicate User"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Test registration fails with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePassword123!",
                "full_name": "Invalid Email User"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_weak_password(self, client):
        """Test registration fails with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "123",
                "full_name": "Weak Password User"
            }
        )
        
        # Should fail validation (password too short)
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login"""
    
    def test_login_success(self, client, test_user, test_user_data):
        """Test successful login returns tokens."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user, test_user_data):
        """Test login fails with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login fails for non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )
        
        assert response.status_code == 401


class TestProfile:
    """Tests for GET /api/v1/auth/me"""
    
    def test_get_profile_success(self, auth_client, test_user):
        """Test getting current user profile."""
        response = auth_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
    
    def test_get_profile_unauthorized(self, client):
        """Test profile requires authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_get_profile_invalid_token(self, client):
        """Test profile fails with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
