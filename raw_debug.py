from sqlalchemy import create_engine, text
import os

db_path = "sql_app.db"
if not os.path.exists(db_path):
    print("DB not found")
    exit(1)

engine = create_engine(f"sqlite:///{db_path}")

with engine.connect() as conn:
    print("--- Inspecting Users ---")
    try:
        result = conn.execute(text("SELECT id, email, role FROM users WHERE email='abraham@gmail.com'"))
        user = result.fetchone()
        if user:
            print(f"Found User: ID={user.id}, Email={user.email}, Role={user.role}")
            user_id = user.id
            
            print("--- Inspecting Requests for User ---")
            try:
                # Check column names first
                columns = conn.execute(text("PRAGMA table_info(requests)"))
                print("Requests Table Columns:")
                for col in columns:
                    print(col)

                reqs = conn.execute(text(f"SELECT id, user_id, status FROM requests WHERE user_id={user_id}"))
                reqs_list = list(reqs)
                print(f"Total Requests found: {len(reqs_list)}")
                for r in reqs_list:
                    print(f"Req ID: {r.id}, Status: {r.status}")
            except Exception as e:
                print(f"Error querying requests: {e}")
        else:
            print("User abraham@gmail.com not found")
    except Exception as e:
        print(f"Error querying users: {e}")
