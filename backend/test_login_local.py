import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "admin.mumbai@maharashtracyber.gov.in"))
        user = result.scalar_one_or_none()
        if not user:
            print("User not found!")
            return
        print("User found:", user.email)
        print("Hash:", user.hashed_password)
        try:
            is_valid = verify_password("SecurePolice@2026", user.hashed_password)
            print("Password valid:", is_valid)
        except Exception as e:
            print("Verify failed:", type(e), e)

asyncio.run(test())
