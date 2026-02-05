"""
Database connection and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Use DATABASE_URL from settings directly
DATABASE_URL = settings.DATABASE_URL
# Fix Heroku "postgres://" legacy protocol usage for SQLAlchemy 1.4+
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
print(f"🔌 Database: {DATABASE_URL.split('@')[0].split('://')[0]}://***")

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
    from app.models import user, wallet, job, transaction, ad
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

