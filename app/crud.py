from sqlalchemy.orm import Session, joinedload
from . import models, schemas
from .auth import get_password_hash
from typing import Any

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        business_name=user.business_name,
        phone=user.phone,
        location=user.location,
        production_focus=user.production_focus,
        certifications=user.certifications,
        needs=user.needs
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_status(db: Session, user_id: int, status: str):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.status = status
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_profile(db: Session, user_id: int, profile_data: schemas.UserProfileUpdate):
    db_user = get_user(db, user_id)
    if db_user:
        update_data = profile_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()

# Assets
def calculate_availability(db: Session, asset: models.Asset):
    # Calculate active bookings that reduce availability
    # Statuses that hold inventory: pending, awaiting_payment, paid, in_possession
    # We could also check date overlaps, but for simple quantity display "Available Now", 
    # we can just count un-returned, non-cancelled bookings.
    # However, future bookings shouldn't reduce "Available Now" count unless they overlap today.
    # For this fix, let's assume if it's booked (even future), it reduces "general availability" for simplicity, 
    # OR better: check overlap with TODAY.
    
    from datetime import datetime
    now = datetime.utcnow()
    
    active_count = 0
    # This is inefficient for lists, but fine for small scale
    # Better: do a join query or subquery. Given the "sqlite json dates" structure, python side filter is safer.
    
    bookings = db.query(models.Booking).filter(
        models.Booking.asset_id == asset.id,
        models.Booking.status.in_(["pending", "awaiting_payment", "paid", "in_possession"])
    ).all()
    
    for b in bookings:
        # Check overlaps with today?
        # If user books for next week, should it show unavailable today?
        # Usually no. But "Quantity: 5" often implies "Total Stock". 
        # "Available: 4" implies 1 is out.
        # If the user says "count doesn't update", they likely see "Inventory: 5" and want "Available: 4".
        # Let's subtract ALL active bookings for now to be safe/responsive to "request made", 
        # or implement proper date overlap with "now".
        # Let's do overlap with "now" to be accurate.
        
        # Parse dates
        if not b.dates: continue
        b_dates = b.dates
        if isinstance(b_dates, str):
            import json
            try:
                b_dates = json.loads(b_dates)
            except:
                continue
        
        if not isinstance(b_dates, dict) or "start" not in b_dates:
             continue
             
        try:
            b_start = datetime.fromisoformat(str(b_dates["start"]).replace("Z", "+00:00")).replace(tzinfo=None)
            b_end = datetime.fromisoformat(str(b_dates["end"]).replace("Z", "+00:00")).replace(tzinfo=None)
            
            # Simple overlap check: is NOW within booking window? 
            # Or is booking status 'in_possession'? 
            # If 'in_possession', definitely unavailable.
            if b.status == 'in_possession':
                active_count += b.quantity
            elif now >= b_start and now <= b_end:
                 active_count += b.quantity
            # If status is pending/paid but dates are future?
            # User might expect "Available for my selected dates". The UI has a date picker.
            # But the UI *also* shows a static "Inventory: X". I should update that static text to "Available Now: Y".
            # If I make a request for *today*, it should drop.
            
        except:
             continue
    
    return max(0, asset.total_quantity - active_count)


def get_assets(db: Session, skip: int = 0, limit: int = 100, location: str = None, type: str = None):
    query = db.query(models.Asset)
    if location:
        query = query.filter(models.Asset.location.contains(location))
    if type:
        query = query.filter(models.Asset.type.contains(type))
    assets = query.offset(skip).limit(limit).all()
    
    # Calculate available_quantity
    for asset in assets:
        asset.available_quantity = calculate_availability(db, asset)
        
    return assets

def get_asset(db: Session, asset_id: int):
    asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    if asset:
        asset.available_quantity = calculate_availability(db, asset)
    return asset

