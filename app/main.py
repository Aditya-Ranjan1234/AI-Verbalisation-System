"""
Main FastAPI Application
Combines all routers and middleware
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime

from .config import settings
from .routers import auth, trips, config, feedback, users


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## AI-Based Trip Data Verbalization System
    
    Transform complex GPS trip data into human-readable narratives using AI.
    
    ### Features
    
    * **Trip Management**: Create, retrieve, search, and delete trips with GPS route points
    * **Geospatial Validation**: Automatic validation of coordinates and timestamps
    * **Authentication**: Secure OAuth2 with JWT tokens
    * **Role-Based Access**: User, Analyst, and Admin roles
    * **Zone Configuration**: Define geographic zones and regions for analytics
    * **Feedback System**: Manual override and quality assurance for AI outputs
    
    ### Getting Started
    
    1. Register a new user at `/auth/register`
    2. Login at `/auth/login` to get an access token
    3. Use the "Authorize" button (top right) to set your token
    4. Start creating trips and exploring the API!
    
    ### Authentication
    
    Most endpoints require authentication. After logging in, include the token in requests:
    
    ```
    Authorization: Bearer <your_access_token>
    ```
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "error_code": "VALIDATION_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(config.router)
app.include_router(feedback.router)
app.include_router(users.router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns the health status of the application.
    Can be expanded to check database connectivity.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# Mount static files only if directory exists (serverless-safe)
if os.path.isdir(os.path.join(os.path.dirname(__file__), "..", "static")) or os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    from .database import init_db
    
    if settings.DEBUG:
        print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        print(f"Debug mode: {settings.DEBUG}")
        print("Initializing database...")
    
    try:
        await init_db()
        if settings.DEBUG:
            print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if settings.DEBUG:
        print("Shutting down application...")
