from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Request
import os

db_path = "sql_app.db"
if not os.path.exists(db_path):
    print(f"Database file {db_path} not found!")
else:
    print(f"Database file found at {os.path.abspath(db_path)}")

engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

inspector = inspect(engine)
print("Tables:", inspector.get_table_names())

if "requests" in inspector.get_table_names():
    requests = db.query(Request).all()
    print(f"Total Requests in DB: {len(requests)}")
    for r in requests:
        print(f"ID: {r.id}, UserID: {r.user_id}, Status: {r.status}")
else:
    print("Requests table does not exist!")

users = db.query(User).all()
print(f"Total Users: {len(users)}")
for u in users:
    print(f"ID: {u.id}, Email: {u.email}")

db.close()
