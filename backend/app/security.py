# backend/app/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenPayload
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from the token
    
    Dependency to be used in FastAPI endpoints to get the authenticated user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.sub).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return user


def get_current_active_staff(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if the current user is staff
    
    Dependency to be used in FastAPI endpoints that require staff permissions
    """
    if current_user.role not in ["admin", "hotel_staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if the current user is admin
    
    Dependency to be used in FastAPI endpoints that require admin permissions
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
