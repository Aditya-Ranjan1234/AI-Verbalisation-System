"""
Configuration Management Router
Endpoints for zones and regions (analyst/admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from .. import schemas, models, auth


router = APIRouter(prefix="/config", tags=["Configuration"])


def polygon_to_wkt(coordinates: List[List[float]]) -> str:
    """Convert coordinate list to WKT POLYGON"""
    points = ", ".join([f"{lon} {lat}" for lon, lat in coordinates])
    return f'POLYGON(({points}))'


@router.post("/zones", response_model=schemas.ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    zone_data: schemas.ZoneCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new geographic zone
    
    **Requires:** Analyst or Admin role
    
    **Request Body:**
    - name: Unique zone name
    - boundary: Polygon coordinates [[lon, lat], ...] (auto-closes if not closed)
    - description: Optional description
    
    **Returns:**
    - Created zone information
    
    **Errors:**
    - 401: Not authenticated
    - 403: Insufficient permissions
    - 400: Zone name already exists
    - 422: Invalid polygon
    """
    # Check if zone name exists
    result = await db.execute(
        select(models.Zone).where(models.Zone.name == zone_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone '{zone_data.name}' already exists"
        )
    
    # Create zone
    db_zone = models.Zone(
        name=zone_data.name,
        boundary=polygon_to_wkt(zone_data.boundary),
        description=zone_data.description
    )
    
    db.add(db_zone)
    await db.commit()
    await db.refresh(db_zone)
    
    return db_zone


@router.get("/zones", response_model=List[schemas.ZoneResponse])
async def list_zones(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all zones
    
    **Requires:** Valid authentication
    
    **Returns:**
    - List of all configured zones
    """
    result = await db.execute(select(models.Zone))
    zones = result.scalars().all()
    
    return zones


@router.put("/zones/{zone_id}", response_model=schemas.ZoneResponse)
async def update_zone(
    zone_id: int,
    zone_data: schemas.ZoneCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a zone
    
    **Requires:** Analyst or Admin role
    
    **Path Parameters:**
    - zone_id: Zone identifier
    
    **Request Body:**
    - Same as create zone
    
    **Returns:**
    - Updated zone information
    
    **Errors:**
    - 401: Not authenticated
    - 403: Insufficient permissions
    - 404: Zone not found
    """
    result = await db.execute(
        select(models.Zone).where(models.Zone.zone_id == zone_id)
    )
    zone = result.scalar_one_or_none()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )
    
    # Update fields
    zone.name = zone_data.name
    zone.boundary = polygon_to_wkt(zone_data.boundary)
    zone.description = zone_data.description
    
    await db.commit()
    await db.refresh(zone)
    
    return zone


@router.post("/regions", response_model=schemas.RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    region_data: schemas.RegionCreate,
    current_user: models.User = Depends(auth.require_role(models.UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new region with associated zones
    
    **Requires:** Analyst or Admin role
    
    **Request Body:**
    - name: Unique region name
    - description: Optional description
    - zone_ids: List of zone IDs to include in this region
    
    **Returns:**
    - Created region with zones
    
    **Errors:**
    - 401: Not authenticated
    - 403: Insufficient permissions
    - 400: Region name already exists or invalid zone IDs
    """
    # Check if region exists
    result = await db.execute(
        select(models.Region).where(models.Region.name == region_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Region '{region_data.name}' already exists"
        )
    
    # Verify all zones exist
    if region_data.zone_ids:
        result = await db.execute(
            select(models.Zone).where(models.Zone.zone_id.in_(region_data.zone_ids))
        )
        zones = result.scalars().all()
        
        if len(zones) != len(region_data.zone_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more zone IDs are invalid"
            )
    
    # Create region
    db_region = models.Region(
        name=region_data.name,
        description=region_data.description
    )
    
    db.add(db_region)
    await db.flush()
    
    # Create region-zone mappings
    for zone_id in region_data.zone_ids:
        mapping = models.RegionZone(
            region_id=db_region.region_id,
            zone_id=zone_id
        )
        db.add(mapping)
    
    await db.commit()
    
    # Reload with zones for response
    stmt = select(models.Region).options(
        selectinload(models.Region.zones).selectinload(models.RegionZone.zone)
    ).where(models.Region.region_id == db_region.region_id)
    
    result = await db.execute(stmt)
    db_region = result.scalars().first()
    
    # Manually construct response to handle association object
    return schemas.RegionResponse(
        region_id=db_region.region_id,
        name=db_region.name,
        description=db_region.description,
        created_at=db_region.created_at,
        zones=[rz.zone for rz in db_region.zones]
    )


@router.get("/regions", response_model=List[schemas.RegionResponse])
async def list_regions(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all regions
    
    **Requires:** Valid authentication
    
    **Returns:**
    - List of all configured regions with their zones
    """
    stmt = select(models.Region).options(
        selectinload(models.Region.zones).selectinload(models.RegionZone.zone)
    )
    result = await db.execute(stmt)
    regions = result.scalars().all()
    
    return [
        schemas.RegionResponse(
            region_id=r.region_id,
            name=r.name,
            description=r.description,
            created_at=r.created_at,
            zones=[rz.zone for rz in r.zones]
        )
        for r in regions
    ]
