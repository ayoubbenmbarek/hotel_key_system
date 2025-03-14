# backend/app/config.py
import os
import secrets
import re
from typing import Optional, Dict, Any, Union, List

# In Pydantic v2, BaseSettings has been moved to pydantic-settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, EmailStr, field_validator, model_validator


# Function to clean environment variable values by removing comments
def clean_env_value(value):
    if isinstance(value, str):
        # Remove comments (anything after #)
        return re.sub(r'#.*$', '', value).strip()
    return value


# Get environment variables with comments removed
def get_env(name, default=None):
    value = os.getenv(name, default)
    return clean_env_value(value)


class Settings(BaseSettings):
    API_V1_STR: str = get_env("API_V1_STR", "/api/v1")
    SECRET_KEY: str = get_env("SECRET_KEY", secrets.token_urlsafe(32))
    APPLE_PUSH_PRIVATE_KEY_PATH: str = get_env("APPLE_PUSH_PRIVATE_KEY_PATH", "./certificates/apple/AuthKey_BA9F84UHXN.p8")
    APPLE_PUSH_KEY_ID: str = get_env("APPLE_PUSH_KEY_ID", "BA9F84UHXN")
    PRODUCTION: str = get_env("PRODUCTION", "True")
    ENVIRONMENT: str = get_env("ENVIRONMENT", "development")

    # Set a default value directly as an integer
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days

    # Clean the environment variable if it exists
    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES", mode="before")
    @classmethod
    def parse_token_expire(cls, v):
        if isinstance(v, str):
            # Remove comments and convert to int
            cleaned = clean_env_value(v)
            try:
                return int(cleaned)
            except ValueError:
                return 11520  # Default if parsing fails
        return v
    
    # Database
    POSTGRES_SERVER: str = get_env("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = get_env("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = get_env("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = get_env("POSTGRES_DB", "hotel_keys")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Create the database URI manually
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:5432/{self.POSTGRES_DB}"
            )
        return self
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = get_env("SMTP_HOST", "smtp.gmail.com")
    SMTP_USER: Optional[str] = get_env("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = get_env("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[EmailStr] = get_env("EMAILS_FROM_EMAIL", "info@example.com")
    EMAILS_FROM_NAME: Optional[str] = get_env("EMAILS_FROM_NAME", "Hotel Key System")
    
    # Wallet pass settings
    APPLE_PASS_TYPE_ID: str = get_env("APPLE_PASS_TYPE_ID", "pass.com.azaynohotel.nfc")
    APPLE_TEAM_ID: str = get_env("APPLE_TEAM_ID", "5CADJ27PT5")
    APPLE_CERT_PATH: str = get_env("APPLE_CERT_PATH", "./certificates/apple/cert.pem")
    APPLE_KEY_PATH: str = get_env("APPLE_KEY_PATH", "./certificates/apple/key.pem")
    APPLE_WWDR_PATH: str = get_env("APPLE_WWDR_PATH", "./certificates/apple/wwdr.pem")
    
    GOOGLE_PAY_ISSUER_ID: str = get_env("GOOGLE_PAY_ISSUER_ID", "3388000000022198")
    GOOGLE_SERVICE_ACCOUNT_PATH: str = get_env("GOOGLE_SERVICE_ACCOUNT_PATH", "./certificates/google/service_account.json")
    
    # Application info
    HOTEL_NAME: str = get_env("HOTEL_NAME", "Palacio Holding Mbarek")
    HOTEL_LOGO_URL: str = get_env("HOTEL_LOGO_URL", "/static/images/hotel_logo.png")
    HOTEL_ICON_URL: str = get_env("HOTEL_ICON_URL", "/static/images/hotel_icon.png")
    
    # Frontend URLs
    FRONTEND_URL: str = get_env("FRONTEND_URL", "http://localhost:3000")
    PASS_BASE_URL: str = get_env("PASS_BASE_URL", "https://2e24-2a01-e0a-159-2b50-b46f-2afb-eef3-7ede.ngrok-free.app/api/v1/passes")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
