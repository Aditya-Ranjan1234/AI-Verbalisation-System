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
# Normalize URL to async driver
database_url = settings.DATABASE_URL or settings.POSTGRES_URL
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

if database_url:
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
else:
    engine = None
    async_session_maker = None

# SQLAlchemy Base for ORM models
Base = declarative_base()

# MongoDB Setup
mongodb_client = None
mongodb = None

mongodb_url = settings.MONGODB_URL or settings.MONGODB_URI

if mongodb_url:
    mongodb_client = AsyncIOMotorClient(mongodb_url)
    mongodb = mongodb_client.trip_verbalization


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get async database session
    Usage: db: AsyncSession = Depends(get_db)
    """
    if not async_session_maker:
        raise RuntimeError("Database URL not configured")
        
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
    if not engine:
        return
        
    async with engine.begin() as conn:
        from . import models
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        except Exception as e:
            if settings.DEBUG:
                print(f"PostGIS extension setup failed: {e}")
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            if settings.DEBUG:
                print(f"Table creation failed: {e}")
