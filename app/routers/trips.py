"""
Trip Management Router
Endpoints for creating, retrieving, searching, and deleting trips
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point

from ..database import get_db
from .. import schemas, models, auth


router = APIRouter(prefix="/trips", tags=["Trip Management"])


def create_point_wkt(latitude: float, longitude: float) -> str:
    """Convert lat/lon to WKT POINT for PostGIS"""
    return f'POINT({longitude} {latitude})'


@router.post("/", response_model=schemas.TripDataResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: schemas.TripDataCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new trip with route points
    
    **Request Body:**
    - start_lat, start_lon: Starting coordinates
    - end_lat, end_lon: Ending coordinates
    - start_time, end_time: Timestamps (end_time must be after start_time)
    - route_points: List of intermediate GPS points with timestamps in sequence
    
    **Returns:**
    - Created trip with all route points
    
    **Validation:**
    - Coordinates must be valid (lat: -90 to 90, lon: -180 to 180)
    - end_time must be after start_time
    - Route points must be in chronological order
    - Route point sequences must be unique
    
    **Errors:**
    - 401: Not authenticated
    - 422: Validation error
    """
    # Create trip
    db_trip = models.TripData(
        user_id=current_user.user_id,
        start_location=create_point_wkt(trip_data.start_lat, trip_data.start_lon),
        start_time=trip_data.start_time,
        end_location=create_point_wkt(trip_data.end_lat, trip_data.end_lon),
        end_time=trip_data.end_time
    )
    
    db.add(db_trip)
    await db.flush()  # Get the trip_id
    
    # Create route points
    route_points = []
    for rp in trip_data.route_points:
        db_route_point = models.RoutePoint(
            trip_id=db_trip.trip_id,
            location=create_point_wkt(rp.latitude, rp.longitude),
            timestamp=rp.timestamp,
            sequence=rp.sequence,
            speed_kmh=rp.speed_kmh,
            altitude_m=rp.altitude_m
        )
        route_points.append(db_route_point)
        db.add(db_route_point)
    
    await db.commit()
    await db.refresh(db_trip)
    
    # Format response
    return schemas.TripDataResponse(
        trip_id=db_trip.trip_id,
        user_id=db_trip.user_id,
        start_lat=trip_data.start_lat,
        start_lon=trip_data.start_lon,
        end_lat=trip_data.end_lat,
        end_lon=trip_data.end_lon,
        start_time=db_trip.start_time,
        end_time=db_trip.end_time,
        created_at=db_trip.created_at,
        route_points=[]
    )


@router.get("/{trip_id}", response_model=schemas.TripDataResponse)
async def get_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific trip by ID
    
    **Path Parameters:**
    - trip_id: Trip identifier
    
    **Returns:**
    - Trip details with route points and verbalized summary (if available)
    
    **Errors:**
    - 401: Not authenticated
    - 404: Trip not found
    - 403: Unauthorized (can only access own trips, unless admin/analyst)
    """
    # Query trip with relationships
    result = await db.execute(
        select(models.TripData).where(models.TripData.trip_id == trip_id)
    )
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found"
        )
    
    # Authorization check: users can only see their own trips
    if current_user.role == models.UserRole.USER and trip.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this trip"
        )
    
    # Extract coordinates from PostGIS Geography
    # For simplicity, we'll store the original coordinates
    # In production, you'd parse the WKT or use ST_X/ST_Y functions
    
    return schemas.TripDataResponse(
        trip_id=trip.trip_id,
        user_id=trip.user_id,
        start_lat=0.0,  # TODO: Extract from PostGIS
        start_lon=0.0,
        end_lat=0.0,
        end_lon=0.0,
        start_time=trip.start_time,
        end_time=trip.end_time,
        created_at=trip.created_at,
        route_points=[],
        verbalized_text=None
    )


@router.get("/", response_model=List[schemas.TripDataResponse])
async def search_trips(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin/analyst only)"),
    limit: int = Query(100, le=1000, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search trips by date range and user
    
    **Query Parameters:**
    - start_date: Filter trips after this date
    - end_date: Filter trips before this date
    - user_id: Filter by user (requires analyst/admin role)
    - limit: Maximum results (default 100, max 1000)
    - offset: Pagination offset
    
    **Returns:**
    - List of trips matching the criteria
    
    **Authorization:**
    - Regular users can only search their own trips
    - Analysts and admins can search all users' trips
    
    **Errors:**
    - 401: Not authenticated
    - 403: Unauthorized to filter by other users
    """
    # Build query
    query = select(models.TripData)
    
    # Apply filters
    filters = []
    
    if start_date:
        filters.append(models.TripData.start_time >= start_date)
    
    if end_date:
        filters.append(models.TripData.end_time <= end_date)
    
    # User filter with authorization
    if user_id:
        if current_user.role == models.UserRole.USER and user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot search other users' trips"
            )
        filters.append(models.TripData.user_id == user_id)
    else:
        # Regular users can only see their own trips
        if current_user.role == models.UserRole.USER:
            filters.append(models.TripData.user_id == current_user.user_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    trips = result.scalars().all()
    
    # Format response
    return [
        schemas.TripDataResponse(
            trip_id=trip.trip_id,
            user_id=trip.user_id,
            start_lat=0.0,  # TODO: Extract from PostGIS
            start_lon=0.0,
            end_lat=0.0,
            end_lon=0.0,
            start_time=trip.start_time,
            end_time=trip.end_time,
            created_at=trip.created_at,
            route_points=[],
            verbalized_text=None
        )
        for trip in trips
    ]


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a trip
    
    **Path Parameters:**
    - trip_id: Trip identifier
    
    **Authorization:**
    - Users can delete their own trips
    - Admins can delete any trip
    
    **Errors:**
    - 401: Not authenticated
    - 403: Unauthorized
    - 404: Trip not found
    """
    # Get trip
    result = await db.execute(
        select(models.TripData).where(models.TripData.trip_id == trip_id)
    )
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found"
        )
    
    # Authorization check
    if current_user.role != models.UserRole.ADMIN and trip.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this trip"
        )
    
    # Delete trip (cascade will delete route points)
    await db.delete(trip)
    await db.commit()
    
    return None
