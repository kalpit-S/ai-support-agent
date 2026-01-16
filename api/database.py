# api/database.py
# Database connection for the API service.
# Uses shared models to ensure consistency with worker.

from shared.database import Base, get_engine, get_session_factory
from config import settings

# Create engine and session factory
engine = get_engine(settings.database_url, echo=False)
SessionLocal = get_session_factory(engine)


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Re-export Base for any code that imports from here
__all__ = ["Base", "engine", "SessionLocal", "get_db"]
