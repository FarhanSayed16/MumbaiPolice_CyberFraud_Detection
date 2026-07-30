import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.core.security import get_password_hash
from app.config import settings

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User))
        users = res.scalars().all()
        hashed = get_password_hash("SecurePolice@2026")
        for u in users:
            u.hashed_password = hashed
        await db.commit()
        print(f"Updated {len(users)} users.")

if __name__ == "__main__":
    asyncio.run(main())
