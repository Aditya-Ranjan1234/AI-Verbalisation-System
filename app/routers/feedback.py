"""
Feedback Router
Manual override and thumbs up/down endpoints (analyst only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from .. import schemas, models, auth


router = APIRouter(prefix="/feedback", tags=["Feedback & Manual Override"])


@router.post("/", response_model=schemas.FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: schemas.FeedbackCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback on a verbalized trip
    
    **Requires:** Analyst or Admin role
    
    **Request Body:**
    - trip_id: Trip identifier
    - verbal_id: Verbalized trip identifier (optional)
    - rating: Rating 0-5 or binary thumbs up/down (1/0)
    - corrected_text: Corrected narrative text (optional)
    - notes: Analyst notes (optional)
    
    **Returns:**
    - Created feedback entry
    
    **Use Cases:**
    - Thumbs up/down on AI-generated narratives
    - Provide corrected text for model improvement
    - Add analytical notes for quality assurance
    
    **Errors:**
    - 401: Not authenticated
    - 403: Insufficient permissions (requires analyst role)
    - 404: Trip or verbalized trip not found
    """
    # Verify trip exists
    result = await db.execute(
        select(models.TripData).where(models.TripData.trip_id == feedback_data.trip_id)
    )
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {feedback_data.trip_id} not found"
        )
    
    # Verify verbal trip if provided
    if feedback_data.verbal_id:
        result = await db.execute(
            select(models.VerbalizedTrip).where(
                models.VerbalizedTrip.verbal_id == feedback_data.verbal_id
            )
        )
        verbal_trip = result.scalar_one_or_none()
        
        if not verbal_trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verbalized trip {feedback_data.verbal_id} not found"
            )
        
        if verbal_trip.trip_id != feedback_data.trip_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verbal trip does not belong to the specified trip"
            )
    
    # Create feedback
    db_feedback = models.Feedback(
        trip_id=feedback_data.trip_id,
        verbal_id=feedback_data.verbal_id,
        analyst_id=current_user.user_id,
        rating=feedback_data.rating,
        corrected_text=feedback_data.corrected_text,
        notes=feedback_data.notes
    )
    
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)
    
    return db_feedback


@router.get("/trip/{trip_id}", response_model=List[schemas.FeedbackResponse])
async def get_trip_feedback(
    trip_id: int,
    current_user: models.User = Depends(auth.require_role(models.UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all feedback for a specific trip
    
    **Requires:** Analyst or Admin role
    
    **Path Parameters:**
    - trip_id: Trip identifier
    
    **Returns:**
    - List of all feedback entries for the trip
    
    **Errors:**
    - 401: Not authenticated
    - 403: Insufficient permissions
    - 404: Trip not found
    """
    # Verify trip exists
    result = await db.execute(
        select(models.TripData).where(models.TripData.trip_id == trip_id)
    )
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found"
        )
    
    # Get all feedback
    result = await db.execute(
        select(models.Feedback).where(models.Feedback.trip_id == trip_id)
    )
    feedbacks = result.scalars().all()
    
    return feedbacks


@router.put("/{feedback_id}", response_model=schemas.FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback_data: schemas.FeedbackCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db)
):
    """
    Update existing feedback
    
    **Requires:** Analyst or Admin role
    
    **Path Parameters:**
    - feedback_id: Feedback identifier
    
    **Request Body:**
    - Same as create feedback
    
    **Returns:**
    - Updated feedback entry
    
    **Authorization:**
    - Analysts can update their own feedback
    - Admins can update any feedback
    
    **Errors:**
    - 401: Not authenticated
    - 403: Insufficient permissions
    - 404: Feedback not found
    """
    result = await db.execute(
        select(models.Feedback).where(models.Feedback.feedback_id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback {feedback_id} not found"
        )
    
    # Authorization: analysts can only update their own feedback
    if current_user.role == models.UserRole.ANALYST and feedback.analyst_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own feedback"
        )
    
    # Update fields
    feedback.trip_id = feedback_data.trip_id
    feedback.verbal_id = feedback_data.verbal_id
    feedback.rating = feedback_data.rating
    feedback.corrected_text = feedback_data.corrected_text
    feedback.notes = feedback_data.notes
    
    await db.commit()
    await db.refresh(feedback)
    
    return feedback
