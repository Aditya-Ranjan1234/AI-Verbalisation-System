"""
Authentication Router
User registration, login, and profile endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from ..database import get_db
from ..config import settings
from .. import schemas, models, auth


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    **Request Body:**
    - username: Unique username (3-50 characters)
    - email: Valid email address
    - password: Password (minimum 8 characters)
    - role: User role (user, analyst, admin) - default: user
    
    **Returns:**
    - Created user information (excluding password)
    
    **Errors:**
    - 400: Username or email already exists
    """
    user = await auth.create_user(db, user_create)
    return user


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    User login - returns JWT access token
    
    **Form Data:**
    - username: User's username
    - password: User's password
    
    **Returns:**
    - access_token: JWT token for authentication
    - token_type: "bearer"
    
    **Usage:**
    Include the token in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Errors:**
    - 401: Invalid username or password
    """
    user = await auth.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "user_id": user.user_id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Get current user information
    
    **Requires:** Valid JWT token
    
    **Returns:**
    - User profile information
    
    **Errors:**
    - 401: Invalid or expired token
    """
    return current_user
