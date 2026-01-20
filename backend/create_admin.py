import sys
import os

# Add current directory to python path so we can import app modules
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.user import User
from app.models.wallet import Wallet
from app.utils.security import hash_password

def create_admin():
    db = SessionLocal()
    try:
        email = "admin@homegpu.com"
        password = "admin123"
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"User {email} already exists. Promoting to superuser...")
            user.is_superuser = True
            db.commit()
        else:
            print(f"Creating new superuser {email}...")
            user = User(
                email=email,
                full_name="System Administrator",
                hashed_password=hash_password(password),
                is_superuser=True,
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create wallet
            wallet = Wallet(user_id=user.id)
            db.add(wallet)
            db.commit()
            
        print("✅ Admin user ready!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