def create_asset(db: Session, asset: schemas.AssetCreate):
    db_asset = models.Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def update_asset(db: Session, asset_id: int, asset_data: schemas.AssetUpdate, user_id: int = None):
    db_asset = get_asset(db, asset_id)
    if db_asset:
        update_data = asset_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_asset, key, value)
        
        if user_id:
            db_asset.last_modified_by_id = user_id
            
        db.commit()
        db.refresh(db_asset)
    return db_asset

def delete_asset(db: Session, asset_id: int):
    db_asset = get_asset(db, asset_id)
    if db_asset:
        db.delete(db_asset)
        db.commit()

# Bookings
import uuid

def generate_ref_code():
    return f"BK-{uuid.uuid4().hex[:6].upper()}"

def get_bookings(db: Session, user_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Booking)
    if user_id:
        query = query.filter(models.Booking.user_id == user_id)
    import traceback
    import json
    try:
        bookings = query.options(
        joinedload(models.Booking.user),
        joinedload(models.Booking.asset)
    ).order_by(models.Booking.created_at.desc()).offset(skip).limit(limit).all()
        
        # Fix for SQLite JSON string issue
        for b in bookings:
            if isinstance(b.dates, str):
                try:
                    b.dates = json.loads(b.dates)
                except:
                    b.dates = {}
            # Also fix audits
            for a in b.audits:
                if isinstance(a.details, str):
                    try:
                        a.details = json.loads(a.details)
                    except:
                        a.details = {}
        return bookings
    except Exception as e:
        with open("backend_error.log", "a") as f:
            f.write(f"CRITICAL ERROR IN get_bookings: {str(e)}\n{traceback.format_exc()}\n")
        raise e

def get_booking(db: Session, booking_id: int):
    # import json # already imported in get_bookings scope, but good to be safe or module level
    import json
    b = db.query(models.Booking).options(
        joinedload(models.Booking.user),
        joinedload(models.Booking.asset)
    ).filter(models.Booking.id == booking_id).first()
    if b:
        # Fix dates JSON
        if isinstance(b.dates, str):
            try:
                b.dates = json.loads(b.dates)
            except:
                b.dates = {}
        # Fix audits JSON
        for a in b.audits:
            if isinstance(a.details, str):
                try:
                    a.details = json.loads(a.details)
                except:
                    a.details = {}
    return b

from fastapi import HTTPException
from datetime import datetime

