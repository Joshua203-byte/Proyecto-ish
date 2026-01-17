#!/usr/bin/env python3
"""
Database initialization script.
Creates initial admin user and test data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from decimal import Decimal
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.wallet import Wallet
from app.utils.security import hash_password


def init_db():
    """Initialize database with tables and seed data."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@homegpu.local").first()
        
        if not admin:
            print("Creating admin user...")
            admin = User(
                email="admin@homegpu.local",
                full_name="System Admin",
                hashed_password=hash_password("admin123"),
                is_active=True,
                is_verified=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            # Create wallet with initial credits
            wallet = Wallet(
                user_id=admin.id,
                balance=Decimal("100.00")
            )
            db.add(wallet)
            db.commit()
            
            print(f"  Email: admin@homegpu.local")
            print(f"  Password: admin123")
            print(f"  Credits: 100.00")
        else:
            print("Admin user already exists")
        
        # Create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not test_user:
            print("Creating test user...")
            test_user = User(
                email="test@example.com",
                full_name="Test User",
                hashed_password=hash_password("test1234"),
                is_active=True,
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            
            # Create wallet
            wallet = Wallet(
                user_id=test_user.id,
                balance=Decimal("50.00")
            )
            db.add(wallet)
            db.commit()
            
            print(f"  Email: test@example.com")
            print(f"  Password: test1234")
            print(f"  Credits: 50.00")
        else:
            print("Test user already exists")
        
        print("\n✓ Database initialized successfully!")
        
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
