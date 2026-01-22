import sqlite3

def check_balances():
    conn = sqlite3.connect('C:/Users/HOME/OneDrive/Desktop/Machine learning de ISH/home-gpu-cloud/backend/homegpu_dev.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT u.email, w.balance FROM users u JOIN wallets w ON u.id = w.user_id")
    results = cursor.fetchall()
    
    print("User Balances:")
    for email, balance in results:
        print(f"User: {email} | Balance: {balance}")
        
    conn.close()

if __name__ == "__main__":
    check_balances()
