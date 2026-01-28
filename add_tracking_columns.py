import sqlite3
import os

db_path = 'backend/fhsa.db'
if not os.path.exists(db_path) and os.path.exists('fhsa.db'):
    db_path = 'fhsa.db'

print(f"Connecting to {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(assets)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'updated_at' not in columns:
        print("Adding updated_at column...")
        cursor.execute("ALTER TABLE assets ADD COLUMN updated_at TIMESTAMP")
    else:
        print("updated_at already exists.")

    if 'last_modified_by_id' not in columns:
        print("Adding last_modified_by_id column...")
        cursor.execute("ALTER TABLE assets ADD COLUMN last_modified_by_id INTEGER")
    else:
        print("last_modified_by_id already exists.")

    conn.commit()
    print("Schema update complete.")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn: conn.close()
