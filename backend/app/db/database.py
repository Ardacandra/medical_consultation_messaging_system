from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use docker-compose service name 'db' or localhost for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/nightingale")

# SQLAlchemy 2.0 style async engine is better for FastAPI but for simplicity/speed of setup 
# I'll stick to sync for just the scaffolding phase or use asyncpg if requested. 
# Prompt said "FastAPI (Async)", so I should set up Async support.
# Updating to Async Engine.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Async URL usually starts with postgresql+asyncpg://
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
