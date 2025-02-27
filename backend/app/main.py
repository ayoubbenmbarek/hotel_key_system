# backend/app/main.py
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


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_application():
    app = FastAPI(
        title="Hotel Virtual Key API",
        description="API for managing hotel virtual keys",
        version="1.0.0",
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
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up application...")
        create_tables()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application...")
    
    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "healthy"}
    
    return app


app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
