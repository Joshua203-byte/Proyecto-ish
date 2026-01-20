import sqlite3
import os

def migrate():
    db_path = "homegpu_dev.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Nothing to migrate.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "is_superuser" not in columns:
            print("Adding is_superuser column to users table...")
            # Add column with default 0 (False)
            cursor.execute("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT 0 NOT NULL")
            conn.commit()
            print("✅ Migration successful: is_superuser column added.")
        else:
            print("Values 'is_superuser' already exists. Skipping.")
            
        conn.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
