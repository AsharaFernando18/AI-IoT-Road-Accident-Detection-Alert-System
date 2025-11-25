"""
Populate Database with Realistic Fake Data for Analytics Dashboard
Creates accidents, alerts, incidents, notifications, and system logs
"""

import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from prisma import Prisma
from config import Config

# Malaysia cities and locations
MALAYSIA_LOCATIONS = [
    {"city": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869, "name": "Jalan Bukit Bintang"},
    {"city": "Kuala Lumpur", "lat": 3.1478, "lon": 101.6953, "name": "KLCC Area"},
    {"city": "Kuala Lumpur", "lat": 3.1850, "lon": 101.6783, "name": "Sentul"},
    {"city": "Petaling Jaya", "lat": 3.1073, "lon": 101.6067, "name": "Section 14"},
    {"city": "Shah Alam", "lat": 3.0687, "lon": 101.4458, "name": "Shah Alam Highway"},
    {"city": "Johor Bahru", "lat": 1.4927, "lon": 103.7414, "name": "JB City Centre"},
    {"city": "Penang", "lat": 5.4164, "lon": 100.3327, "name": "Georgetown"},
    {"city": "Ipoh", "lat": 4.5975, "lon": 101.0901, "name": "Ipoh City"},
    {"city": "Kuantan", "lat": 3.8077, "lon": 103.3260, "name": "Kuantan Bypass"},
    {"city": "Melaka", "lat": 2.1896, "lon": 102.2501, "name": "Melaka Raya"},
    {"city": "Seremban", "lat": 2.7258, "lon": 101.9424, "name": "Seremban 2"},
    {"city": "Kota Bharu", "lat": 6.1256, "lon": 102.2381, "name": "KB Central"},
    {"city": "Kuala Terengganu", "lat": 5.3302, "lon": 103.1408, "name": "KT Waterfront"},
    {"city": "Alor Setar", "lat": 6.1248, "lon": 100.3678, "name": "AS City"},
    {"city": "Kota Kinabalu", "lat": 5.9788, "lon": 116.0753, "name": "KK Town"},
    {"city": "Kuching", "lat": 1.5535, "lon": 110.3593, "name": "Kuching Central"},
]

SEVERITIES = ["low", "medium", "high", "critical"]
ACCIDENT_TYPES = ["collision", "rollover", "pedestrian", "rear-end", "side-impact", "motorcycle"]
INCIDENT_STATUS = ["pending", "dispatched", "resolved"]
ALERT_LANGUAGES = ["en", "ms", "zh", "ta"]

DETECTED_OBJECTS_TEMPLATES = [
    '{"vehicles": 2, "persons": 1, "motorcycles": 0}',
    '{"vehicles": 3, "persons": 0, "motorcycles": 1}',
    '{"vehicles": 1, "persons": 2, "motorcycles": 0}',
    '{"vehicles": 4, "persons": 1, "motorcycles": 2}',
    '{"vehicles": 2, "persons": 3, "motorcycles": 1}',
]

RESPONDER_ROLES = ["hospital", "police", "ambulance"]

