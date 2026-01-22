from app.database import SessionLocal
from app.models.user import User
from app.models.wallet import Wallet
from decimal import Decimal

def add_credits(email: str, amount: float):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ Error: User with email {email} not found.")
            return
        
        wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
        if not wallet:
            print(f"❌ Error: Wallet for user {email} not found. Creating one...")
            wallet = Wallet(user_id=user.id, balance=Decimal(str(amount)))
            db.add(wallet)
        else:
            wallet.balance += Decimal(str(amount))
            print(f"✅ Added {amount} credits to {email}.")
            print(f"💰 New balance: {wallet.balance}")
            
        db.commit()
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_credits("hammy.garcilazo@gmail.com", 1000.0)
