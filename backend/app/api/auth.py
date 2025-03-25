# backend/app/api/auth.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import EmailStr

from app.db.session import get_db
from app.security import create_access_token, verify_password, get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import Token, TokenPayload, User as UserSchema, UserCreate
from app.config import settings
from app.utils.validators import validate_password
from app.utils.email import send_welcome_email, send_password_reset_email

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Validate user and password
    if not user or not verify_password(form_data.password, user.hashed_password):
        print(f"Password verification result: {verify_password(form_data.password, user.hashed_password)}")
        print(f"Attempted password: {form_data.password}")
        print(f"Stored hash: {user.hashed_password}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user account"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            subject=user.email, 
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserSchema)  # Change User to UserSchema
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks
):  # Remove -> Any return type annotation
    """
    Register a new user
    """
    # Check if user already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone_number=user_in.phone_number,
        role=UserRole.GUEST,  # Default role for self-registration
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send welcome email in background
    background_tasks.add_task(
        send_welcome_email,
        db_user.email,
        db_user.first_name
    )
    
    return db_user


@router.post("/password-reset-request")
def request_password_reset(
    *,
    db: Session = Depends(get_db),
    email: EmailStr,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Request a password reset
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal that the user doesn't exist
        return {"message": "If the email exists, a password reset link will be sent"}
    
    # Generate password reset token
    password_reset_token = create_access_token(
        subject=user.email,
        expires_delta=timedelta(hours=24)
    )

    # Send password reset email in background
    # This would be implemented in a real application
    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        user.first_name,
        password_reset_token
    )
    
    return {"message": "If the email exists, a password reset link will be sent"}


@router.post("/reset-password")
def reset_password(
    *,
    db: Session = Depends(get_db),
    token: str,
    new_password: str
) -> Dict[str, str]:
    """
    Reset password using token
    """
    # Verify token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = TokenPayload(**payload)
        
        # Use timezone-aware comparison
        if datetime.fromtimestamp(token_data.exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token has expired"
            )
        
        email = token_data.sub
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    
    return {"message": "Password updated successfully"}
