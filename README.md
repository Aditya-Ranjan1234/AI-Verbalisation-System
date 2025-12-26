# AI-Based Trip Data Verbalization System

A comprehensive system that transforms GPS trip data into human-readable narratives using AI, featuring BCNF-normalized database schema, OAuth2 authentication, and geospatial validation.

## 🚀 Features

- **Trip Management**: Create, retrieve, search, and delete GPS trips
- **Geospatial Validation**: Automatic validation of coordinates using PostGIS
- **Security**: OAuth2 with JWT authentication and role-based access control
- **Configuration**: Define geographic zones and regions for analytics
- **Feedback System**: Manual override and quality assurance for AI outputs
- **API Documentation**: Interactive Swagger UI and ReDoc

## 📋 Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+** with PostGIS extension
- **MongoDB 4.4+** (for AI metadata)

## 🛠️ Installation

### 1. Clone and Setup Virtual Environment

```bash
cd "d:/5th Sem/dbms"
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
copy .env.example .env
```

Edit `.env` and configure:

```env
# Database URLs
DATABASE_URL=postgresql://username:password@localhost:5432/trip_verbalization
MONGODB_URL=mongodb://localhost:27017/trip_verbalization

# Generate JWT secret with: openssl rand -hex 32
JWT_SECRET_KEY=your_generated_secret_key_here

# Optional: API keys for geocoding and LLM
GEOCODING_API_KEY=your_here_api_key
LLM_API_KEY=your_gemini_api_key
```

### 4. Initialize Database

Ensure PostgreSQL is running, then initialize the database:

```bash
# Create database
psql -U postgres -c "CREATE DATABASE trip_verbalization;"

# Initialize tables and create admin user
python init_db.py
```

**Default admin credentials:**
- Username: `admin`
- Password: `admin123` (⚠️ Change after first login!)

## 🏃‍♂️ Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Usage

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "email": "analyst@example.com",
    "password": "SecurePass123",
    "role": "analyst"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=analyst1&password=SecurePass123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Create a Trip

```bash
curl -X POST "http://localhost:8000/trips/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_lat": 12.9716,
    "start_lon": 77.5946,
    "end_lat": 13.0827,
    "end_lon": 80.2707,
    "start_time": "2025-12-22T08:00:00",
    "end_time": "2025-12-22T12:00:00",
    "route_points": [
      {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timestamp": "2025-12-22T08:00:00",
        "sequence": 1
      },
      {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "timestamp": "2025-12-22T12:00:00",
        "sequence": 2
      }
    ]
  }'
```

### 4. Search Trips

```bash
curl -X GET "http://localhost:8000/trips/?start_date=2025-12-20&end_date=2025-12-25" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔐 Security

### User Roles

1. **USER**: Can create and manage their own trips
2. **ANALYST**: Can manage trips, create zones/regions, and provide feedback
3. **ADMIN**: Full access to all features

### Password Requirements

- Minimum 8 characters
- Passwords are hashed using bcrypt

### JWT Tokens

- Expire after 30 minutes (configurable)
- Include in requests: `Authorization: Bearer <token>`

## 📊 Database Schema

### BCNF-Normalized Relations

- **users**: User authentication and authorization
- **trip_data**: Primary trip information
- **route_points**: GPS points along the trip route
- **locations**: Geocoded address information
- **verbalized_trips**: AI-generated narratives
- **api_usage_logs**: API call tracking
- **zones**: Geographic zones for analytics
- **regions**: Logical grouping of zones
- **feedbacks**: Manual corrections from analysts

## 🧪 Validation

### Geospatial Validation

- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees
- Polygon coordinates auto-close if not closed

### Temporal Validation

- end_time must be after start_time
- Route points must be in chronological order
- Sequence numbers must be unique

## 🐛 Troubleshooting

### PostGIS Extension Error

If you get "PostGIS extension not found":

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### AsyncPG Connection Error

If using `asyncpg`, ensure your DATABASE_URL uses `postgresql+asyncpg://`:

```python
# The app automatically handles this conversion
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### JWT Secret Key

Generate a secure secret key:

```bash
openssl rand -hex 32
```

## 📝 License

This project was developed at RV College of Engineering for the DBMS course.

## 👥 Contributors

- AI Trip Verbalization Team
- RV College of Engineering

## 📞 Support

For issues or questions, please contact the development team.
