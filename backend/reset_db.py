
import asyncio
from app.db.database import engine, Base
from app.main import startup
from sqlalchemy import text

async def reset_db():
    print("🗑️  Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # Drop migration table if exists (alembic) though we aren't using it explicitly here yet
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    
    print("✨ Creating tables and seeding data...")
    # Re-run the startup logic from main.py which handles creation and seeding
    await startup()
    print("✅ Database reset complete.")

if __name__ == "__main__":
    asyncio.run(reset_db())
