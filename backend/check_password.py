import asyncio
from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import verify_password
from sqlalchemy import select

async def check_password():
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalars().first()
        if user:
            is_old = verify_password("password", user.hashed_password)
            is_new = verify_password("Nightingale@123", user.hashed_password)
            print(f"User found: {user.email}")
            print(f"Is password 'password'? {is_old}")
            print(f"Is password 'Nightingale@123'? {is_new}")
        else:
            print("User not found.")

if __name__ == "__main__":
    asyncio.run(check_password())
