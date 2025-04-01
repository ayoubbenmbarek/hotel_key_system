# backend/app/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.config import dictConfig
from app.db.session import SessionLocal
import time
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.config import settings
from app.db.session import engine
from app.models.base import Base


# Get the directory where the main.py file is located
base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "..", "logs")
os.makedirs(log_dir, exist_ok=True)


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
            "filename": os.path.join(log_dir, "app.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
    },
    "loggers": {
        # Set propagate=False for app and its subloggers
        "app": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "app.api": {"level": "INFO", "propagate": True},  # Will inherit from "app"
        "app.services": {"level": "INFO", "propagate": True},  # Will inherit from "app"
        "uvicorn": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
    },
    # Root logger has no handlers - messages propagate up to their parent loggers
    "root": {"level": "INFO"},
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

def startup_event():
    """Run tasks at application startup"""
    db = SessionLocal()
    try:
        # Update auth tokens for existing keys
        from app.services.wallet_service import update_auth_tokens_for_existing_keys
        updated = update_auth_tokens_for_existing_keys(db)
        logger.info(f"Startup: Updated auth tokens for {updated} keys")
        
        # Remove the check for expired keys on startup
        # from app.services.key_service import expire_outdated_keys
        # deactivated = expire_outdated_keys(db)
        # if deactivated > 0:
        #     logger.info(f"Startup: Deactivated {deactivated} expired keys")
    finally:
        db.close()

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
    
    # Run startup tasks
    startup_event()
    
    logger.info("Application startup complete")
    
    # Yield control back to the application
    yield
    
    # Shutdown tasks
    logger.info("Shutting down application...")
    
    # No scheduled_key_expiration task to cancel
    
    logger.info("Application shutdown complete")


def get_application():
    app = FastAPI(
        title="Hotel Virtual Key API",
        description="API for managing hotel virtual keys",
        docs_url="/api/v1/docs",
        # Also update the redoc URL for consistency
        redoc_url="/api/v1/redoc",
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
