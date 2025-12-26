# Docker Setup Guide - AI Trip Data Verbalization System

Complete guide for running the entire system using Docker and Docker Compose.

---

## 📋 Prerequisites

- **Docker Desktop** installed (https://www.docker.com/products/docker-desktop/)
- **Docker Compose** (included with Docker Desktop)
- **Python 3.9+** for running the FastAPI app

---

## 🚀 Quick Start (Docker Only)

### Step 1: Start Database Services

```powershell
# Navigate to project directory
cd "d:\5th Sem\dbms"

# Start PostgreSQL with PostGIS
docker run -d `
  --name postgis `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=trip_verbalization `
  -p 5432:5432 `
  postgis/postgis:15-3.3

# Start MongoDB
docker run -d `
  --name mongodb `
  -p 27017:27017 `
  mongo:latest
```

### Step 2: Verify Containers are Running

```powershell
docker ps
```

You should see both `postgis` and `mongodb` running.

### Step 3: Enable PostGIS Extension

```powershell
docker exec -it postgis psql -U postgres -d trip_verbalization -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

**Verify PostGIS:**
```powershell
docker exec -it postgis psql -U postgres -d trip_verbalization -c "SELECT PostGIS_Full_Version();"
```

### Step 4: Setup Python Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Environment

```powershell
# Copy example env file
copy .env.example .env
```

Edit `.env` with these Docker settings:

```env
# PostgreSQL (Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trip_verbalization

# MongoDB (Docker)
MONGODB_URL=mongodb://localhost:27017/trip_verbalization

# Generate JWT secret
JWT_SECRET_KEY=your_generated_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
APP_NAME=AI Trip Data Verbalization System
APP_VERSION=1.0.0
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Generate JWT Secret:**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 6: Initialize Database

```powershell
python init_db.py
```

**Expected Output:**
```
Initializing database...
Creating PostGIS extension...
Creating tables...
Database initialized successfully!

Creating default admin user...
Admin user created successfully!
  Username: admin
  Password: admin123
```

### Step 7: Run Application

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access the API:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐳 Using Docker Compose (Recommended)

Create `docker-compose.yml` in your project root:

```yaml
version: '3.8'

services:
  postgis:
    image: postgis/postgis:15-3.3
    container_name: trip_postgis
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: trip_verbalization
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:latest
    container_name: trip_mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  mongo_data:
```

### Using Docker Compose

```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: Deletes data!)
docker-compose down -v
```

---

## 🔧 Docker Management Commands

### Managing PostgreSQL Container

```powershell
# Start container
docker start postgis

# Stop container
docker stop postgis

# Restart container
docker restart postgis

# View logs
docker logs postgis

# Access PostgreSQL shell
docker exec -it postgis psql -U postgres -d trip_verbalization

# Backup database
docker exec postgis pg_dump -U postgres trip_verbalization > backup.sql

# Restore database
cat backup.sql | docker exec -i postgis psql -U postgres -d trip_verbalization
```

### Managing MongoDB Container

```powershell
# Start container
docker start mongodb

# Stop container
docker stop mongodb

# Access MongoDB shell
docker exec -it mongodb mongosh

# Backup database
docker exec mongodb mongodump --db trip_verbalization --out /backup
docker cp mongodb:/backup ./mongodb_backup

# Restore database
docker cp ./mongodb_backup mongodb:/backup
docker exec mongodb mongorestore --db trip_verbalization /backup/trip_verbalization
```

### Useful Docker Commands

```powershell
# List all containers
docker ps -a

# Remove stopped containers
docker rm postgis mongodb

# View container resource usage
docker stats

# Inspect container
docker inspect postgis
```

---

## 🔄 Daily Workflow (Docker)

### Starting Development Session

```powershell
# 1. Navigate to project
cd "d:\5th Sem\dbms"

# 2. Start Docker containers (if not running)
docker start postgis mongodb
# OR with docker-compose:
docker-compose up -d

# 3. Activate Python environment
venv\Scripts\activate

# 4. Run application
uvicorn app.main:app --reload
```

### Stopping Development Session

```powershell
# 1. Stop application (Ctrl+C)

# 2. Deactivate Python environment
deactivate

# 3. Stop Docker containers (optional)
docker stop postgis mongodb
# OR with docker-compose:
docker-compose down
```

---

## 🐛 Troubleshooting Docker

### Issue: "port is already allocated"

**If port 5432 is in use:**
```powershell
# Find what's using the port
netstat -ano | findstr :5432

# Kill the process or use different port
docker run -d --name postgis -e POSTGRES_PASSWORD=postgres -p 5433:5432 postgis/postgis:15-3.3

# Update .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/trip_verbalization
```

### Issue: "Container already exists"

```powershell
# Remove existing container
docker rm -f postgis mongodb

# Recreate
docker run -d --name postgis -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgis/postgis:15-3.3
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

### Issue: "PostGIS extension not found"

```powershell
# Ensure you're using the PostGIS image, not plain postgres
docker ps

# Should show: postgis/postgis:15-3.3 (not postgres:15)

# If using wrong image, recreate:
docker rm -f postgis
docker run -d --name postgis -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=trip_verbalization -p 5432:5432 postgis/postgis:15-3.3

# Enable extension
docker exec -it postgis psql -U postgres -d trip_verbalization -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Issue: Database connection refused

```powershell
# Check if containers are running
docker ps

