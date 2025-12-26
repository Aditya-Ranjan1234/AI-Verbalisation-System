"""
Application Configuration
Environment-based settings using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str | None = None
    POSTGRES_URL: str | None = None  # Vercel Postgres variable
    MONGODB_URL: str | None = None
    
    # Security & Authentication
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External API Keys
    GRAPHHOPPER_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEOCODING_API_KEY: str = "" # Keep for backward compatibility if needed
    LLM_API_KEY: str = "" # Keep for backward compatibility if needed
    
    # Application Settings
    APP_NAME: str = "AI Trip Data Verbalization System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
