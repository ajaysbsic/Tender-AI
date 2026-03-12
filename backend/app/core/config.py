from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application configuration"""
    
    # App
    APP_NAME: str = "TenderIQ"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./tenderiq.db"
    )
    
    # JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "dev-secret-key-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Configuration (TO BE IMPLEMENTED)
    # TODO: Add LLM provider, API key, and model selection once AI logic is ready
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")  # openai, anthropic, mixtral
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    
    # Document Processing
    MAX_FILE_SIZE_MB: int = 500
    UPLOAD_DIR: str = "uploads"
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 150
    
    # FAISS Configuration
    FAISS_INDEX_PATH: str = "faiss_indices"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL", 
        "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", 
        "redis://localhost:6379/0"
    )
    
    # API Configuration
    # Allow any localhost port for development (4200, 4201, 4202, etc.)
    ALLOWED_ORIGIN_REGEX: str = r"^https?://localhost(:\d+)?$"
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:4201",
        "http://localhost:4202",
        "http://localhost:5173",
        "http://localhost:60880"
    ]
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
