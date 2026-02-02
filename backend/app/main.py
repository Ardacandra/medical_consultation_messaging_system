from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base, SessionLocal
from app.db.models import User
from sqlalchemy import select, text
from app.api.v1.api import api_router

app = FastAPI(title="Nightingale API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Auto-Migration for chief_complaint
        try:
            await conn.execute(text("ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS chief_complaint JSON DEFAULT '[]'::json"))
        except Exception as e:
            print(f"Migration Note (chief_complaint): {e}")

    # Auto-Migration for escalation snapshot
        try:
            await conn.execute(text("ALTER TABLE escalations ADD COLUMN IF NOT EXISTS patient_profile_snapshot JSON"))
        except Exception as e:
            print(f"Migration Note (snapshot): {e}")

        # Auto-Migration: Users & Voice
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'patient'"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS clinic_id VARCHAR"))
            await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS audio_transcript_id VARCHAR"))
            await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS audio_url VARCHAR"))
            print("Migration Success: Added User & Voice columns")
        except Exception as e:
            print(f"Migration Note (Auth/Voice): {e}")
    
    # Seed default user
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalars().first()
        if not user:
            print("Seeding default user...")
            from app.core.security import get_password_hash
            default_user = User(
                id=1, 
                email="patient@example.com", 
                hashed_password=get_password_hash("Nightingale@123"),
                role="patient",
                is_active=True
            )
            session.add(default_user)
            await session.commit()
        else:
            # Backfill password if missing or update if it's the old insecure default
            from app.core.security import get_password_hash, verify_password
            
            # Check if password is the old "password"
            is_old_password = False
            if user.hashed_password:
                try:
                    is_old_password = verify_password("password", user.hashed_password)
                except Exception:
                    pass

            if not user.hashed_password or is_old_password:
                print("Updating/Backfilling password for default user...")
                user.hashed_password = get_password_hash("Nightingale@123")
                user.role = "patient"
                user.is_active = True
                await session.commit()

        # Seed default clinician (Check explicitly)
        result = await session.execute(select(User).where(User.id == 2))
        clinician = result.scalars().first()
        if not clinician:
            print("Seeding default clinician...")
            from app.core.security import get_password_hash
            default_clinician = User(
                id=2, 
                email="clinician@example.com", 
                hashed_password=get_password_hash("Nightingale@123"),
                role="clinician",
                is_active=True
            )
            session.add(default_clinician)
            await session.commit()


@app.get("/")
def read_root():
    return {"message": "Welcome to Nightingale API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
