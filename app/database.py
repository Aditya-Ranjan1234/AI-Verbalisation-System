"""
Database Connection Management
Handles PostgreSQL (with PostGIS) and MongoDB connections
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import ssl
from .config import settings

# PostgreSQL Setup
# Normalize URL to async driver
def _normalize_url(url: str):
    args = {}
    u = url
    if u.startswith("postgres://"):
        u = u.replace("postgres://", "postgresql+asyncpg://", 1)
    elif u.startswith("postgresql://"):
        u = u.replace("postgresql://", "postgresql+asyncpg://", 1)
    parsed = urlparse(u)
    query = parse_qs(parsed.query)
    keys = {k.lower(): k for k in query.keys()}
    if "sslmode" in keys:
        mode = query[keys["sslmode"]][0]
        if mode == "disable":
            args["ssl"] = False
        else:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            args["ssl"] = ctx
        query.pop(keys["sslmode"], None)
    u = urlunparse(parsed._replace(query=""))
    return u, args

database_url = settings.POSTGRES_URL_NON_POOLING or settings.DATABASE_URL or settings.POSTGRES_URL
connect_args = {}
if database_url:
    database_url, connect_args = _normalize_url(database_url)

if database_url:
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        future=True,
        connect_args=connect_args or None
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
    # prefer non-pooling URL for DDL if available
    init_url = settings.POSTGRES_URL_NON_POOLING or (settings.DATABASE_URL or settings.POSTGRES_URL)
    init_args = {}
    if init_url:
        init_url, init_args = _normalize_url(init_url)
    init_engine = None
    try:
        init_engine = create_async_engine(
            init_url,
            echo=settings.DEBUG,
            future=True,
            connect_args=init_args or None
        ) if init_url else engine
        async with init_engine.begin() as conn:
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
    finally:
        if init_engine and init_engine is not engine:
            await init_engine.dispose()