async def populate_data():
    """Populate database with fake data"""
    db = Prisma()
    await db.connect()
    
    print("🎲 Starting database population with fake data...")
    
    try:
        # Get current date
        now = datetime.now()
        
        # 1. Create Accidents (last 90 days)
        print("\n📊 Creating accident records...")
        accidents_created = 0
        
        for i in range(150):  # 150 accidents over 90 days
            days_ago = random.randint(0, 90)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            location = random.choice(MALAYSIA_LOCATIONS)
            severity = random.choices(
                SEVERITIES, 
                weights=[30, 40, 20, 10]  # More low/medium, fewer critical
            )[0]
            
            confidence = random.uniform(0.65, 0.99)
            status = random.choices(
                ["pending", "confirmed", "resolved", "false_alarm"],
                weights=[10, 30, 50, 10]
            )[0]
            
            accident = await db.accident.create(
                data={
                    "timestamp": timestamp,
                    "location_lat": location["lat"] + random.uniform(-0.01, 0.01),
                    "location_lon": location["lon"] + random.uniform(-0.01, 0.01),
                    "location_name": location["name"],
                    "address": f"{location['name']}, {location['city']}",
                    "city": location["city"],
                    "country": "Malaysia",
                    "severity": severity,
                    "confidence": confidence,
                    "detected_objects": random.choice(DETECTED_OBJECTS_TEMPLATES),
                    "status": status,
                    "notes": f"Auto-detected accident with {confidence:.1%} confidence"
                }
            )
            accidents_created += 1
            
            # Create alerts for each accident (2-4 alerts)
            num_alerts = random.randint(2, 4)
            for j in range(num_alerts):
                language = random.choice(ALERT_LANGUAGES)
                await db.alert.create(
                    data={
                        "accident_id": accident.id,
                        "language": language,
                        "message": f"Accident detected at {location['name']}, severity: {severity}",
                        "sent_at": timestamp + timedelta(seconds=random.randint(5, 30)),
                        "status": random.choices(["sent", "failed"], weights=[95, 5])[0],
                        "recipient": f"+60{random.randint(100000000, 199999999)}"
                    }
                )
        
        print(f"✅ Created {accidents_created} accident records")
        
        # 2. Create Incidents (last 60 days)
        print("\n📊 Creating incident records...")
        incidents_created = 0
        
        for i in range(200):  # 200 incidents over 60 days
            days_ago = random.randint(0, 60)
            hours_ago = random.randint(0, 23)
            
            timestamp = now - timedelta(days=days_ago, hours=hours_ago)
            location = random.choice(MALAYSIA_LOCATIONS)
            severity = random.choices(SEVERITIES, weights=[25, 40, 25, 10])[0]
            status = random.choices(INCIDENT_STATUS, weights=[15, 25, 60])[0]
            
            incident = await db.incident.create(
                data={
                    "timestamp": timestamp,
                    "location_lat": location["lat"] + random.uniform(-0.01, 0.01),
                    "location_lon": location["lon"] + random.uniform(-0.01, 0.01),
                    "address": f"{location['name']}, {location['city']}",
                    "city": location["city"],
                    "state": location["city"],
                    "country": "Malaysia",
                    "severity": severity,
                    "status": status,
                    "type": random.choice(ACCIDENT_TYPES),
                    "confidence": random.uniform(0.70, 0.98),
                    "description": f"{random.choice(ACCIDENT_TYPES).title()} accident detected"
                }
            )
            incidents_created += 1
        
        print(f"✅ Created {incidents_created} incident records")
        
        # 3. Get responders for notifications
        responders = await db.responder.find_many()
        
        if responders:
            print("\n📊 Creating notifications...")
            notifications_created = 0
            
            # Get all incidents
            all_incidents = await db.incident.find_many(
                take=150,
                order={'timestamp': 'desc'}
            )
            
            for incident in all_incidents:
                # Create 3-5 notifications per incident
                num_notifications = random.randint(3, 5)
                selected_responders = random.sample(responders, min(num_notifications, len(responders)))
                
                for responder in selected_responders:
                    notification = await db.notification.create(
                        data={
                            "incident_id": incident.id,
                            "responder_id": responder.id,
                            "language": random.choice(ALERT_LANGUAGES),
                            "message": f"Emergency at {incident.address}, severity: {incident.severity}",
                            "sent_to": responder.role,
                            "sent_time": incident.timestamp + timedelta(seconds=random.randint(10, 60)),
                            "delivered_time": incident.timestamp + timedelta(seconds=random.randint(70, 120)),
                            "status": random.choices(["sent", "delivered", "failed"], weights=[10, 85, 5])[0]
                        }
                    )
                    notifications_created += 1
            
            print(f"✅ Created {notifications_created} notification records")
        
        # 4. Create System Logs (last 30 days)
        print("\n📊 Creating system log records...")
        logs_created = 0
        
        log_sources = ["detection", "translation", "telegram", "api", "system"]
        log_levels = ["INFO", "WARNING", "ERROR"]
        
        log_messages = {
            "INFO": [
                "System started successfully",
                "Detection model loaded",
                "Video stream initialized",
                "Notification sent successfully",
                "API request processed"
            ],
            "WARNING": [
                "High CPU usage detected",
                "Low disk space warning",
                "Slow response time detected",
                "Network latency increased"
            ],
            "ERROR": [
                "Failed to send notification",
                "Database connection timeout",
                "API request failed",
                "Video stream interrupted"
            ]
        }
        
        for i in range(500):  # 500 logs over 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            timestamp = now - timedelta(days=days_ago, hours=hours_ago)
            
            level = random.choices(log_levels, weights=[70, 20, 10])[0]
            source = random.choice(log_sources)
            message = random.choice(log_messages[level])
            
            await db.systemlog.create(
                data={
                    "timestamp": timestamp,
                    "level": level,
                    "source": source,
                    "message": message,
                    "details": f'{{"source": "{source}", "timestamp": "{timestamp.isoformat()}"}}'
                }
            )
            logs_created += 1
        
        print(f"✅ Created {logs_created} system log records")
        
        # Print summary statistics
        print("\n" + "="*60)
        print("📈 DATABASE POPULATION SUMMARY")
        print("="*60)
        
        total_accidents = await db.accident.count()
        total_alerts = await db.alert.count()
        total_incidents = await db.incident.count()
        total_notifications = await db.notification.count()
        total_logs = await db.systemlog.count()
        
        print(f"📊 Total Accidents: {total_accidents}")
        print(f"📨 Total Alerts: {total_alerts}")
        print(f"🚨 Total Incidents: {total_incidents}")
        print(f"📢 Total Notifications: {total_notifications}")
        print(f"📝 Total System Logs: {total_logs}")
        
        # Show breakdown by severity
        print("\n🔴 Severity Distribution:")
        for severity in SEVERITIES:
            count = await db.accident.count(where={"severity": severity})
            print(f"   {severity.upper()}: {count}")
        
        # Show breakdown by status
        print("\n✅ Status Distribution:")
        for status in ["pending", "confirmed", "resolved", "false_alarm"]:
            count = await db.accident.count(where={"status": status})
            print(f"   {status.upper()}: {count}")
        
        # Show recent activity
        print("\n📅 Recent Activity (Last 7 Days):")
        week_ago = now - timedelta(days=7)
        recent_accidents = await db.accident.count(
            where={"timestamp": {"gte": week_ago}}
        )
        print(f"   Accidents: {recent_accidents}")
        
        print("\n✨ Database population completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error populating database: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(populate_data())
