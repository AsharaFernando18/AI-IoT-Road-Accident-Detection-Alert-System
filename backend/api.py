"""
FastAPI Backend for RoadSafeNet
RESTful API endpoints for accident detection system
"""

from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from passlib.hash import bcrypt
import sys
from pathlib import Path
import asyncio
import json

sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from prisma import Prisma
import logging
from utils.telegram_notifications import notify_nearest_responders

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RoadSafeNet API",
    description="AI-powered road accident detection and alert system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database
db = Prisma()


# Pydantic Models
class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class AccidentCreate(BaseModel):
    location_lat: float
    location_lon: float
    location_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    severity: str = "medium"
    confidence: float
    detected_objects: str
    image_path: Optional[str] = None
    video_frame: Optional[int] = None
    weather_info: Optional[str] = None
    notes: Optional[str] = None


class AccidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None


class AlertCreate(BaseModel):
    accident_id: int
    language: str
    message: str
    translated_message: Optional[str] = None
    recipient: Optional[str] = None


class SystemSettingUpdate(BaseModel):
    value: str


# Helper Functions
def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        Config.JWT_SECRET_KEY, 
        algorithm=Config.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            Config.JWT_SECRET_KEY, 
            algorithms=[Config.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = await db.user.find_unique(where={"username": username})
        
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def require_admin(current_user = Depends(get_current_user)):
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Startup and Shutdown Events
@app.on_event("startup")
async def startup():
    """Initialize database connection"""
    await db.connect()
    logger.info("✓ Database connected")


@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    await db.disconnect()
    logger.info("✓ Database disconnected")


# Authentication Endpoints
@app.post("/api/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user exists
    existing = await db.user.find_first(
        where={
            "OR": [
                {"username": user_data.username},
                {"email": user_data.email}
            ]
        }
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create user
    password_hash = bcrypt.hash(user_data.password)
    
    user = await db.user.create(
        data={
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": password_hash,
            "full_name": user_data.full_name,
            "role": user_data.role
        }
    )
    
    return user


@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login(credentials: UserLogin):
    """Login and get access token"""
    user = await db.user.find_unique(where={"username": credentials.username})
    
    if not user or not bcrypt.verify(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_me(current_user = Depends(get_current_user)):
    """Get current user information"""
    return current_user


# Accident Endpoints
@app.post("/api/accidents", status_code=status.HTTP_201_CREATED, tags=["Accidents"])
async def create_accident(
    accident: AccidentCreate,
    current_user = Depends(get_current_user)
):
    """Create new accident record and send notifications"""
    new_accident = await db.accident.create(data=accident.dict())
    
    # Log action
    await db.systemlog.create(
        data={
            "level": "INFO",
            "source": "api",
            "message": f"Accident created: {new_accident.id}",
            "user_id": current_user.id
        }
    )
    
    # Send notifications to nearest responders
    try:
        accident_data = {
            'latitude': new_accident.latitude,
            'longitude': new_accident.longitude,
            'severity': new_accident.severity,
            'location': new_accident.location,
            'city': new_accident.city,
            'timestamp': new_accident.timestamp.isoformat() if new_accident.timestamp else datetime.now().isoformat(),
            'description': new_accident.description
        }
        
        notification_results = notify_nearest_responders(accident_data, limit_per_type=3)
        
        logger.info(f"🚨 Notifications sent for accident {new_accident.id}")
        logger.info(f"Results: {notification_results}")
        
    except Exception as e:
        logger.error(f"Error sending notifications for accident {new_accident.id}: {e}")
        # Don't fail the accident creation if notifications fail
    
    return new_accident


@app.get("/api/accidents", tags=["Accidents"])
async def get_accidents(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get list of accidents with filters"""
    where = {}
    
    if severity:
        where["severity"] = severity
    
    if status_filter:
        where["status"] = status_filter
    
    accidents = await db.accident.find_many(
        where=where,
        skip=skip,
        take=limit,
        order={"timestamp": "desc"}
    )
    
    total = await db.accident.count(where=where)
    
    return {
        "data": accidents,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@app.get("/api/accidents/{accident_id}", tags=["Accidents"])
async def get_accident(
    accident_id: int,
    current_user = Depends(get_current_user)
):
    """Get specific accident by ID"""
    accident = await db.accident.find_unique(
        where={"id": accident_id},
        include={"alerts": True}
    )
    
    if not accident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accident not found"
        )
    
    return accident


@app.patch("/api/accidents/{accident_id}", tags=["Accidents"])
async def update_accident(
    accident_id: int,
    update: AccidentUpdate,
    current_user = Depends(get_current_user)
):
    """Update accident information"""
    accident = await db.accident.find_unique(where={"id": accident_id})
    
    if not accident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accident not found"
        )
    
    updated = await db.accident.update(
        where={"id": accident_id},
        data=update.dict(exclude_unset=True)
    )
    
    # Log action
    await db.systemlog.create(
        data={
            "level": "INFO",
            "source": "api",
            "message": f"Accident updated: {accident_id}",
            "user_id": current_user.id
        }
    )
    
    return updated


@app.delete("/api/accidents/{accident_id}", tags=["Accidents"])
async def delete_accident(
    accident_id: int,
    current_user = Depends(require_admin)
):
    """Delete accident record (admin only)"""
    accident = await db.accident.find_unique(where={"id": accident_id})
    
    if not accident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accident not found"
        )
    
    await db.accident.delete(where={"id": accident_id})
    
    return {"message": "Accident deleted successfully"}


# Analytics Endpoints
@app.get("/api/analytics/stats", tags=["Analytics"])
async def get_statistics(current_user = Depends(get_current_user)):
    """Get overall statistics"""
    total_accidents = await db.accident.count()
    total_alerts = await db.alert.count()
    
    pending_accidents = await db.accident.count(where={"status": "pending"})
    confirmed_accidents = await db.accident.count(where={"status": "confirmed"})
    
    # Severity breakdown
    severity_stats = {}
    for severity in ["low", "medium", "high", "critical"]:
        count = await db.accident.count(where={"severity": severity})
        severity_stats[severity] = count
    
    # Recent accidents (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    recent_accidents = await db.accident.count(
        where={"timestamp": {"gte": yesterday}}
    )
    
    return {
        "total_accidents": total_accidents,
        "total_alerts": total_alerts,
        "pending_accidents": pending_accidents,
        "confirmed_accidents": confirmed_accidents,
        "severity_breakdown": severity_stats,
        "recent_24h": recent_accidents
    }


@app.get("/api/analytics/timeline", tags=["Analytics"])
async def get_timeline(
    days: int = 7,
    current_user = Depends(get_current_user)
):
    """Get accident timeline for specified days"""
    start_date = datetime.now() - timedelta(days=days)
    
    accidents = await db.accident.find_many(
        where={"timestamp": {"gte": start_date}},
        order={"timestamp": "asc"}
    )
    
    # Group by date
    timeline = {}
    for accident in accidents:
        date_key = accident.timestamp.strftime("%Y-%m-%d")
        if date_key not in timeline:
            timeline[date_key] = 0
        timeline[date_key] += 1
    
    return timeline


@app.get("/api/analytics/heatmap", tags=["Analytics"])
async def get_heatmap(current_user = Depends(get_current_user)):
    """Get accident locations for heatmap"""
    accidents = await db.accident.find_many(
        select={
            "id": True,
            "location_lat": True,
            "location_lon": True,
            "severity": True,
            "timestamp": True
        }
    )
    
    return [
        {
            "lat": acc.location_lat,
            "lon": acc.location_lon,
            "severity": acc.severity,
            "timestamp": acc.timestamp.isoformat()
        }
        for acc in accidents
    ]


# Alert Endpoints
@app.post("/api/alerts", status_code=status.HTTP_201_CREATED, tags=["Alerts"])
async def create_alert(
    alert: AlertCreate,
    current_user = Depends(get_current_user)
):
    """Create new alert"""
    new_alert = await db.alert.create(data=alert.dict())
    return new_alert


@app.get("/api/alerts", tags=["Alerts"])
async def get_alerts(
    skip: int = 0,
    limit: int = 100,
    accident_id: Optional[int] = None,
    current_user = Depends(get_current_user)
):
    """Get list of alerts"""
    where = {}
    if accident_id:
        where["accident_id"] = accident_id
    
    alerts = await db.alert.find_many(
        where=where,
        skip=skip,
        take=limit,
        order={"sent_at": "desc"},
        include={"accident": True}
    )
    
    total = await db.alert.count(where=where)
    
    return {
        "data": alerts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# User Management Endpoints
@app.get("/api/users", tags=["Users"])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(require_admin)
):
    """Get list of users (admin only)"""
    users = await db.user.find_many(
        skip=skip,
        take=limit,
        order={"created_at": "desc"}
    )
    
    total = await db.user.count()
    
    return {
        "data": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@app.patch("/api/users/{user_id}", tags=["Users"])
async def update_user(
    user_id: int,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    current_user = Depends(require_admin)
):
    """Update user (admin only)"""
    user = await db.user.find_unique(where={"id": user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = {}
    if is_active is not None:
        update_data["is_active"] = is_active
    if role is not None:
        update_data["role"] = role
    
    updated = await db.user.update(
        where={"id": user_id},
        data=update_data
    )
    
    return updated


# System Logs Endpoints
@app.get("/api/logs", tags=["Logs"])
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,
    source: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get system logs"""
    where = {}
    if level:
        where["level"] = level
    if source:
        where["source"] = source
    
    logs = await db.systemlog.find_many(
        where=where,
        skip=skip,
        take=limit,
        order={"timestamp": "desc"}
    )
    
    total = await db.systemlog.count(where=where)
    
    return {
        "data": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# System Settings Endpoints
@app.get("/api/settings", tags=["Settings"])
async def get_settings(current_user = Depends(get_current_user)):
    """Get all system settings"""
    settings = await db.systemsetting.find_many()
    return {setting.key: setting.value for setting in settings}


@app.patch("/api/settings/{key}", tags=["Settings"])
async def update_setting(
    key: str,
    setting: SystemSettingUpdate,
    current_user = Depends(require_admin)
):
    """Update system setting (admin only)"""
    existing = await db.systemsetting.find_unique(where={"key": key})
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    
    updated = await db.systemsetting.update(
        where={"key": key},
        data={"value": setting.value}
    )
    
    return updated


# Health Check
@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=Config.FASTAPI_HOST,
        port=Config.FASTAPI_PORT,
        reload=Config.DEBUG
    )
