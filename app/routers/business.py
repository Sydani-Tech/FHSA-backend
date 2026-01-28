from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, schemas, auth
from ..database import SessionLocal

router = APIRouter(
    prefix="/api",
    tags=["Business"]
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Assets Retrieval (Public/Business)
@router.get("/assets", response_model=List[schemas.Asset])
def list_assets(location: Optional[str] = None, type: Optional[str] = None, search: Optional[str] = None,  db: Session = Depends(get_db)):
    return crud.get_assets(db, location=location, type=type)

@router.get("/assets/{asset_id}", response_model=schemas.Asset)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = crud.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

# Booking Management (Business)
@router.get("/bookings", response_model=List[schemas.Booking])
def list_bookings(current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    filter_user_id = current_user.id if current_user.role != "admin" else None
    return crud.get_bookings(db, user_id=filter_user_id)

@router.post("/bookings", response_model=schemas.Booking)
def create_booking(booking_data: schemas.BookingCreate, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    return crud.create_booking(db, booking_data, current_user.id)

@router.get("/bookings/{booking_id}", response_model=schemas.Booking)
def get_booking(booking_id: int, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user.role != "admin" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this booking")
    return booking

@router.post("/bookings/{booking_id}/cancel", response_model=schemas.Booking)
def cancel_booking(booking_id: int, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    return crud.cancel_booking(db, booking_id, current_user.id)

@router.post("/bookings/{booking_id}/pay", response_model=schemas.Payment)
def process_payment(booking_id: int, payment: schemas.PaymentCreate, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    return crud.create_payment(db, booking_id, payment, current_user.id)

@router.get("/bookings/{booking_id}/receipt")
def get_receipt(booking_id: int, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    # Simple Receipt Generation
    booking = crud.get_booking(db, booking_id)
    if not booking or (booking.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if not booking.payments:
        raise HTTPException(status_code=400, detail="No payment record found")
        
    payment = booking.payments[0]
    
    receipt_text = f"""
    --- OFFICIAL RECEIPT ---
    Reference: {payment.reference}
    Date: {payment.created_at.strftime("%Y-%m-%d %H:%M:%S")}
    
    Payer: {current_user.business_name or current_user.email}
    Booking Ref: {booking.reference_code}
    Asset: {booking.asset.name if booking.asset else 'Unknown Asset'}
    
    Amount: {payment.amount} {payment.currency}
    Status: PAID
    
    Thank you for your business.
    ------------------------
    """
    return {"content": receipt_text}

@router.post("/bookings/{booking_id}/feedback", response_model=schemas.Feedback)
def submit_feedback(booking_id: int, feedback: schemas.FeedbackCreate, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    return crud.create_feedback(db, booking_id, feedback, current_user.id)

@router.get("/user/dashboard", response_model=schemas.UserDashboardStats)
def get_user_dashboard_stats(current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    return crud.get_user_dashboard_stats(db, current_user.id)
