"""
Database connection and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Use SQLite for development if PostgreSQL is not available
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgresql://") and os.environ.get("USE_SQLITE", "true").lower() == "true":
    # Switch to SQLite for local development
    DATABASE_URL = "sqlite:///./homegpu_dev.db"
    print(f"⚠️  Using SQLite for development: {DATABASE_URL}")

# Create engine - adjust settings for SQLite vs PostgreSQL
if DATABASE_URL.startswith("sqlite://"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def init_db():
    """Create all tables in the database."""
    from app.models import user, wallet, job, transaction
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

