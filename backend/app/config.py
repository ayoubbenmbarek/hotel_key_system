# backend/app/config.py
import os
import secrets
from typing import Optional, Dict, Any, Union, List

# In Pydantic v2, BaseSettings has been moved to pydantic-settings
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, EmailStr, field_validator, model_validator


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "hotel_keys")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "09388906")
    

    # Create the database URI manually instead of using PostgresDsn
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )
        return self
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[EmailStr] = os.getenv("EMAILS_FROM_EMAIL", "info@example.com")
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME", "Hotel Key System")
    
    # Wallet pass settings
    APPLE_PASS_TYPE_ID: str = os.getenv("APPLE_PASS_TYPE_ID", "pass.com.yourhotel.key")
    APPLE_TEAM_ID: str = os.getenv("APPLE_TEAM_ID", "1234567890")
    APPLE_CERT_PATH: str = os.getenv("APPLE_CERT_PATH", "./certificates/apple/cert.pem")
    APPLE_KEY_PATH: str = os.getenv("APPLE_KEY_PATH", "./certificates/apple/key.pem")
    APPLE_WWDR_PATH: str = os.getenv("APPLE_WWDR_PATH", "./certificates/apple/wwdr.pem")
    
    GOOGLE_PAY_ISSUER_ID: str = os.getenv("GOOGLE_PAY_ISSUER_ID", "3388000000022198")
    GOOGLE_SERVICE_ACCOUNT_PATH: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "./certificates/google/service_account.json")
    
    # Application info
    HOTEL_NAME: str = os.getenv("HOTEL_NAME", "Your Hotel")
    HOTEL_LOGO_URL: str = os.getenv("HOTEL_LOGO_URL", "https://your-hotel.com/logo.png")
    HOTEL_ICON_URL: str = os.getenv("HOTEL_ICON_URL", "https://your-hotel.com/icon.png")
    
    # Frontend URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    PASS_BASE_URL: str = os.getenv("PASS_BASE_URL", "https://passes.your-hotel.com")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
