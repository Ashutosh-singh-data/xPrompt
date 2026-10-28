from typing import Generator
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase
from app.core.config import settings

logger = logging.getLogger("consultos.database")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Connect arguments specific to SQLite
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite connections."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        # Ignore for non-SQLite engines if switched
        pass


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a database session per request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None) -> None:
    """Initialize database tables during startup."""
    active_engine = target_engine or engine
    logger.info("Initializing database tables...")
    # Import all models to ensure they are registered with Base.metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=active_engine)
    logger.info("Database tables initialized successfully.")


def check_db_connection(db: Session) -> bool:
    """Check actual database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"Database connectivity check failed: {exc}")
        return False
