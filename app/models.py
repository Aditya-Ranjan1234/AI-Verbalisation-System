"""
Database Models (BCNF Normalized Schema)
SQLAlchemy ORM models for PostgreSQL with PostGIS support
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime
import enum
from .database import Base


class UserRole(str, enum.Enum):
    """User roles for authorization"""
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"


class User(Base):
    """User authentication and authorization"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    trips = relationship("TripData", back_populates="user", cascade="all, delete-orphan")
    api_logs = relationship("APIUsageLog", back_populates="user", cascade="all, delete-orphan")


from geoalchemy2.shape import to_shape

# ... (imports)

class TripData(Base):
    """Trip Data - Primary trip information (BCNF)"""
    __tablename__ = "trip_data"
    
    trip_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Start location (PostGIS Geography type for lat/lon)
    start_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    
    # End location
    end_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    end_time = Column(DateTime, nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="trips")
    route_points = relationship("RoutePoint", back_populates="trip", cascade="all, delete-orphan", order_by="RoutePoint.sequence")
    verbalized_trips = relationship("VerbalizedTrip", back_populates="trip", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="trip", cascade="all, delete-orphan")

    @property
    def start_lat(self):
        return to_shape(self.start_location).y

    @property
    def start_lon(self):
        return to_shape(self.start_location).x

    @property
    def end_lat(self):
        return to_shape(self.end_location).y

    @property
    def end_lon(self):
        return to_shape(self.end_location).x


class RoutePoint(Base):
    """Route Points - Individual GPS points along the trip (BCNF)"""
    __tablename__ = "route_points"
    
    point_id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trip_data.trip_id"), nullable=False)
    
    # Location
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    sequence = Column(Integer, nullable=False)  # Order of points in route
    
    # Optional: speed, altitude, accuracy
    speed_kmh = Column(Float, nullable=True)
    altitude_m = Column(Float, nullable=True)
    
    # Relationships
    trip = relationship("TripData", back_populates="route_points")
    
    @property
    def latitude(self):
        return to_shape(self.location).y

    @property
    def longitude(self):
        return to_shape(self.location).x
    
    # Composite index for efficient querying
    __table_args__ = (
        {'extend_existing': True}
    )


class Location(Base):
    """Locations - Geocoded address information (BCNF)"""
    __tablename__ = "locations"
    
    loc_id = Column(Integer, primary_key=True, index=True)
    
    # Coordinates
    coordinates = Column(Geography(geometry_type='POINT', srid=4326), nullable=False, unique=True)
    
    # Reverse geocoded information
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, index=True)
    postal_code = Column(String(20), nullable=True)
    
    # Metadata
    geocoded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    geocoding_source = Column(String(50), nullable=True)  # 'HERE', 'OSM', etc.


class VerbalizedTrip(Base):
    """Verbalized Trips - AI-generated narratives (BCNF)"""
    __tablename__ = "verbalized_trips"
    
    verbal_id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trip_data.trip_id"), nullable=False)
    
    # AI-generated content
    narrative_text = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=False)  # 'Gemini', 'LLaMA', etc.
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    trip = relationship("TripData", back_populates="verbalized_trips")


class APIUsageLog(Base):
    """API Usage Logs - Track all API calls (BCNF)"""
    __tablename__ = "api_usage_logs"
    
    api_log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # Request information
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    status_code = Column(Integer, nullable=False)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Optional: IP address, user agent
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_logs")


class Zone(Base):
    """Zones - Geographic zones for analytics (BCNF)"""
    __tablename__ = "zones"
    
    zone_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    
    # GeoJSON polygon
    boundary = Column(Geography(geometry_type='POLYGON', srid=4326), nullable=False)
    
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    regions = relationship("RegionZone", back_populates="zone", cascade="all, delete-orphan")


class Region(Base):
    """Regions - Logical grouping of zones (BCNF)"""
    __tablename__ = "regions"
    
    region_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    zones = relationship("RegionZone", back_populates="region", cascade="all, delete-orphan")


class RegionZone(Base):
    """Region-Zone mapping - Many-to-many relationship (BCNF)"""
    __tablename__ = "region_zones"
    
    region_zone_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.zone_id"), nullable=False)
    
    # Relationships
    region = relationship("Region", back_populates="zones")
    zone = relationship("Zone", back_populates="regions")


class Feedback(Base):
    """Feedback - Manual corrections from analysts (BCNF)"""
    __tablename__ = "feedbacks"
    
    feedback_id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trip_data.trip_id"), nullable=False)
    verbal_id = Column(Integer, ForeignKey("verbalized_trips.verbal_id"), nullable=True)
    analyst_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Feedback details
    rating = Column(Integer, nullable=False)  # 1-5 or thumbs up/down (1/0)
    corrected_text = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    trip = relationship("TripData", back_populates="feedbacks")
    verbal_trip = relationship("VerbalizedTrip")
    analyst = relationship("User")
