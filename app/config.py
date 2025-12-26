"""
Application Configuration
Environment-based settings using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str
    MONGODB_URL: str
    
    # Security & Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External API Keys
    GRAPHHOPPER_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
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
