import sqlite3
import json

try:
    try:
        db_path = 'backend/fhsa.db'
        import os
        if not os.path.exists(db_path):
             # Try local if running from backend dir
             if os.path.exists('fhsa.db'):
                 db_path = 'fhsa.db'
             else:
                 print(f"DB not found at {db_path} or fhsa.db")
                 
        conn = sqlite3.connect(db_path)
    except Exception as e:
        print(f"Could not connect to fhsa.db: {e}")
        # Try finding where it might be
        import os
        print(f"Current dir: {os.getcwd()}")
        print(f"Files: {os.listdir('.')}")
        exit(1)

    cursor = conn.cursor()
    
    print("--- ASSETS COLUMNS ---")
    cursor.execute("PRAGMA table_info(assets)")
    columns = [row[1] for row in cursor.fetchall()]
    print(columns)
    if 'total_quantity' in columns:
        print("total_quantity EXISTS")
    else:
        print("total_quantity MISSING")

    print("\n--- BOOKINGS DATA ---")
    cursor.execute("SELECT id, dates FROM bookings LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Dates Type: {type(row[1])}, Value: {row[1]}")
    
    if not rows:
        print("No bookings found invalidating date testing logic, but schema check is useful.")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn: conn.close()
