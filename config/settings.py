"""
Application Settings and Configuration

This module provides centralized configuration management using pydantic-settings.
Settings are loaded from environment variables and a .env file.

Configuration Sources (in order of precedence):
1. Environment variables
2. .env file
3. Default values

Key Settings:
- google_api_key: Required for Gemini API access
- model_name: Gemini model to use
- app_name: Application name for sessions
- api_host/port: FastAPI server configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application Settings
    
    Loads configuration from environment variables and .env file.
    Uses pydantic for validation and type safety.
    """
    
    # Google API Configuration
    google_api_key: str = ""
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "global"
    
    # Model Configuration
    model_name: str = "gemini-2.5-flash-lite"
    
    # Application Configuration
    app_name: str = "CustoFlow"
    debug: bool = False
    
    # API Configuration (for FastAPI server)
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()

# Validate API key is set
if not settings.google_api_key:
    raise ValueError(
        "GOOGLE_API_KEY environment variable is required. "
        "Please set it in your .env file or environment."
    )

