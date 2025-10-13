"""Configuration management using environment variables"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    APP_NAME: str = "shield-ag-ui-backend"
    ENV: str = "production"
    DEBUG: bool = False
    
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    CORS_ORIGINS: List[str] = ["http://localhost:3001", "http://localhost:80"]
    
    LITELLM_URL: str = "http://hx-litellm-server:4000"
    ORCHESTRATOR_URL: str = "http://hx-orchestrator-server:8000"
    REDIS_URL: str = "redis://hx-sqldb-server:6379"
    QDRANT_URL: str = "http://hx-vectordb-server:6333"
    
    REDIS_STREAM_NAME: str = "shield:events"
    REDIS_CONSUMER_GROUP: str = "ag-ui-clients"
    REDIS_CONSUMER_NAME: str = "hx-dev-server"
    
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    DATABASE_URL: str = "postgresql://shield:shield@hx-sqldb-server:5432/shield"
    
    LITELLM_API_KEY: str = "sk-shield-lob-default"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
