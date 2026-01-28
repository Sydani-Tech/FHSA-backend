from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    business_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    production_focus: Optional[str] = None
    certifications: Optional[List[str]] = None
    needs: Optional[List[str]] = None

class UserCreate(UserBase):
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    business_name: str
    role: Optional[str] = "business_user"

class UserUpdate(BaseModel):
    status: str

class UserProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    production_focus: Optional[str] = None
    certifications: Optional[List[str]] = None
    needs: Optional[List[str]] = None

class User(UserBase):
    id: int
    role: str
    status: str
    login_count: int
    created_at: datetime

    class Config:
        from_attributes = True

# Asset Schemas
class AssetBase(BaseModel):
    name: str
    type: str
    location: str
    description: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    cost: str
    duration_options: Optional[List[str]] = None
    availability: Optional[Dict[str, Any]] = None
    total_quantity: int = 1
    active: bool = True
    available_quantity: Optional[int] = None

class AssetCreate(AssetBase):
    owner_id: Optional[int] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    cost: Optional[str] = None
    duration_options: Optional[List[str]] = None
    availability: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None
    total_quantity: Optional[int] = None

class Asset(AssetBase):
    id: int
    owner_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    last_modified_by_id: Optional[int] = None

    class Config:
        from_attributes = True

# Booking Schemas
class BookingBase(BaseModel):
    asset_id: int
    dates: Dict[str, Any]
    purpose: str
    quantity: int = 1
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdateStatus(BaseModel):
    status: str

class BookingAuditResponse(BaseModel):
    id: int
    action: str
    timestamp: datetime
    performed_by_id: Optional[int]
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

# Feedback Schemas
class FeedbackBase(BaseModel):
    rating: int
    comment: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    booking_id: int
    asset_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Payment Schemas
class PaymentBase(BaseModel):
    amount: str
    method: str = "card"

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    booking_id: int
    reference: str
    status: str
    currency: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Booking (Updated)
class Booking(BookingBase):
    id: int
    reference_code: str
    user_id: int
    status: str
    payment_status: str
    total_amount: Optional[str] = None
    created_at: datetime
    audits: List[BookingAuditResponse] = []
    payments: List[Payment] = []
    feedback: Optional[Feedback] = None
    
    # Nested relationships for Admin/Detail views
    user: Optional[User] = None
    asset: Optional[Asset] = None

    class Config:
        from_attributes = True

# Stats Schema
class Stats(BaseModel):
    users: int
    activeAssets: int
    pendingBookings: int

class UserDashboardStats(BaseModel):
    total_bookings: int
    pending_bookings: int
    active_bookings: int # In possession / paid
    completed_bookings: int # Returned

class AdminDashboardStats(BaseModel):
    total_users: int
    active_assets: int
    pending_requests: int
    assets_in_possession: int
    completed_requests: int
    total_requests: int
# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User # Include user details in login response for frontend convenience
