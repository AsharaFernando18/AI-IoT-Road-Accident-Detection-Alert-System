#!/usr/bin/env python3
"""
Quick system test to verify all components are working
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("🔍 Testing RoadSafeNet Components...")
print("=" * 50)

# Test 1: Config
try:
    from config import Config
    config = Config()
    print("✅ Config: Loaded successfully")
    print(f"   - Database: {config.DATABASE_URL}")
    print(f"   - YOLO Model: {config.YOLO_MODEL_PATH}")
except Exception as e:
    print(f"❌ Config: Failed - {e}")

# Test 2: Database
try:
    from prisma import Prisma
    import asyncio
    
    async def test_db():
        db = Prisma()
        await db.connect()
        users = await db.user.count()
        accidents = await db.accident.count()
        await db.disconnect()
        return users, accidents
    
    users_count, accidents_count = asyncio.run(test_db())
    print(f"✅ Database: Connected successfully")
    print(f"   - Users: {users_count}")
    print(f"   - Accidents: {accidents_count}")
except Exception as e:
    print(f"❌ Database: Failed - {e}")

# Test 3: YOLO Model
try:
    model_path = Path("ai_model/models/yolov10n.pt")
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ YOLO Model: Found ({size_mb:.1f} MB)")
    else:
        print(f"❌ YOLO Model: Not found at {model_path}")
except Exception as e:
    print(f"❌ YOLO Model: Failed - {e}")

# Test 4: OpenCV
try:
    import cv2
    print(f"✅ OpenCV: Version {cv2.__version__}")
except Exception as e:
    print(f"❌ OpenCV: Failed - {e}")

# Test 5: PyTorch
try:
    import torch
    cuda_available = torch.cuda.is_available()
    print(f"✅ PyTorch: Version {torch.__version__}")
    print(f"   - CUDA Available: {cuda_available}")
    if cuda_available:
        print(f"   - CUDA Version: {torch.version.cuda}")
except Exception as e:
    print(f"❌ PyTorch: Failed - {e}")

# Test 6: Ultralytics
try:
    from ultralytics import YOLO
    print(f"✅ Ultralytics: Imported successfully")
except Exception as e:
    print(f"❌ Ultralytics: Failed - {e}")

# Test 7: Geolocation Service
try:
    from utils.geolocation import GeolocationService
    geo = GeolocationService()
    print(f"✅ Geolocation Service: Initialized")
except Exception as e:
    print(f"❌ Geolocation Service: Failed - {e}")

# Test 8: Translation Service
try:
    from utils.translation import TranslationService, SimpleTranslator
    print(f"✅ Translation Service: Available")
    print(f"   - Using SimpleTranslator (mBART requires model download)")
except Exception as e:
    print(f"❌ Translation Service: Failed - {e}")

# Test 9: FastAPI
try:
    from fastapi import FastAPI
    print(f"✅ FastAPI: Available")
except Exception as e:
    print(f"❌ FastAPI: Failed - {e}")

# Test 10: Flask & Dash
try:
    from flask import Flask
    from dash import Dash
    print(f"✅ Flask & Dash: Available")
except Exception as e:
    print(f"❌ Flask & Dash: Failed - {e}")

print("=" * 50)
print("✨ Component test completed!")
print()
print("Next steps:")
print("1. Configure Telegram bot (edit .env file)")
print("2. Start services: ./start_services.sh")
print("3. Access dashboard: http://localhost:8050/dashboard/")
print("4. Login with: admin / admin123")
