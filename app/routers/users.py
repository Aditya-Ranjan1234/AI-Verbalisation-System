"""
User Management Router
"""
from fastapi import APIRouter, Depends
from .. import schemas, models, auth

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Get current user information
    """
    return current_user
