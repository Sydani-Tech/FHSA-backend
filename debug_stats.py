from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Request
from app.database import SQLALCHEMY_DATABASE_URL

# Adjust the database URL if needed (e.g. if it's relative)
# Assuming sqlite:///./sql_app.db
engine = create_engine("sqlite:///./sql_app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

email = "abraham@gmail.com"
user = db.query(User).filter(User.email == email).first()

if not user:
    print(f"User {email} not found")
else:
    print(f"User ID: {user.id}")
    requests = db.query(Request).filter(Request.user_id == user.id).all()
    print(f"Total Requests: {len(requests)}")
    for req in requests:
        print(f"Request ID: {req.id}, Status: '{req.status}'")

    # Double check stats counts
    pending = db.query(Request).filter(Request.user_id == user.id, Request.status == "pending").count()
    approved = db.query(Request).filter(Request.user_id == user.id, Request.status == "approved").count()
    completed = db.query(Request).filter(Request.user_id == user.id, Request.status == "completed").count()
    print(f"Stats -> Pending: {pending}, Approved: {approved}, Completed: {completed}")

db.close()