def create_booking(db: Session, booking: schemas.BookingCreate, user_id: int):
    import traceback
    with open("debug_flow.txt", "a") as f:
        f.write(f"ENTER create_booking for user {user_id} asset {booking.asset_id}\n")

    try:
        # Check Availability
        with open("debug_flow.txt", "a") as f: f.write("Getting asset...\n")
        asset = get_asset(db, booking.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Parse requested dates
        with open("debug_flow.txt", "a") as f: f.write(f"Parsing dates: {booking.dates}\n")
        req_start = datetime.fromisoformat(str(booking.dates["start"]).replace("Z", "+00:00"))
        req_end = datetime.fromisoformat(str(booking.dates["end"]).replace("Z", "+00:00"))
        
        # Get all active bookings for this asset
        # In a production app, use DB-side filtering. Here we filter in Python for JSON simplicity.
        with open("debug_flow.txt", "a") as f: f.write("Querying active bookings...\n")
        active_statuses = ["pending", "awaiting_payment", "paid", "in_possession", "overdue"]
        asset_bookings = db.query(models.Booking).filter(
            models.Booking.asset_id == booking.asset_id,
            models.Booking.status.in_(active_statuses)
        ).all()
        
        current_reserved = 0
        with open("debug_flow.txt", "a") as f: f.write(f"Found {len(asset_bookings)} existing bookings. Checking overlap...\n")
        
        for b in asset_bookings:
            # Check overlap
            # Overlap if: A_start <= B_end AND A_end >= B_start
            if not b.dates: continue
            
            # Handle string dates (if JSON not decoded)
            b_dates = b.dates
            if isinstance(b_dates, str):
                import json
                try:
                    b_dates = json.loads(b_dates)
                except:
                    continue

            if not isinstance(b_dates, dict) or "start" not in b_dates:
                    continue
            
            b_start = datetime.fromisoformat(str(b_dates["start"]).replace("Z", "+00:00"))
            b_end = datetime.fromisoformat(str(b_dates["end"]).replace("Z", "+00:00"))
            
            if req_start <= b_end and req_end >= b_start:
                current_reserved += b.quantity
                
        if current_reserved + booking.quantity > asset.total_quantity:
            with open("debug_flow.txt", "a") as f: f.write("Insufficient units!\n")
            raise HTTPException(status_code=400, detail=f"Insufficient units available. {asset.total_quantity - current_reserved} units remaining for these dates.")
            
        # Create Booking
        with open("debug_flow.txt", "a") as f: f.write("Creating booking record...\n")
        db_booking = models.Booking(
            **booking.model_dump(),
            user_id=user_id,
            reference_code=generate_ref_code(),
            status="pending"
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        
        # Create Initial Audit Log
        create_booking_audit(db, db_booking.id, "Created", "Booking created by user", user_id)
        
        # FIX: Ensure dates is a dict before returning to Pydantic
        import json
        if isinstance(db_booking.dates, str):
            try:
                db_booking.dates = json.loads(db_booking.dates)
            except:
                pass

        # FIX: Ensure audit details are dicts
        for a in db_booking.audits:
            if isinstance(a.details, str):
                try:
                    a.details = json.loads(a.details)
                except:
                    pass
        
        # FIX: Ensure Asset JSON fields are parsed (if loaded/returned)
        if db_booking.asset:
            for field in ['specs', 'images', 'duration_options', 'availability']:
                val = getattr(db_booking.asset, field, None)
                if isinstance(val, str):
                    try:
                        setattr(db_booking.asset, field, json.loads(val))
                    except:
                        pass

        # FIX: Ensure User JSON fields are parsed (if loaded/returned)
        # Note: create_booking doesn't usually load user, but if Pydantic expects it...
        if db_booking.user:
            for field in ['certifications', 'needs']:
                val = getattr(db_booking.user, field, None)
                if isinstance(val, str):
                    try:
                        setattr(db_booking.user, field, json.loads(val))
                    except:
                        pass
        
        # Debugging Validation
        try:
            schemas.Booking.model_validate(db_booking, from_attributes=True)
        except Exception as val_err:
            with open("debug_flow.txt", "a") as f: f.write(f"VALIDATION FAILURE: {val_err}\n")

        with open("debug_flow.txt", "a") as f: f.write("SUCCESS.\n")
        return db_booking

    except HTTPException as he:
        raise he
    except Exception as e:
        with open("backend_error.log", "a") as f:
            f.write(f"CRITICAL ERROR IN create_booking: {str(e)}\n{traceback.format_exc()}\n")
        raise e

    # Create Initial Audit Log
    create_booking_audit(db, db_booking.id, "Created", "Booking created by user", user_id)
    
    return db_booking

def update_booking_status(db: Session, booking_id: int, status: str, performed_by_id: int):
    db_booking = get_booking(db, booking_id)
    if db_booking:
        old_status = db_booking.status
        db_booking.status = status
        
        # Payment Logic Hook (Simple)
        if status == "paid":
             db_booking.payment_status = "paid"
        
        db.commit()
        db.refresh(db_booking)
        
        # Audit Log
        create_booking_audit(
            db, 
            booking_id, 
            "Status Updated", 
            {"from": old_status, "to": status}, 
            performed_by_id
        )
        
    return db_booking

def create_booking_audit(db: Session, booking_id: int, action: str, details: Any, performed_by_id: int = None):
    db_audit = models.BookingAudit(
        booking_id=booking_id,
        action=action,
        details=details,
        performed_by_id=performed_by_id
    )
    db.add(db_audit)
    db.commit()

def cancel_booking(db: Session, booking_id: int, user_id: int):
    # Retrieve booking
    db_booking = get_booking(db, booking_id)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Check authorization
    if db_booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
        
    # Check if cancellable
    # Allow: pending, awaiting_payment, paid (maybe? if policy allows), custom logic
    allowed_statuses = ["pending", "awaiting_payment", "paid"] 
    if db_booking.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Cannot cancel booking with status: {db_booking.status}")
    
    old_status = db_booking.status
    db_booking.status = "cancelled"
    
    if old_status == "paid":
        db_booking.payment_status = "refunded" # Or 'pending_refund'
        
    db.commit()
    db.refresh(db_booking)
    
    # Audit
    create_booking_audit(
        db, 
        booking_id, 
        "Cancelled", 
        {"reason": "User requested cancellation", "from": old_status}, 
        user_id
    )
    
    return db_booking


    
    return db_booking

def create_payment(db: Session, booking_id: int, payment: schemas.PaymentCreate, user_id: int):
    import uuid
    
    booking = get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.user_id != user_id:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    if booking.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Booking is already paid")
        
    # Create Payment
    db_payment = models.Payment(
        booking_id=booking_id,
        reference=f"PAY-{uuid.uuid4().hex[:8].upper()}",
        amount=payment.amount,
        method=payment.method,
        status="success" # Simulating success
    )
    db.add(db_payment)
    
    # Update Booking
    booking.status = "paid"
    booking.payment_status = "paid"
    booking.total_amount = payment.amount
    
    db.commit()
    db.refresh(db_payment)
    db.refresh(booking)
    
    create_booking_audit(db, booking_id, "Payment Received", {"amount": payment.amount, "ref": db_payment.reference}, user_id)
    
    return db_payment

def get_stats(db: Session):
    users_count = db.query(models.User).count()
    active_assets = db.query(models.Asset).filter(models.Asset.active == True).count()
    pending_bookings = db.query(models.Booking).filter(models.Booking.status == "pending").count()
    return {
        "users": users_count,
        "activeAssets": active_assets,
        "pendingBookings": pending_bookings
    }

def get_admin_dashboard_stats(db: Session):
    users_count = db.query(models.User).count()
    active_assets = db.query(models.Asset).filter(models.Asset.active == True).count()
    
    # "Pending Requests" -> Pending
    pending = db.query(models.Booking).filter(models.Booking.status == "pending").count()
    
    # "Assets with Users" -> In Possession
    in_possession = db.query(models.Booking).filter(models.Booking.status == "in_possession").count()
    
    # "Completion Rate" derived from Completed (Returned) vs Total
    completed = db.query(models.Booking).filter(models.Booking.status == "returned").count()
    
    total = db.query(models.Booking).count()
    
    return {
        "total_users": users_count,
        "active_assets": active_assets,
        "pending_requests": pending,
        "assets_in_possession": in_possession,
        "completed_requests": completed,
        "total_requests": total
    }

def get_user_dashboard_stats(db: Session, user_id: int):
    total = db.query(models.Booking).filter(models.Booking.user_id == user_id).count()
    pending = db.query(models.Booking).filter(models.Booking.user_id == user_id, models.Booking.status == "pending").count()
    active = db.query(models.Booking).filter(models.Booking.user_id == user_id, models.Booking.status.in_(["in_possession", "paid"])).count()
    completed = db.query(models.Booking).filter(models.Booking.user_id == user_id, models.Booking.status == "returned").count()
    
    return {
        "total_bookings": total,
        "pending_bookings": pending,
        "active_bookings": active,
        "completed_bookings": completed # Returned
    }

def create_feedback(db: Session, booking_id: int, feedback: schemas.FeedbackCreate, user_id: int):
    # Get booking
    booking = get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check authorization
    if booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Check status
    if booking.status not in ["returned", "completed"]:
        raise HTTPException(status_code=400, detail="Booking must be completed to leave feedback")
        
    # Check explicitly for existing feedback
    existing = db.query(models.Feedback).filter(models.Feedback.booking_id == booking_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already submitted")

    db_feedback = models.Feedback(
        booking_id=booking_id,
        asset_id=booking.asset_id,
        user_id=user_id,
        rating=feedback.rating,
        comment=feedback.comment
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

