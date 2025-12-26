"""
Database Initialization Script
Run this to initialize the database and create an admin user
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.database import Base, async_session_maker
from app.models import User, UserRole
from app.auth import get_password_hash
from app.config import settings


async def init_database():
    """Initialize database tables and PostGIS extension"""
    print("Initializing database...")
    
    # Create async engine
    database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        # Create PostGIS extension
        print("Creating PostGIS extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        
        # Create all tables
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database initialized successfully!")
    
    # Create admin user
    print("\nCreating default admin user...")
    async with async_session_maker() as session:
        # Check if admin exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("Admin user already exists.")
        else:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            
            print("Admin user created successfully!")
            print("  Username: admin")
            print("  Password: admin123")
            print("  ⚠️  Please change the password after first login!")
    
    await engine.dispose()


async def drop_tables():
    """Drop all tables (WARNING: This will delete all data!)"""
    response = input("⚠️  WARNING: This will delete ALL data! Type 'yes' to confirm: ")
    
    if response.lower() != "yes":
        print("Operation cancelled.")
        return
    
    print("Dropping all tables...")
    
    database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("All tables dropped successfully!")
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        asyncio.run(drop_tables())
    else:
        asyncio.run(init_database())
