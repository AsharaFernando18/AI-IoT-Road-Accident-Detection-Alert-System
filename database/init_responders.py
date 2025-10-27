"""
Initialize Database with Demo Responders for Malaysia
Creates hospitals, police stations, and ambulance services
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from prisma import Prisma
from utils.logger import setup_logger

logger = setup_logger('init_responders')


async def initialize_demo_responders():
    """Add demo emergency responders to database"""
    
    db = Prisma()
    await db.connect()
    
    try:
        logger.info("🏥 Creating demo hospitals...")
        
        hospitals = [
            {
                "name": "Hospital Kuala Lumpur",
                "role": "hospital",
                "telegram_bot_id": "DEMO_HOSPITAL_KL_001",
                "phone": "+60 3-2615 5555",
                "address": "Jalan Pahang, 50586 Kuala Lumpur",
                "city": "Kuala Lumpur",
                "state": "Federal Territory",
                "latitude": 3.1729,
                "longitude": 101.7041,
                "is_active": True
            },
            {
                "name": "Hospital Universiti Kebangsaan Malaysia (HUKM)",
                "role": "hospital",
                "telegram_bot_id": "DEMO_HOSPITAL_HUKM_002",
                "phone": "+60 3-9145 5555",
                "address": "Jalan Yaacob Latif, 56000 Cheras",
                "city": "Cheras",
                "state": "Federal Territory",
                "latitude": 3.0105,
                "longitude": 101.7620,
                "is_active": True
            },
            {
                "name": "Hospital Pantai Kuala Lumpur",
                "role": "hospital",
                "telegram_bot_id": "DEMO_HOSPITAL_PANTAI_003",
                "phone": "+60 3-2296 0888",
                "address": "8, Jalan Bukit Pantai, 59100 Kuala Lumpur",
                "city": "Kuala Lumpur",
                "state": "Federal Territory",
                "latitude": 3.1208,
                "longitude": 101.6634,
                "is_active": True
            }
        ]
        
        for hospital in hospitals:
            try:
                await db.responder.create(data=hospital)
                logger.info(f"  ✅ Created: {hospital['name']}")
            except Exception as e:
                logger.warning(f"  ⚠️  Hospital already exists: {hospital['name']}")
        
        logger.info("🚔 Creating demo police stations...")
        
        police_stations = [
            {
                "name": "Balai Polis Sentul",
                "role": "police",
                "telegram_bot_id": "DEMO_POLICE_SENTUL_001",
                "phone": "+60 3-4042 2222",
                "address": "Jalan Sentul Pasar, 51100 Kuala Lumpur",
                "city": "Kuala Lumpur",
                "state": "Federal Territory",
                "latitude": 3.1820,
                "longitude": 101.6919,
                "is_active": True
            },
            {
                "name": "Balai Polis Wangsa Maju",
                "role": "police",
                "telegram_bot_id": "DEMO_POLICE_WANGSA_002",
                "phone": "+60 3-4142 0222",
                "address": "Section 2, Wangsa Maju, 53300 Kuala Lumpur",
                "city": "Wangsa Maju",
                "state": "Federal Territory",
                "latitude": 3.1969,
                "longitude": 101.7300,
                "is_active": True
            },
            {
                "name": "IPD Kuala Lumpur (Headquarters)",
                "role": "police",
                "telegram_bot_id": "DEMO_POLICE_IPD_KL_003",
                "phone": "+60 3-2115 9999",
                "address": "Jalan Hang Tuah, 50100 Kuala Lumpur",
                "city": "Kuala Lumpur",
                "state": "Federal Territory",
                "latitude": 3.1415,
                "longitude": 101.7005,
                "is_active": True
            }
        ]
        
        for station in police_stations:
            try:
                await db.responder.create(data=station)
                logger.info(f"  ✅ Created: {station['name']}")
            except Exception as e:
                logger.warning(f"  ⚠️  Police station already exists: {station['name']}")
        
        logger.info("🚑 Creating demo ambulance services...")
        
        ambulance_services = [
            {
                "name": "999 Emergency Ambulance Service",
                "role": "ambulance",
                "telegram_bot_id": "DEMO_AMBULANCE_999_001",
                "phone": "999",
                "address": "Nationwide Emergency Service",
                "city": "Nationwide",
                "state": "Malaysia",
                "is_active": True
            },
            {
                "name": "St John Ambulance Malaysia - KL",
                "role": "ambulance",
                "telegram_bot_id": "DEMO_AMBULANCE_STJOHN_002",
                "phone": "+60 3-2691 8880",
                "address": "Jalan Tun Ismail, 50480 Kuala Lumpur",
                "city": "Kuala Lumpur",
                "state": "Federal Territory",
                "latitude": 3.1569,
                "longitude": 101.7069,
                "is_active": True
            },
            {
                "name": "Red Crescent Malaysia",
                "role": "ambulance",
                "telegram_bot_id": "DEMO_AMBULANCE_REDCRES_003",
                "phone": "+60 3-2161 0600",
                "address": "JKR 829, Jalan Belfield, 50460 Kuala Lumpur",
                "city": "Kuala Lumpur",
                "state": "Federal Territory",
                "latitude": 3.1479,
                "longitude": 101.6938,
                "is_active": True
            }
        ]
        
        for ambulance in ambulance_services:
            try:
                await db.responder.create(data=ambulance)
                logger.info(f"  ✅ Created: {ambulance['name']}")
            except Exception as e:
                logger.warning(f"  ⚠️  Ambulance service already exists: {ambulance['name']}")
        
        # Count total responders
        total_hospitals = await db.responder.count(where={"role": "hospital"})
        total_police = await db.responder.count(where={"role": "police"})
        total_ambulances = await db.responder.count(where={"role": "ambulance"})
        
        logger.info("\n📊 Summary:")
        logger.info(f"  🏥 Hospitals: {total_hospitals}")
        logger.info(f"  🚔 Police Stations: {total_police}")
        logger.info(f"  🚑 Ambulance Services: {total_ambulances}")
        logger.info(f"  📍 Total Responders: {total_hospitals + total_police + total_ambulances}")
        
    except Exception as e:
        logger.error(f"❌ Error initializing responders: {e}")
        raise
    finally:
        await db.disconnect()


if __name__ == "__main__":
    print("🚀 Initializing Demo Emergency Responders for Malaysia...")
    asyncio.run(initialize_demo_responders())
    print("✅ Initialization complete!")
