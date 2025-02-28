# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.config import settings

# Convert the PostgresDsn object to a string
DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create test session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get DB session for FastAPI endpoint
    
    Usage:
    ```
    @app.get("/users/")
    async def get_users(db: Session = Depends(get_db)):
        ...
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for getting DB session
    
    Usage:
    ```
    with get_db_context() as db:
        ...
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
