from fastapi import FastAPI
from app.db.database import engine, Base, SessionLocal
from app.db.models import User
from sqlalchemy import select
from app.api.v1.api import api_router

app = FastAPI(title="Nightingale API", version="0.1.0")

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed default user
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalars().first()
        if not user:
            print("Seeding default user...")
            default_user = User(id=1, username="patient_zero", email="patient@example.com")
            session.add(default_user)
            await session.commit()

@app.get("/")
def read_root():
    return {"message": "Welcome to Nightingale API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
