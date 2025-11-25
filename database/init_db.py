
"""
Database initialization and utility functions
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from prisma import Prisma
import bcrypt as bcrypt_lib
from datetime import datetime
import json


async def init_database():
    """Initialize database with default data"""
    db = Prisma()
    await db.connect()
    
    try:
        # Create default admin user
        existing_admin = await db.user.find_first(
            where={"username": "admin"}
        )
        
        if not existing_admin:
            # Hash password using bcrypt
            password_bytes = "admin123".encode('utf-8')
            hashed = bcrypt_lib.hashpw(password_bytes, bcrypt_lib.gensalt())
            
            admin_user = await db.user.create(
                data={
                    "username": "admin",
                    "email": "admin@roadsafenet.com",
                    "password_hash": hashed.decode('utf-8'),
                    "full_name": "System Administrator",
                    "role": "admin",
                    "is_active": True
                }
            )
            print(f"✓ Created admin user: {admin_user.username}")
        else:
            print("✓ Admin user already exists")
        
        # Create default alert templates
        templates = [
            {
                "name": "accident_alert_en",
                "language": "en",
                "template": "⚠️ ACCIDENT DETECTED!\nLocation: {location}\nTime: {time}\nSeverity: {severity}\nPlease respond immediately.",
                "is_active": True
            },
            {
                "name": "accident_alert_es",
                "language": "es",
                "template": "⚠️ ¡ACCIDENTE DETECTADO!\nUbicación: {location}\nHora: {time}\nGravedad: {severity}\nPor favor responda inmediatamente.",
                "is_active": True
            },
            {
                "name": "accident_alert_ar",
                "language": "ar",
                "template": "⚠️ تم اكتشاف حادث!\nالموقع: {location}\nالوقت: {time}\nالخطورة: {severity}\nيرجى الرد فوراً.",
                "is_active": True
            },
            {
                "name": "accident_alert_hi",
                "language": "hi",
                "template": "⚠️ दुर्घटना का पता चला!\nस्थान: {location}\nसमय: {time}\nगंभीरता: {severity}\nकृपया तुरंत जवाब दें।",
                "is_active": True
            },
            {
                "name": "accident_alert_zh",
                "language": "zh",
                "template": "⚠️ 检测到事故！\n位置：{location}\n时间：{time}\n严重程度：{severity}\n请立即响应。",
                "is_active": True
            }
        ]
        
        for template_data in templates:
            existing = await db.alerttemplate.find_first(
                where={"name": template_data["name"]}
            )
            if not existing:
                await db.alerttemplate.create(data=template_data)
                print(f"✓ Created alert template: {template_data['name']}")
        
        # Create default system settings
        settings = [
            {
                "key": "detection_enabled",
                "value": "true",
                "description": "Enable/disable accident detection"
            },
            {
                "key": "alert_enabled",
                "value": "true",
                "description": "Enable/disable alert notifications"
            },
            {
                "key": "confidence_threshold",
                "value": "0.5",
                "description": "Minimum confidence for accident detection"
            },
            {
                "key": "alert_cooldown",
                "value": "300",
                "description": "Cooldown period between alerts (seconds)"
            }
        ]
        
        for setting_data in settings:
            existing = await db.systemsetting.find_first(
                where={"key": setting_data["key"]}
            )
            if not existing:
                await db.systemsetting.create(data=setting_data)
                print(f"✓ Created system setting: {setting_data['key']}")
        
        # Create sample emergency contacts
        contacts = [
            {
                "name": "Emergency Services",
                "telegram_id": "123456789",
                "role": "police",
                "languages": "en,es",
                "is_active": True
            }
        ]
        
        for contact_data in contacts:
            existing = await db.emergencycontact.find_first(
                where={"name": contact_data["name"]}
            )
            if not existing:
                await db.emergencycontact.create(data=contact_data)
                print(f"✓ Created emergency contact: {contact_data['name']}")
        
        print("\n✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        await db.disconnect()


async def reset_database():
    """Reset database (delete all data)"""
    db = Prisma()
    await db.connect()
    
    try:
        # Delete all records (in correct order due to foreign keys)
        await db.alert.delete_many()
        await db.accident.delete_many()
        await db.systemlog.delete_many()
        await db.alerttemplate.delete_many()
        await db.systemsetting.delete_many()
        await db.emergencycontact.delete_many()
        await db.user.delete_many()
        
        print("✅ Database reset successfully!")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        raise
    finally:
        await db.disconnect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        print("⚠️  Resetting database...")
        asyncio.run(reset_database())
    
    print("🔄 Initializing database...")
    asyncio.run(init_database())
