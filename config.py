"""
RoadSafeNet Configuration Module
Centralized configuration management using environment variables
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Main configuration class for RoadSafeNet"""
    
    # Application
    APP_NAME = "RoadSafeNet"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "file:./database/roadsafenet.db")
    DATABASE_PATH = BASE_DIR / "database" / "roadsafenet.db"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_IDS = [
        chat_id.strip() 
        for chat_id in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") 
        if chat_id.strip()
    ]
    
    # Nominatim API (OpenStreetMap)
    NOMINATIM_USER_AGENT = os.getenv("NOMINATIM_USER_AGENT", "RoadSafeNet/1.0")
    NOMINATIM_BASE_URL = os.getenv(
        "NOMINATIM_BASE_URL", 
        "https://nominatim.openstreetmap.org"
    )
    
    # YOLOv10 Configuration
    YOLO_MODEL_PATH = BASE_DIR / os.getenv(
        "YOLO_MODEL_PATH", 
        "ai_model/models/yolov10n.pt"
    )
    YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.5"))
    YOLO_IOU_THRESHOLD = float(os.getenv("YOLO_IOU_THRESHOLD", "0.45"))
    
    # Accident detection classes (COCO dataset)
    ACCIDENT_CLASSES = [
        "car", "motorcycle", "bus", "truck", 
        "bicycle", "person", "traffic light", "stop sign"
    ]
    
    # Flask
    FLASK_APP = os.getenv("FLASK_APP", "backend/app.py")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    
    # FastAPI
    FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
    
    # Dash
    DASH_HOST = os.getenv("DASH_HOST", "0.0.0.0")
    DASH_PORT = int(os.getenv("DASH_PORT", "8050"))
    
    # Hugging Face
    HF_MODEL_NAME = os.getenv(
        "HF_MODEL_NAME", 
        "facebook/mbart-large-50-many-to-many-mmt"
    )
    HF_CACHE_DIR = BASE_DIR / os.getenv("HF_CACHE_DIR", "./cache/huggingface")
    
    # Supported Languages
    SUPPORTED_LANGUAGES = os.getenv("SUPPORTED_LANGUAGES", "en,es,ar,hi,zh").split(",")
    
    LANGUAGE_CODES = {
        "en": "en_XX",  # English
        "es": "es_XX",  # Spanish
        "ar": "ar_AR",  # Arabic
        "hi": "hi_IN",  # Hindi
        "zh": "zh_CN"   # Mandarin Chinese
    }
    
    LANGUAGE_NAMES = {
        "en": "English",
        "es": "Spanish",
        "ar": "Arabic",
        "hi": "Hindi",
        "zh": "Mandarin"
    }
    
    # Alert Configuration
    ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))
    
    # Video Configuration
    VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")
    VIDEO_FRAME_SKIP = int(os.getenv("VIDEO_FRAME_SKIP", "2"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/roadsafenet.log")
    
    # Optional: Weather API
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    WEATHER_API_URL = os.getenv(
        "WEATHER_API_URL", 
        "https://api.openweathermap.org/data/2.5/weather"
    )
    
    # Optional: Voice Alerts
    ENABLE_VOICE_ALERTS = os.getenv("ENABLE_VOICE_ALERTS", "False").lower() == "true"
    
    # Paths
    LOGS_DIR = BASE_DIR / "logs"
    UPLOADS_DIR = BASE_DIR / "uploads"
    STATIC_DIR = BASE_DIR / "frontend" / "static"
    TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.LOGS_DIR,
            cls.UPLOADS_DIR,
            cls.STATIC_DIR / "uploads",
            cls.HF_CACHE_DIR,
            BASE_DIR / "database",
            BASE_DIR / "ai_model" / "models"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is not set")
        
        if not cls.TELEGRAM_CHAT_IDS:
            errors.append("TELEGRAM_CHAT_IDS is not set")
        
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("SECRET_KEY should be changed in production")
        
        return errors


# Create directories on import
Config.create_directories()
