from sqlalchemy import create_engine, text
import os

db_path = "sql_app.db"
out_file = "debug_output.txt"

with open(out_file, "w") as f:
    if not os.path.exists(db_path):
        f.write("DB not found\n")
        exit(1)

    f.write(f"DB Found at {os.path.abspath(db_path)}\n")
    try:
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            f.write("--- Inspecting Users ---\n")
            try:
                result = conn.execute(text("SELECT id, email, role FROM users WHERE email='abraham@gmail.com'"))
                user = result.fetchone()
                if user:
                    f.write(f"Found User: ID={user.id}, Email={user.email}, Role={user.role}\n")
                    user_id = user.id
                    
                    f.write("--- Inspecting Requests for User ---\n")
                    
                    # Check column names first
                    columns = conn.execute(text("PRAGMA table_info(requests)"))
                    f.write("Requests Table Columns:\n")
                    for col in columns:
                        f.write(str(col) + "\n")

                    reqs = conn.execute(text(f"SELECT id, user_id, status FROM requests WHERE user_id={user_id}"))
                    reqs_list = list(reqs)
                    f.write(f"Total Requests found: {len(reqs_list)}\n")
                    for r in reqs_list:
                        f.write(f"Req ID: {r.id}, Status: {r.status}\n")
                else:
                    users = conn.execute(text("SELECT id, email FROM users"))
                    f.write("User abraham@gmail.com not found. Existing users:\n")
                    for u in users:
                        f.write(f"  ID={u.id}, Email={u.email}\n")
            except Exception as e:
                f.write(f"Error querying: {e}\n")
    except Exception as e:
        f.write(f"Engine/Connect Error: {e}\n")
