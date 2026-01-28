from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, auth
from ..database import SessionLocal

router = APIRouter(
    prefix="/api",
    tags=["Admin"]
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User Management (Admin)
@router.get("/users", response_model=List[schemas.User])
def list_users(current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.get_users(db)

@router.get("/users/{user_id}", response_model=schemas.User)
def get_user_details(user_id: int, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}/status", response_model=schemas.User)
def update_user_status(user_id: int, status_update: schemas.UserUpdate, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.update_user_status(db, user_id, status_update.status)

@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    crud.delete_user(db, user_id)
    return {"message": "User deleted"}

# Admin Asset Management
@router.post("/assets", response_model=schemas.Asset)
def create_asset(asset: schemas.AssetCreate, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.create_asset(db, asset)

@router.put("/assets/{asset_id}", response_model=schemas.Asset)
def update_asset(asset_id: int, asset: schemas.AssetUpdate, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.update_asset(db, asset_id, asset, user_id=current_user.id)

@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    crud.delete_asset(db, asset_id)
    return {"message": "Asset deleted"}

# Admin Booking Management
@router.patch("/bookings/{booking_id}/status", response_model=schemas.Booking)
def update_booking_status(booking_id: int, status_update: schemas.BookingUpdateStatus, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.update_booking_status(db, booking_id, status_update.status, current_user.id)

# Stats
@router.get("/stats")
def get_stats(current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.get_stats(db)

@router.get("/admin/dashboard-stats", response_model=schemas.AdminDashboardStats)
def get_admin_dashboard_stats(current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return crud.get_admin_dashboard_stats(db)
