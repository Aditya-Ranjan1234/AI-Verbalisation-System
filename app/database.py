"""
Database Connection Management
Handles PostgreSQL (with PostGIS) and MongoDB connections
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator
from .config import settings

# PostgreSQL Setup
# Convert postgresql:// to postgresql+asyncpg:// for async support
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# SQLAlchemy Base for ORM models
Base = declarative_base()

# MongoDB Setup
mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
mongodb = mongodb_client.trip_verbalization


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get async database session
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_mongo_db():
    """
    Dependency for FastAPI to get MongoDB database
    Usage: mongo_db = Depends(get_mongo_db)
    """
    return mongodb


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models before creating tables
        from . import models
        await conn.run_sync(Base.metadata.create_all)
        
        # Check for PostGIS extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
