import sqlite3
import os

db_path = 'backend/fhsa.db'
if not os.path.exists(db_path) and os.path.exists('fhsa.db'):
    db_path = 'fhsa.db'

print(f"Connecting to {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check if column exists first to be sure
    cursor.execute("PRAGMA table_info(assets)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'total_quantity' not in columns:
        print("Adding total_quantity column...")
        cursor.execute("ALTER TABLE assets ADD COLUMN total_quantity INTEGER DEFAULT 1 NOT NULL")
        conn.commit()
        print("Column added successfully.")
    else:
        print("total_quantity already exists.")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn: conn.close()
