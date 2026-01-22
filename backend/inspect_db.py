import sqlite3
import pandas as pd

def inspect_db():
    conn = sqlite3.connect('C:/Users/HOME/OneDrive/Desktop/Machine learning de ISH/home-gpu-cloud/backend/homegpu_dev.db')
    
    # List all tables
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print("Tables in DB:")
    print(tables)
    
    for table in tables['name']:
        print(f"\n--- Data from table: {table} ---")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table};", conn)
            print(df)
        except Exception as e:
            print(f"Error reading table {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    inspect_db()