# Check container logs
docker logs postgis
docker logs mongodb

# Restart containers
docker restart postgis mongodb
```

### Issue: "init_db.py" fails

**Pydantic warnings:** Already fixed in code, safe to ignore or update schemas.

**SQLAlchemy error:** Already fixed by using `text()` wrapper.

**Connection error:**
```powershell
# Verify .env file has correct Docker settings
# DATABASE_URL should be localhost, not 127.0.0.1
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trip_verbalization
```

---

## 🧪 Testing Database Connections

### Test PostgreSQL

```powershell
# Inside container
docker exec -it postgis psql -U postgres -d trip_verbalization

# Run SQL
\dt  # List tables
SELECT * FROM users LIMIT 5;
\q   # Quit
```

### Test MongoDB

```powershell
# Inside container
docker exec -it mongodb mongosh

# Run commands
use trip_verbalization
show collections
db.test.insertOne({test: "hello"})
db.test.find()
exit
```

### Test from Python

Create `test_connection.py`:

```python
import asyncio
from app.database import engine, mongodb

async def test_connections():
    # Test PostgreSQL
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("PostgreSQL:", result.scalar())
    
    # Test MongoDB
    result = await mongodb.test.insert_one({"test": "connection"})
    print("MongoDB:", result.inserted_id)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connections())
```

Run:
```powershell
python test_connection.py
```

---

## 🗄️ Data Persistence

Docker containers use **volumes** to persist data:

```powershell
# List volumes
docker volume ls

# Inspect volume
docker volume inspect <volume_name>

# Remove volume (WARNING: Deletes all data!)
docker volume rm <volume_name>
```

**With Docker Compose:** Volumes are defined in `docker-compose.yml`
- `postgres_data` - PostgreSQL data
- `mongo_data` - MongoDB data

---

## 🔄 Resetting the Database

### Quick Reset (Docker)

```powershell
# Stop containers
docker-compose down
# OR
docker stop postgis mongodb

# Remove containers and volumes
docker rm -f postgis mongodb
docker volume prune -f

# Recreate containers
docker-compose up -d
# OR
docker run -d --name postgis -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=trip_verbalization -p 5432:5432 postgis/postgis:15-3.3
docker run -d --name mongodb -p 27017:27017 mongo:latest

# Enable PostGIS
docker exec -it postgis psql -U postgres -d trip_verbalization -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Reinitialize
python init_db.py
```

---

## 📊 Monitoring Docker Containers

### Resource Usage

```powershell
# Real-time stats
docker stats

# Container details
docker inspect postgis
docker inspect mongodb
```

### Health Checks (with Docker Compose)

```powershell
# Check health status
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' trip_postgis
```

---

## ✅ Docker Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Start containers | `docker start postgis mongodb` |
| Stop containers | `docker stop postgis mongodb` |
| View running | `docker ps` |
| View all | `docker ps -a` |
| View logs | `docker logs postgis` |
| Access PostgreSQL | `docker exec -it postgis psql -U postgres -d trip_verbalization` |
| Access MongoDB | `docker exec -it mongodb mongosh` |
| Remove containers | `docker rm -f postgis mongodb` |

### Docker Compose Commands

| Task | Command |
|------|---------|
| Start all | `docker-compose up -d` |
| Stop all | `docker-compose down` |
| View status | `docker-compose ps` |
| View logs | `docker-compose logs -f` |
| Restart service | `docker-compose restart postgis` |
| Rebuild images | `docker-compose up -d --build` |

---

## 🎯 Complete First-Time Setup Checklist

- [ ] Docker Desktop installed and running
- [ ] Created `docker-compose.yml` (optional but recommended)
- [ ] Started PostgreSQL container: `docker run -d --name postgis -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=trip_verbalization -p 5432:5432 postgis/postgis:15-3.3`
- [ ] Started MongoDB container: `docker run -d --name mongodb -p 27017:27017 mongo:latest`
- [ ] Verified containers running: `docker ps`
- [ ] Enabled PostGIS: `docker exec -it postgis psql -U postgres -d trip_verbalization -c "CREATE EXTENSION IF NOT EXISTS postgis;"`
- [ ] Created Python venv: `python -m venv venv`
- [ ] Activated venv: `venv\Scripts\activate`
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Created `.env` file from `.env.example`
- [ ] Generated JWT secret and updated `.env`
- [ ] Initialized database: `python init_db.py`
- [ ] Started application: `uvicorn app.main:app --reload`
- [ ] Accessed http://localhost:8000/docs

---

## 🔗 Related Documentation

- **Main README**: [README.md](file:///d:/5th%20Sem/dbms/README.md) - API usage and features
- **General Setup**: [SETUP_GUIDE.md](file:///d:/5th%20Sem/dbms/SETUP_GUIDE.md) - All setup methods
- **Implementation Details**: [walkthrough.md](file:///C:/Users/OMEN/.gemini/antigravity/brain/4620c79b-fb59-42bd-b00c-26fb2cd23b01/walkthrough.md)

---

**Status**: ✅ Docker-ready setup complete!
