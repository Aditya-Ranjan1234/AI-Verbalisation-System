"""
Pydantic Validation Schemas
Request/Response models with custom validators
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============= Authentication Schemas =============

class UserRole(str, Enum):
    """User roles matching database enum"""
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """User registration request"""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER


class UserResponse(UserBase):
    """User response (public)"""
    user_id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token payload"""
    username: Optional[str] = None
    user_id: Optional[int] = None


# ============= Geospatial Schemas =============

class CoordinateBase(BaseModel):
    """Base coordinate validation"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    
    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        """Ensure latitude is within valid range"""
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        """Ensure longitude is within valid range"""
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v


# ============= Trip Data Schemas =============

class RoutePointCreate(CoordinateBase):
    """Route point creation request"""
    timestamp: datetime
    sequence: int = Field(..., ge=1, description="Sequence order of point in route")
    speed_kmh: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    altitude_m: Optional[float] = Field(None, description="Altitude in meters")


class RoutePointResponse(RoutePointCreate):
    """Route point response"""
    point_id: int
    trip_id: int
    
    class Config:
        from_attributes = True


class TripDataCreate(BaseModel):
    """Trip creation request"""
    start_lat: float = Field(..., ge=-90, le=90)
    start_lon: float = Field(..., ge=-180, le=180)
    end_lat: float = Field(..., ge=-90, le=90)
    end_lon: float = Field(..., ge=-180, le=180)
    
    start_time: datetime
    end_time: datetime
    
    route_points: List[RoutePointCreate] = Field(default_factory=list)
    
    @field_validator('start_lat', 'end_lat')
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude range"""
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @field_validator('start_lon', 'end_lon')
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude range"""
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v
    
    @model_validator(mode='after')
    def validate_timestamps(self):
        """Ensure end_time is after start_time"""
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self
    
    @model_validator(mode='after')
    def validate_route_points_sequence(self):
        """Validate route points are in sequence"""
        if self.route_points:
            sequences = [rp.sequence for rp in self.route_points]
            if len(sequences) != len(set(sequences)):
                raise ValueError('Route point sequences must be unique')
            
            # Ensure timestamps are chronological
            timestamps = [rp.timestamp for rp in self.route_points]
            if timestamps != sorted(timestamps):
                raise ValueError('Route point timestamps must be in chronological order')
        
        return self


class TripDataResponse(BaseModel):
    """Trip response with all related data"""
    trip_id: int
    user_id: int
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    start_time: datetime
    end_time: datetime
    created_at: datetime
    
    route_points: List[RoutePointResponse] = []
    verbalized_text: Optional[str] = None
    
    class Config:
        from_attributes = True


class TripSearchParams(BaseModel):
    """Trip search query parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


# ============= Location Schemas =============

class LocationCreate(CoordinateBase):
    """Location creation request"""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None


class LocationResponse(LocationCreate):
    """Location response"""
    loc_id: int
    geocoded_at: datetime
    geocoding_source: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============= Verbalization Schemas =============

class VerbalizedTripCreate(BaseModel):
    """Request to generate verbal trip"""
    trip_id: int
    model_preference: str = Field(default="gemini", description="LLM model to use")
    
    model_config = {"protected_namespaces": ()}


class VerbalizedTripResponse(BaseModel):
    """Verbalized trip response"""
    verbal_id: int
    trip_id: int
    narrative_text: str
    model_used: str
    generated_at: datetime
    processing_time_ms: Optional[int] = None
    
    model_config = {"protected_namespaces": (), "from_attributes": True}


# ============= Configuration Schemas =============

class ZoneCreate(BaseModel):
    """Zone creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    boundary: List[List[float]] = Field(..., description="Polygon coordinates [[lon1, lat1], [lon2, lat2], ...]")
    description: Optional[str] = None
    
    @field_validator('boundary')
    @classmethod
    def validate_polygon(cls, v):
        """Validate polygon has at least 3 points and forms closed loop"""
        if len(v) < 3:
            raise ValueError('Polygon must have at least 3 points')
        
        # Check if polygon is closed (first point == last point)
        if v[0] != v[-1]:
            # Auto-close the polygon
            v.append(v[0])
        
        # Validate each coordinate
        for coord in v:
            if len(coord) != 2:
                raise ValueError('Each coordinate must be [longitude, latitude]')
            lon, lat = coord
            if not -180 <= lon <= 180:
                raise ValueError(f'Invalid longitude: {lon}')
            if not -90 <= lat <= 90:
                raise ValueError(f'Invalid latitude: {lat}')
        
        return v


class ZoneResponse(BaseModel):
    """Zone response"""
    zone_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RegionCreate(BaseModel):
    """Region creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    zone_ids: List[int] = Field(default_factory=list)


class RegionResponse(BaseModel):
    """Region response"""
    region_id: int
    name: str
    description: Optional[str] = None
    zones: List[ZoneResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Feedback Schemas =============

class FeedbackCreate(BaseModel):
    """Feedback creation request"""
    trip_id: int
    verbal_id: Optional[int] = None
    rating: int = Field(..., ge=0, le=5, description="Rating 0-5 or binary 0/1")
    corrected_text: Optional[str] = None
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response"""
    feedback_id: int
    trip_id: int
    verbal_id: Optional[int] = None
    analyst_id: int
    rating: int
    corrected_text: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Error Responses =============

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Aliases for compatibility with Routers
TripCreate = TripDataCreate
TripResponse = TripDataResponse
TripDetail = TripDataResponse
