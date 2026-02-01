import asyncio
from app.db.database import get_db, init_db
from app.db.models import PatientProfile
from sqlalchemy import select
from app.schemas import PatientProfileResponse

async def debug():
    # Ensure DB is init
    # await init_db() 
    
    async for session in get_db():
        print("Session created.")
        stmt = select(PatientProfile).where(PatientProfile.patient_id == 1)
        result = await session.execute(stmt)
        profile = result.scalars().first()
        
        if profile:
            print(f"Profile found: {profile.id}")
            print(f"Meds: {profile.medications} (Type: {type(profile.medications)})")
            
            # Try validating with Pydantic
            try:
                pydantic_profile = PatientProfileResponse.model_validate(profile)
                print("Pydantic Validation Success")
                print(pydantic_profile)
            except Exception as e:
                print(f"Pydantic Validation Failed: {e}")
        else:
            print("Profile not found.")
        break

if __name__ == "__main__":
    asyncio.run(debug())
