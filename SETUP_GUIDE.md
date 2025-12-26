# Complete Setup Guide - AI Trip Data Verbalization System

This guide covers three scenarios: **Initial Setup**, **Development Workflow**, and **Running Again**.

---

## 📋 Table of Contents

1. [Initial Setup (First Time)](#initial-setup-first-time)
2. [Development Workflow](#development-workflow)
3. [Running Again (Subsequent Sessions)](#running-again-subsequent-sessions)
4. [Troubleshooting](#troubleshooting)

---

## 🆕 Initial Setup (First Time)

Follow these steps when setting up the project for the first time.

### Step 1: Install Prerequisites

#### 1.1 Install PostgreSQL with PostGIS

**Windows:**
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer (recommended version: 15 or 16)
3. During installation:
   - Set password for `postgres` user (remember this!)
   - Port: `5432` (default)
   - Install Stack Builder when prompted
4. In Stack Builder:
   - Select "Spatial Extensions"
   - Install PostGIS 3.x

**Docker Alternative:**
```powershell
docker run --name postgis -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgis/postgis:15-3.3
```

#### 1.2 Install MongoDB

**Windows:**
1. Download from https://www.mongodb.com/try/download/community
2. Run the installer
3. Choose "Complete" installation
4. Install as Windows Service (port 27017)

**Docker Alternative:**
```powershell
docker run --name mongodb -p 27017:27017 -d mongo:latest
```

**Cloud Alternative (MongoDB Atlas):**
1. Create free account at https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string

#### 1.3 Verify Installations

```powershell
# Check PostgreSQL
psql --version

# Check MongoDB
mongosh --version

# Check Python
python --version
# Should be 3.9 or higher
```

---

### Step 2: Create and Configure Database

#### 2.1 Create PostgreSQL Database

```powershell
# Connect to PostgreSQL
psql -U postgres

# Inside psql prompt:
CREATE DATABASE trip_verbalization;
\c trip_verbalization
CREATE EXTENSION postgis;
\q
```

**Verify PostGIS:**
```powershell
psql -U postgres -d trip_verbalization -c "SELECT PostGIS_version();"
```

#### 2.2 Test MongoDB Connection

```powershell
# Using mongosh
mongosh
> use trip_verbalization
> db.test.insertOne({test: "connection"})
> db.test.find()
> exit
```

---

### Step 3: Setup Python Environment

```powershell
# Navigate to project directory
cd "d:\5th Sem\dbms"

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip (optional but recommended)
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install async PostgreSQL driver
pip install asyncpg
```

---

### Step 4: Configure Environment Variables

#### 4.1 Create .env File

```powershell
copy .env.example .env
notepad .env
```

#### 4.2 Generate JWT Secret Key

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output.

#### 4.3 Edit .env File

Update the following in `.env`:

```env
# PostgreSQL - Update password if different
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/trip_verbalization

# MongoDB - Local installation
MONGODB_URL=mongodb://localhost:27017/trip_verbalization

# MongoDB Atlas alternative
# MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/trip_verbalization

# JWT Secret - Paste the generated key here
JWT_SECRET_KEY=paste_your_generated_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs (optional, leave empty for now)
GEOCODING_API_KEY=
LLM_API_KEY=

# Application Settings
APP_NAME=AI Trip Data Verbalization System
APP_VERSION=1.0.0
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

Save and close the file.

---

### Step 5: Initialize Database

```powershell
# Make sure virtual environment is activated
# You should see (venv) in your prompt

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
  ⚠️  Please change the password after first login!
```

---

### Step 6: Run the Application

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
Starting AI Trip Data Verbalization System v1.0.0
Debug mode: True
Initializing database...
Database initialized successfully
INFO:     Application startup complete.
```

---

### Step 7: Access and Test

1. **Open API Documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

2. **Test the API:**
   - Click "Authorize" button in Swagger UI
   - Login with:
     - Username: `admin`
     - Password: `admin123`
   - Try creating a trip, searching trips, etc.

---

## 🔧 Development Workflow

### Creating New Features

#### 1. Add New Database Models

Edit `app/models.py`:
```python
class NewModel(Base):
    __tablename__ = "new_table"
    id = Column(Integer, primary_key=True)
    # ... add fields
```

#### 2. Create Validation Schemas

Edit `app/schemas.py`:
```python
class NewModelCreate(BaseModel):
    field: str
    # ... add validators
```

#### 3. Create New Router

Create `app/routers/new_feature.py`:
```python
from fastapi import APIRouter, Depends
from ..auth import get_current_active_user

router = APIRouter(prefix="/new", tags=["New Feature"])

@router.post("/")
async def create_item(...):
    pass
```

#### 4. Register Router

Edit `app/main.py`:
```python
from .routers import auth, trips, config, feedback, new_feature

app.include_router(new_feature.router)
```

#### 5. Update Database Schema

```powershell
# Drop and recreate (WARNING: Deletes all data!)
python init_db.py drop
python init_db.py

# Or use Alembic for migrations (recommended for production)
```

#### 6. Test Changes

```powershell
# Restart the server (Ctrl+C, then)
uvicorn app.main:app --reload
```

---

### Making Code Changes

The development server (`--reload` flag) automatically restarts when you save files:

1. Edit files in `app/` directory
2. Save the file
3. Server automatically reloads
4. Test changes in browser at http://localhost:8000/docs

**Files to edit:**
- **Models**: `app/models.py` (database tables)
- **Schemas**: `app/schemas.py` (validation)
- **Auth**: `app/auth.py` (authentication logic)
- **Routes**: `app/routers/*.py` (API endpoints)
- **Config**: `app/config.py` (settings)

---

### Adding New Dependencies

```powershell
# Activate virtual environment
venv\Scripts\activate

# Install new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

---

## 🔄 Running Again (Subsequent Sessions)

Use these steps every time you want to run the application after initial setup.

### Quick Start (Every Time)

```powershell
# 1. Navigate to project
cd "d:\5th Sem\dbms"

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**That's it!** Open http://localhost:8000/docs in your browser.

---

### If Database Services Aren't Running

#### Start PostgreSQL

**Windows Service:**
```powershell
# Check status
Get-Service postgresql*

# Start if needed
Start-Service postgresql-x64-15  # Adjust version number
```

**Docker:**
```powershell
docker start postgis
```

#### Start MongoDB

**Windows Service:**
```powershell
# Check status
Get-Service MongoDB

# Start if needed
Start-Service MongoDB
```

**Docker:**
```powershell
docker start mongodb
```

---

### After Pulling Code Changes

If you've pulled updates from Git:

```powershell
# 1. Activate environment
venv\Scripts\activate

# 2. Update dependencies
pip install -r requirements.txt

# 3. Check for database changes
# If models.py changed, you may need to:
python init_db.py

# 4. Run application
uvicorn app.main:app --reload
```

---

### Running Tests (Future)

```powershell
# When tests are implemented
pytest

# With coverage
pytest --cov=app tests/
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution:**
```powershell
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Issue: "Connection to database failed"

**PostgreSQL:**
```powershell
# Check if running
psql -U postgres -d trip_verbalization

# Verify .env has correct credentials
notepad .env

# Test connection
psql -U postgres -d trip_verbalization -c "SELECT 1;"
```

**MongoDB:**
```powershell
# Check if running
mongosh

# Restart service
net stop MongoDB
net start MongoDB
```

---

### Issue: "PostGIS extension not found"

**Solution:**
```powershell
psql -U postgres -d trip_verbalization
```

Inside psql:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
\dx  -- List installed extensions
\q
```

---

### Issue: "Port 8000 already in use"

**Solution:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

---

### Issue: "asyncpg module not found"

**Solution:**
```powershell
pip install asyncpg
```

---

### Issue: "JWT decode error"

**Solution:**
1. Logout from Swagger UI
2. Generate new JWT secret:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Update `.env` with new secret
4. Restart application
5. Login again

---

### Issue: "Database tables don't exist"

**Solution:**
```powershell
# Reinitialize database
python init_db.py
```

---

## 📝 Quick Reference Commands

### Daily Development

```powershell
# Start development session
cd "d:\5th Sem\dbms"
venv\Scripts\activate
uvicorn app.main:app --reload

# Stop server: Ctrl+C
# Deactivate virtual environment: deactivate
```

### Database Management

```powershell
# Connect to PostgreSQL
psql -U postgres -d trip_verbalization

# Common SQL commands
\dt              # List tables
\d table_name    # Describe table
SELECT * FROM users LIMIT 5;

# MongoDB
mongosh
> use trip_verbalization
> show collections
> db.collection_name.find()
```

### Reset Database (WARNING: Deletes all data!)

```powershell
python init_db.py drop
python init_db.py
```

---

## 🎯 Checklist for Each Scenario

### ✅ Initial Setup Checklist

- [ ] PostgreSQL installed with PostGIS
- [ ] MongoDB installed
- [ ] Database created (`trip_verbalization`)
- [ ] PostGIS extension enabled
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `asyncpg` installed
- [ ] `.env` file created and configured
- [ ] JWT secret generated
- [ ] Database initialized (`python init_db.py`)
- [ ] Application runs successfully
- [ ] Can access http://localhost:8000/docs

### ✅ Daily Development Checklist

- [ ] Navigate to project directory
- [ ] Activate virtual environment
- [ ] PostgreSQL running
- [ ] MongoDB running
- [ ] Start application (`uvicorn app.main:app --reload`)
- [ ] Access http://localhost:8000/docs

### ✅ After Pulling Changes Checklist

- [ ] Pull latest code
- [ ] Activate virtual environment
- [ ] Update dependencies (`pip install -r requirements.txt`)
- [ ] Check for model changes (reinit db if needed)
- [ ] Run application

---

## 🚀 Next Steps

Once your development environment is running:

1. **Change admin password** via Swagger UI
2. **Create test users** with different roles
3. **Test all API endpoints** interactively
4. **Integrate LLM** for trip verbalization
5. **Add geocoding service** for address resolution
6. **Build frontend** application

---

**For detailed API documentation, see:** [README.md](file:///d:/5th%20Sem/dbms/README.md)  
**For implementation details, see:** [walkthrough.md](file:///C:/Users/OMEN/.gemini/antigravity/brain/4620c79b-fb59-42bd-b00c-26fb2cd23b01/walkthrough.md)
