"""M3 Agent System Settings"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Settings
    LLM_BASE_URL: str = "http://192.168.9.125:8000/v1"
    LLM_MODEL: str = "qwen.qwen3-vl-235b-a22b-instruct"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    # Redis Settings
    REDIS_URL: str = "redis://m3-redis:6379/0"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Admin Settings
    ADMIN_PORT: int = 8002
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from .env

settings = Settings()
