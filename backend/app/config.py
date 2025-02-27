# backend/app/config.py
import os
import secrets
from pydantic import BaseSettings, PostgresDsn, field_validator, EmailStr
from typing import Optional, Dict, Any, Union


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "hotel_keys")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
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
