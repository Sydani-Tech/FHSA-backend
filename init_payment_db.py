from app.database import engine, Base
from app import models

def init_payment_db():
    print("Creating payment table...")
    # This will create tables that don't exist, i.e., payments
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init_payment_db()
