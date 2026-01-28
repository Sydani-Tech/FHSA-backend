from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="business_user", nullable=False) # business_user, admin
    status = Column(String, default="pending", nullable=False) # pending, approved, restricted
    login_count = Column(Integer, default=0, nullable=False)
    
    # Personal Info
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # Business Profile
    business_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    production_focus = Column(String, nullable=True)
    certifications = Column(JSON, nullable=True) # List of strings
    needs = Column(JSON, nullable=True) # List of strings
    
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    # assets = relationship("Asset", back_populates="owner") # If needed

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    specs = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True) # List of URLs
    cost = Column(String, nullable=False) # Storing as string to match schema decimal/string behavior easily
    duration_options = Column(JSON, nullable=True)
    availability = Column(JSON, nullable=True)
    total_quantity = Column(Integer, default=1, nullable=False)
    active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Audit fields
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_modified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", foreign_keys=[owner_id]) # explicit relationship if needed
    last_modified_by = relationship("User", foreign_keys=[last_modified_by_id])
    
    bookings = relationship("Booking", back_populates="asset")
    feedbacks = relationship("Feedback", back_populates="asset")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    reference_code = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Booking Details
    dates = Column(JSON, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    purpose = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Financials
    total_amount = Column(String, nullable=True) # Calculated based on duration/cost
    payment_status = Column(String, default="unpaid", nullable=False) # unpaid, paid, refunded
    
    # Status Workflow
    status = Column(String, default="pending", nullable=False) 
    # pending -> awaiting_payment -> paid -> in_possession -> returned 
    # (plus overdue, cancelled)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bookings")
    asset = relationship("Asset", back_populates="bookings")
    audits = relationship("BookingAudit", back_populates="booking", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="booking")
    feedback = relationship("Feedback", back_populates="booking", uselist=False)

class BookingAudit(Base):
    __tablename__ = "booking_audits"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # User who performed the action
    
    action = Column(String, nullable=False) # Created, Approved, Paid, Helper Text...
    details = Column(JSON, nullable=True) # { "from_status": "pending", "to_status": "awaiting_payment" }
    timestamp = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="audits")
    performed_by = relationship("User")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    reference = Column(String, unique=True, index=True, nullable=False) # Payment Ref
    
    amount = Column(String, nullable=False)
    currency = Column(String, default="NGN")
    status = Column(String, default="success") # success, failed
    method = Column(String, nullable=True) # card, transfer
    
    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="payments")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    rating = Column(Integer, nullable=False) # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="feedback")
    asset = relationship("Asset", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
