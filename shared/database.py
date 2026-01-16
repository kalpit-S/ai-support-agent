# shared/database.py
# Database utilities shared between API and Worker.
# Both services connect to the same PostgreSQL database.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()


def get_engine(database_url: str, echo: bool = False):
    """Create a SQLAlchemy engine for the given database URL."""
    return create_engine(database_url, pool_pre_ping=True, echo=echo)


def get_session_factory(engine):
    """Create a session factory bound to the given engine."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)
