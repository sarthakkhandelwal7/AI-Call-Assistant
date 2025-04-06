from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app.core.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# Load environment variables

# Get settings
settings = Settings()

# Use settings for database connection
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE
)

# Log database pool settings
logger.info(f"Database pool settings: size={settings.DB_POOL_SIZE}, "
            f"overflow={settings.DB_MAX_OVERFLOW}, "
            f"timeout={settings.DB_POOL_TIMEOUT}, "
            f"recycle={settings.DB_POOL_RECYCLE}")

SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autocommit=False, autoflush=False)

base = declarative_base()

# Connection counter for debugging
_active_connections = 0

# Dependency to get DB session with improved connection tracking
async def get_db():
    global _active_connections
    _active_connections += 1
    connection_id = id(SessionLocal)
    logger.debug(f"Opening DB connection {connection_id} (Active: {_active_connections})")
    
    try:
        async with SessionLocal() as db:
            try:
                yield db
            finally:
                await db.close()
                _active_connections -= 1
                logger.debug(f"Closed DB connection {connection_id} (Active: {_active_connections})")
    except Exception as e:
        _active_connections -= 1
        logger.error(f"Error with DB connection {connection_id}: {str(e)}")
        raise

# Alternative context manager for manual connection management
@asynccontextmanager
async def get_db_context():
    """Context manager for database sessions that ensures proper cleanup."""
    async for db in get_db():
        try:
            yield db
        finally:
            # Connection will be closed in the get_db generator finalizer
            pass