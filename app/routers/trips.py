from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from ..database import get_db, mongodb
from ..models import TripData as Trip, User, UserRole, RoutePoint
from ..schemas import TripCreate, TripResponse, TripDetail
from ..auth import get_current_user, require_role, get_current_active_user
from ..services import GeocodingService, LLMService

router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)

@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip: TripCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new trip.
    """
    # Create trip object
    new_trip = Trip(
        user_id=current_user.user_id,
        start_location=f"POINT({trip.start_lon} {trip.start_lat})",
        end_location=f"POINT({trip.end_lon} {trip.end_lat})",
        start_time=trip.start_time,
        end_time=trip.end_time
    )
    
    db.add(new_trip)
    await db.flush()  # Get ID without committing yet
    
    # Add route points if provided
    if trip.route_points:
        sequence = 1
        for point in trip.route_points:
            route_point = RoutePoint(
                trip_id=new_trip.trip_id,
                location=f"POINT({point.longitude} {point.latitude})",
                timestamp=point.timestamp,
                sequence=sequence
            )
            db.add(route_point)
            sequence += 1
            
    await db.commit()
    await db.refresh(new_trip)
    
    return new_trip

@router.get("/", response_model=List[TripResponse])
async def list_trips(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """
    List user's trips.
    """
    query = select(Trip).where(Trip.user_id == current_user.user_id).offset(skip).limit(limit)
    result = await db.execute(query)
    trips = result.scalars().all()
    return trips

@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip(
    trip_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """
    Get trip details including route points.
    """
    query = select(Trip).options(selectinload(Trip.route_points)).where(Trip.trip_id == trip_id)
    
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        query = query.where(Trip.user_id == current_user.user_id)
        
    result = await db.execute(query)
    trip = result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    return trip

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a trip.
    """
    # Check if trip exists and belongs to user
    query = select(Trip).where(Trip.trip_id == trip_id)
    if current_user.role != UserRole.ADMIN:
        query = query.where(Trip.user_id == current_user.user_id)
        
    result = await db.execute(query)
    trip = result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    await db.delete(trip)
    await db.commit()

@router.post("/{trip_id}/verbalize", status_code=status.HTTP_200_OK)
async def verbalize_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a story for valuable trip data using AI.
    """
    # 1. Fetch Trip Data
    query = select(Trip).where(Trip.trip_id == trip_id)
    if current_user.role != UserRole.ADMIN:
        query = query.where(Trip.user_id == current_user.user_id)
        
    result = await db.execute(query)
    trip = result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Check if already verbalized in MongoDB
    try:
        existing = await mongodb.verbalizations.find_one({"trip_id": trip_id})
        if existing:
            return {"story": existing["story"], "cached": True}
    except Exception as e:
        print(f"MongoDB check failed: {e}")

    # 2. Geocode Locations
    start_address = await GeocodingService.get_address(trip.start_lat, trip.start_lon)
    end_address = await GeocodingService.get_address(trip.end_lat, trip.end_lon)
    
    # 3. Prepare Data for LLM
    duration = trip.end_time - trip.start_time
    trip_data = {
        "start_time": trip.start_time.strftime("%Y-%m-%d %H:%M"),
        "end_time": trip.end_time.strftime("%Y-%m-%d %H:%M"),
        "duration": str(duration)
    }
    
    # 4. Generate Story
    story = await LLMService.generate_trip_story(trip_data, start_address, end_address)
    
    # 5. Save to MongoDB
    doc = {
        "trip_id": trip_id,
        "user_id": current_user.user_id,
        "start_address": start_address,
        "end_address": end_address,
        "story": story,
        "generated_at": datetime.utcnow()
    }
    
    try:
        await mongodb.verbalizations.insert_one(doc)
    except Exception as e:
        print(f"MongoDB insert failed: {e}")
        
    return {
        "start_address": start_address, 
        "end_address": end_address, 
        "story": story
    }
