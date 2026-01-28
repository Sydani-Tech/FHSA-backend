from sqlalchemy import create_engine, text
import os

db_path = "fhsa.db"
out_file = "debug_output_fhsa.txt"

with open(out_file, "w") as f:
    if not os.path.exists(db_path):
        f.write(f"DB {db_path} not found\n")
        exit(1)

    f.write(f"DB Found at {os.path.abspath(db_path)}\n")
    try:
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            f.write("--- Inspecting Users ---\n")
            try:
                # Get all users to see what comes back
                users = conn.execute(text("SELECT id, email, role FROM users"))
                f.write("All Users:\n")
                target_user_id = None
                for u in users:
                    f.write(f"  ID={u.id}, Email={u.email}, Role={u.role}\n")
                    if u.email == 'abraham@gmail.com':
                        target_user_id = u.id

                if target_user_id:
                    f.write(f"Found Target User ID: {target_user_id}\n")
                    f.write("--- Inspecting Requests for User ---\n")
                    reqs = conn.execute(text(f"SELECT id, user_id, status FROM requests WHERE user_id={target_user_id}"))
                    reqs_list = list(reqs)
                    f.write(f"Total Requests found: {len(reqs_list)}\n")
                    for r in reqs_list:
                        f.write(f"Req ID: {r.id}, Status: '{r.status}'\n")
                    
                    # Check if status case matches what we expect
                    pending_count = 0
                    for r in reqs_list:
                        if r.status == 'pending':
                            pending_count += 1
                        else:
                            f.write(f"  Non-pending status: '{r.status}'\n")
                    f.write(f"Counted 'pending': {pending_count}\n")
                else:
                    f.write("User abraham@gmail.com not found in list.\n")

            except Exception as e:
                f.write(f"Error querying: {e}\n")
    except Exception as e:
        f.write(f"Engine/Connect Error: {e}\n")
