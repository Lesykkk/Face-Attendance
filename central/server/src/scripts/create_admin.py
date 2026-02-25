import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from core.database import async_session_factory, engine
from core.security import hash_password
from models.admin import Admin


async def main():
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    password = input("Password: ").strip()
    if not password:
        print("Password cannot be empty.")
        return

    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Admin).where(Admin.username == username)
            )
            if result.scalar_one_or_none():
                print(f"Admin '{username}' already exists.")
                return

            admin = Admin(
                username=username,
                password_hash=hash_password(password),
            )
            session.add(admin)
            await session.commit()
            print(f"Admin '{username}' created successfully.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
