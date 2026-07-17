from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

from dotenv import load_dotenv
load_dotenv(env_path)


class Settings(BaseSettings):
    APP_NAME: str = "Lumina Cameroon"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./lumina_cameroon.db"
    )
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # DeepSeek AI Configuration
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    DEEPSEEK_API_BASE_URL: str = os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com")
    
    # File Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt"]
    
    # Class Code Settings
    CLASS_CODE_EXPIRY_DAYS: int = 7
    
    # Parent Linking
    MAX_PARENTS_PER_STUDENT: int = 2
    
    # Streak Multipliers
    STREAK_MULTIPLIERS: dict = {
        3: 1.25,
        7: 1.5,
        14: 1.75,
        30: 2.0
    }
    
    # Scoring
    LEADERBOARD_CATEGORIES: List[str] = ["participation", "speed", "quiz"]
    
    class Config:
        env_file = ".env"


settings = Settings()
