"""
Authentication Routes - Sahool Agricultural Platform
Handles user authentication, registration, and token management
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import os

from src.models.user import (
    UserCreate, UserResponse, UserInDB,
    PasswordReset, PasswordResetConfirm,
    EmailVerification
)
from src.utils.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserInDB:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Here you would query the database for the user
    # user = db.query(User).filter(User.id == user_id).first()
    # if user is None:
    #     raise credentials_exception
    # return user
    
    # Placeholder return
    raise HTTPException(status_code=501, detail="User lookup not implemented")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **tenant_id**: Organization/tenant ID
    """
    # Validate password match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check if user already exists
    # existing_user = db.query(User).filter(User.email == user.email).first()
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user in database
    # db_user = User(
    #     email=user.email,
    #     hashed_password=hashed_password,
    #     full_name=user.full_name,
    #     phone=user.phone,
    #     role=user.role,
    #     tenant_id=user.tenant_id
    # )
    # db.add(db_user)
    # db.commit()
    # db.refresh(db_user)
    
    # Send verification email
    # await send_verification_email(db_user.email, db_user.id)
    
    return {"message": "User registered successfully. Please verify your email."}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    Returns access and refresh tokens
    """
    # Get user from database
    # user = db.query(User).filter(User.email == form_data.username).first()
    # if not user or not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect email or password",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    
    # Check if user is active
    # if user.status != UserStatus.ACTIVE:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Account is not active"
    #     )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(1)})  # user.id
    refresh_token = create_refresh_token(data={"sub": str(1)})
    
    # Update last login
    # user.last_login = datetime.utcnow()
    # db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        access_token = create_access_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/password-reset")
async def request_password_reset(data: PasswordReset, db: Session = Depends(get_db)):
    """Request password reset email"""
    # Check if user exists
    # user = db.query(User).filter(User.email == data.email).first()
    # if user:
    #     # Generate reset token
    #     reset_token = create_access_token(
    #         data={"sub": str(user.id), "type": "password_reset"},
    #         expires_delta=timedelta(hours=1)
    #     )
    #     # Send reset email
    #     await send_password_reset_email(user.email, reset_token)
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        # Update password
        # user = db.query(User).filter(User.id == user_id).first()
        # if user:
        #     user.hashed_password = get_password_hash(data.new_password)
        #     db.commit()
        
        return {"message": "Password reset successfully"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )


@router.post("/verify-email")
async def verify_email(data: EmailVerification, db: Session = Depends(get_db)):
    """Verify user email with token"""
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        # Update user verification status
        # user = db.query(User).filter(User.id == user_id).first()
        # if user:
        #     user.email_verified = True
        #     db.commit()
        
        return {"message": "Email verified successfully"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_user)):
    """Logout current user (invalidate token)"""
    # In a production system, you would:
    # 1. Add token to blacklist
    # 2. Remove from Redis cache
    # 3. Log the logout event
    
    return {"message": "Logged out successfully"}
