from fastapi import FastAPI
from app import crud, schemas
from app.routers import auth, admin, business, upload # Added upload
from app.database import SessionLocal, engine
from app import models
import os
from fastapi.staticfiles import StaticFiles # Added StaticFiles

from fastapi.middleware.cors import CORSMiddleware

# Initialize DB Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FHSA API")

# Mount static files
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS configuration
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(business.router)
app.include_router(upload.router)

# Seed Database
def seed_db():
    db = SessionLocal()
    try:
        # Check Admin
        admin = crud.get_user_by_email(db, "admin@fhsa.org")
        if not admin:
            crud.create_user(db, schemas.UserCreate(
                email="admin@fhsa.org",
                password="admin123",
                role="admin",
                business_name="FHSA Admin",
                phone="08000000000",
                location="Abuja",
                production_focus="Administration",
                certifications=[],
                needs=[]
            ))
            print("Admin seeded")

        # Check Assets
        # Define the assets list first
        assets_data = [
            {
                "name": "Industrial Dough Mixer",
                "type": "Equipment",
                "location": "Garki, Abuja",
                "description": "High capacity mixer for bakery operations.",
                "specs": {"capacity": "50kg", "power": "2000W"},
                "cost": "5000",
                "duration_options": ["day"],
                "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
                "active": True,
                "images": ["https://d21d281c1yd2en.cloudfront.net/media/product_images/new-industrial-dough-bread-spiral-mixer-one-bag-50kg-8939-640x640.jpeg"]
            },
            {
                "name": "Commercial Deck Oven",
                "type": "Processing",
                "location": "Wuse 2, Abuja",
                "description": "Double deck gas oven, perfect for bread and pastries. High efficiency and even baking.",
                "specs": {"capacity": "4 Trays/Deck", "temp_range": "50-400C", "power": "Gas/Electric"},
                "cost": "15000",
                "duration_options": ["day", "week"],
                "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]},
                "active": True,
                "images": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ-j-f0z2z2z2z2z2z2z2z2z2z2z2z2z2z&s"]
            },
            {
                "name": "Refrigerated Delivery Truck",
                "type": "Logistics",
                "location": "Maitama, Abuja",
                "description": "3-ton refrigerated truck for perishable goods transport. Driver included.",
                "specs": {"capacity": "3 Tons", "temp_range": "-10 to 5C", "fuel": "Diesel"},
                "cost": "50000",
                "duration_options": ["trip", "day"],
                "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
                "active": True,
                "images": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8XytPzC_7XIttq-O2Mprtn8TppbmiNFbXkA&s"]
            },
            {
                "name": "John Deere Utility Tractor",
                "type": "Machinery",
                "location": "Kuje, Abuja",
                "description": "Versatile utility tractor for plowing, tilling, and hauling. Includes front loader attachment.",
                "specs": {"power": "75 HP", "drive": "4WD", "fuel": "Diesel"},
                "cost": "45000",
                "duration_options": ["day", "week"],
                "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
                "active": True,
                "images": ["https://thumbs.dreamstime.com/b/left-side-mahindra-tractor-yuvo-hp-white-background-wd-four-wheel-drive-front-exhost-air-filter-weights-208875766.jpg"]
            },
            {
                "name": "Cold CStorage Container",
                "type": "Cold Storage",
                "location": "Idu Industrial Layout, Abuja",
                "description": "Large capacity cold storage for vegetables and fruits. Temperature controlled.",
                "specs": {"capacity": "1000 sq ft", "temp_range": "0-10C", "power": "Grid/Generator"},
                "cost": "2000",
                "duration_options": ["day", "month"],
                "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
                "active": True,
                "images": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRA9dRQIDzGKtJCSmCByi_hgZAPKJqf13M0KA&s", "https://assets.easycallsales.com.ng/products/midea-chest-freezer-1732544726.webp"]
            },
            {
                "name": "Pepper Grinder",
                "type": "Machinery",
                "location": "Kaduna Road, Abuja",
                "description": "High efficiency combine harvester for maize and grains. Operator provided.",
                "specs": {"capacity": "Large", "width": "4m header", "fuel": "Diesel"},
                "cost": "8000",
                "duration_options": ["acre", "day"],
                "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
                "active": True,
                "images": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSBOhVE3_ClcNePmZqfa-WRWvPwSwNtfF9SuA&s"]
            },
            {
                "name": "Solar Irrigation Pump",
                "type": "Equipment",
                "location": "Kwali, Abuja",
                "description": "Mobile solar-powered water pump for irrigation. Eco-friendly and cost-effective.",
                "specs": {"flow_rate": "5000 L/hr", "power": "Solar", "head": "50m"},
                "cost": "5000",
                "duration_options": ["day", "week"],
                "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
                "active": True,
                "images": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpAf7xjA50mwgKDwcNBmFGZ4_ONvCHg9Y0gw&s"]
            }
        ]

        for asset_data in assets_data:
             # Check if asset exists by name to avoid duplicates
            existing_asset = db.query(models.Asset).filter(models.Asset.name == asset_data["name"]).first()
            if not existing_asset:
                crud.create_asset(db, schemas.AssetCreate(**asset_data))
                print(f"Seeded: {asset_data['name']}")
        
        print("Asset seeding check complete")
    except Exception as e:
        print(f"Error seeding DB: {e}")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    seed_db()

if __name__ == "__main__":
    import uvicorn
    # Use 8000 to match UV and Frontend defaults
    uvicorn.run(app, host="127.0.0.1", port=8000)
