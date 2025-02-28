# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.config import dictConfig
import time
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.config import settings
from app.db.session import engine
from app.models.base import Base

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": "backend/logs/app.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "app": {"handlers": ["console", "file"], "level": "INFO"},
        "uvicorn": {"handlers": ["console", "file"], "level": "INFO"},
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}

dictConfig(logging_config)
logger = logging.getLogger("app")


# Request timing middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"Request took {process_time:.4f}s: {request.method} {request.url.path}")
        return response


def create_admin_user():
    """
    Create initial admin user if not exists
    """
    from app.security import get_password_hash
    from sqlalchemy.orm import Session
    from models.user import User
    from app.db.session import SessionLocal

    try:
        db = SessionLocal()
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        print(existing_admin, "existing_admin")
        
        if not existing_admin:
            # Create admin user
            admin_user = User(
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                phone_number='1234567890',
                # admin123
                hashed_password='$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
                role='ADMIN',
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def create_tables():
    """
    Create database tables based on SQLAlchemy models
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application
    
    Handles startup and shutdown events
    """
    # Startup tasks
    logger.info("Starting up application...")
    
    # Create database tables
    create_tables()
    print("tables created")
    
    # Create admin user
    # create_admin_user()
    # print("Admin user created")
    
    logger.info("Application startup complete")
    
    # Yield control back to the application
    yield
    
    # Shutdown tasks
    logger.info("Shutting down application...")
    
    # Optional: Add any cleanup tasks
    # For example, closing database connections, clearing caches, etc.
    logger.info("Application shutdown complete")


def get_application():
    app = FastAPI(
        title="Hotel Virtual Key API",
        description="API for managing hotel virtual keys",
        version="1.0.0",
        lifespan=lifespan,  # Use the new lifespan handler
    )
    
    # Set up CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add timing middleware
    app.add_middleware(TimingMiddleware)
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "healthy"}
    
    return app


app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
