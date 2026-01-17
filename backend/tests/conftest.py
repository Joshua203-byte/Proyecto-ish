"""
Pytest fixtures for Home-GPU-Cloud tests.

Provides database sessions, test client, and authenticated user helpers.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.main import app
from app.database import Base, get_db
from app.models import User, Wallet
from app.utils.security import get_password_hash, create_access_token


# ─────────────────────────────────────────────────────────────────────────────────
# DATABASE FIXTURES
# ─────────────────────────────────────────────────────────────────────────────────

# In-memory SQLite for testing (fast, isolated)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────────
# USER FIXTURES
# ─────────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_user_data():
    """Default test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_user(db, test_user_data):
    """Create a test user in the database."""
    user = User(
        id=uuid.uuid4(),
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        is_active=True,
    )
    db.add(user)
    
    # Create wallet for user
    wallet = Wallet(
        id=uuid.uuid4(),
        user_id=user.id,
        balance=100.00,  # Start with credits for testing
    )
    db.add(wallet)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def test_user_token(test_user):
    """Get JWT token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(test_user_token):
    """Get authorization headers with bearer token."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def auth_client(client, auth_headers):
    """Client with authentication headers pre-set."""
    client.headers.update(auth_headers)
    return client


# ─────────────────────────────────────────────────────────────────────────────────
# ADMIN FIXTURES
# ─────────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Admin User",
        is_active=True,
        is_admin=True,
    )
    db.add(user)
    
    wallet = Wallet(
        id=uuid.uuid4(),
        user_id=user.id,
        balance=1000.00,
    )
    db.add(wallet)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def admin_token(admin_user):
    """Get JWT token for admin user."""
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def admin_headers(admin_token):
    """Get authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}


# ─────────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────────

def create_test_job(db, user, **kwargs):
    """Helper to create a job for testing."""
    from app.models import Job
    
    job = Job(
        id=uuid.uuid4(),
        user_id=user.id,
        script_name=kwargs.get("script_name", "train.py"),
        status=kwargs.get("status", "pending"),
        memory_limit=kwargs.get("memory_limit", "8g"),
        cpu_count=kwargs.get("cpu_count", 4),
        timeout_seconds=kwargs.get("timeout_seconds", 3600),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
