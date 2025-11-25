"""
Simple script to populate database with fake data using SQLite directly
"""
import sqlite3
import random
from datetime import datetime, timedelta
import json

# Database path (correct path)
DB_PATH = "database/database/roadsafenet.db"

# Malaysia locations
MALAYSIA_LOCATIONS = [
    {"name": "Jalan Bukit Bintang", "city": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869},
    {"name": "Jalan Tun Razak", "city": "Kuala Lumpur", "lat": 3.1579, "lon": 101.7122},
    {"name": "Federal Highway", "city": "Petaling Jaya", "lat": 3.1073, "lon": 101.6067},
    {"name": "KLIA Highway", "city": "Sepang", "lat": 2.7456, "lon": 101.7072},
    {"name": "North-South Highway", "city": "Seremban", "lat": 2.7297, "lon": 101.9381},
    {"name": "Jalan Sultan Ismail", "city": "Kuala Lumpur", "lat": 3.1524, "lon": 101.7054},
    {"name": "LDP Highway", "city": "Shah Alam", "lat": 3.0738, "lon": 101.5183},
    {"name": "Johor Bahru Highway", "city": "Johor Bahru", "lat": 1.4927, "lon": 103.7414},
    {"name": "Penang Bridge", "city": "Penang", "lat": 5.3242, "lon": 100.2873},
    {"name": "Ipoh-KL Highway", "city": "Ipoh", "lat": 4.5975, "lon": 101.0901},
    {"name": "East Coast Highway", "city": "Kuantan", "lat": 3.8077, "lon": 103.3260},
    {"name": "Kota Kinabalu Highway", "city": "Kota Kinabalu", "lat": 5.9804, "lon": 116.0735},
    {"name": "Kuching-Sri Aman Road", "city": "Kuching", "lat": 1.5533, "lon": 110.3593},
    {"name": "Melaka Highway", "city": "Melaka", "lat": 2.1896, "lon": 102.2501},
    {"name": "Alor Setar Highway", "city": "Alor Setar", "lat": 6.1248, "lon": 100.3678},
    {"name": "Butterworth Road", "city": "Butterworth", "lat": 5.3991, "lon": 100.3637},
]

SEVERITIES = ["low", "medium", "high", "critical"]
ACCIDENT_TYPES = ["collision", "rollover", "pedestrian", "rear-end", "side-impact", "motorcycle"]

def populate_database():
    """Populate database with fake data"""
    print("🎲 Starting database population with fake data...")
    print(f"📂 Database: {DB_PATH}\n")
    
    # Connect to SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        now = datetime.now()
        accidents_created = 0
        alerts_created = 0
        incidents_created = 0
        notifications_created = 0
        logs_created = 0
        
        # Get all responder IDs
        cursor.execute("SELECT id FROM Responder")
        responder_ids = [row[0] for row in cursor.fetchall()]
        print(f"✅ Found {len(responder_ids)} responders in database\n")
        
        # 1. Create Accidents (last 90 days)
        print("📊 Creating 150 accident records...")
        for i in range(150):
            days_ago = random.randint(0, 90)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            location = random.choice(MALAYSIA_LOCATIONS)
            severity = random.choices(SEVERITIES, weights=[30, 40, 20, 10])[0]
            confidence = random.uniform(0.65, 0.99)
            status = random.choices(
                ["pending", "confirmed", "resolved", "false_alarm"],
                weights=[10, 30, 50, 10]
            )[0]
            accident_type = random.choice(ACCIDENT_TYPES)
            
            # Add small random offset to coordinates
            lat = location["lat"] + random.uniform(-0.01, 0.01)
            lon = location["lon"] + random.uniform(-0.01, 0.01)
            
            detected_objects = json.dumps([
                {"class": "car", "confidence": random.uniform(0.7, 0.99)},
                {"class": "accident", "confidence": confidence}
            ])
            
            cursor.execute("""
                INSERT INTO Accident (
                    timestamp, location_lat, location_lon, location_name,
                    address, city, country, severity, confidence,
                    detected_objects, status, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp.isoformat(),
                lat, lon,
                location["name"],
                f"{location['name']}, {location['city']}",
                location["city"],
                "Malaysia",
                severity,
                confidence,
                detected_objects,
                status,
                f"Type: {accident_type}",
                timestamp.isoformat()
            ))
            
            accident_id = cursor.lastrowid
            accidents_created += 1
            
            # Create 2-4 alerts per accident
            num_alerts = random.randint(2, 4)
            for _ in range(num_alerts):
                lang = random.choice(["en", "ms", "zh", "ta"])
                alert_timestamp = timestamp + timedelta(seconds=random.randint(1, 30))
                
                messages = {
                    "en": f"🚨 {severity.upper()} accident detected at {location['name']}",
                    "ms": f"🚨 Kemalangan {severity.upper()} dikesan di {location['name']}",
                    "zh": f"🚨 在{location['name']}检测到{severity.upper()}事故",
                    "ta": f"🚨 {location['name']}இல் {severity.upper()} விபத்து கண்டறியப்பட்டது"
                }
                
                cursor.execute("""
                    INSERT INTO Alert (
                        accident_id, message, language, severity,
                        sent_at, status, recipients
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    accident_id,
                    messages[lang],
                    lang,
                    severity,
                    alert_timestamp.isoformat(),
                    "sent",
                    json.dumps(["emergency_services", "authorities"])
                ))
                alerts_created += 1
            
            if (i + 1) % 30 == 0:
                print(f"  ✓ Created {i + 1}/150 accidents...")
        
        print(f"✅ Created {accidents_created} accidents with {alerts_created} alerts\n")
        
        # 2. Create Incidents (last 60 days)
        print("📊 Creating 200 incident records...")
        for i in range(200):
            days_ago = random.randint(0, 60)
            hours_ago = random.randint(0, 23)
            timestamp = now - timedelta(days=days_ago, hours=hours_ago)
            
            location = random.choice(MALAYSIA_LOCATIONS)
            severity = random.choices(SEVERITIES, weights=[25, 40, 25, 10])[0]
            incident_type = random.choice(ACCIDENT_TYPES)
            status = random.choices(
                ["pending", "dispatched", "resolved"],
                weights=[15, 25, 60]
            )[0]
            
            lat = location["lat"] + random.uniform(-0.01, 0.01)
            lon = location["lon"] + random.uniform(-0.01, 0.01)
            
            cursor.execute("""
                INSERT INTO Incident (
                    type, description, location_lat, location_lon,
                    location_name, severity, status, reported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident_type,
                f"{incident_type.title()} incident at {location['name']}",
                lat, lon,
                location["name"],
                severity,
                status,
                timestamp.isoformat()
            ))
            
            incident_id = cursor.lastrowid
            incidents_created += 1
            
            # Create 3-5 notifications per incident
            if responder_ids:
                num_notifications = random.randint(3, 5)
                for _ in range(num_notifications):
                    responder_id = random.choice(responder_ids)
                    notif_timestamp = timestamp + timedelta(minutes=random.randint(1, 10))
                    notif_status = random.choices(
                        ["pending", "sent", "delivered", "failed"],
                        weights=[5, 30, 60, 5]
                    )[0]
                    
                    cursor.execute("""
                        INSERT INTO Notification (
                            incident_id, responder_id, message,
                            status, sent_at, delivered_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        incident_id,
                        responder_id,
                        f"🚨 {severity.upper()}: {incident_type} at {location['name']}. Immediate response required.",
                        notif_status,
                        notif_timestamp.isoformat(),
                        (notif_timestamp + timedelta(seconds=random.randint(5, 60))).isoformat() if notif_status == "delivered" else None
                    ))
                    notifications_created += 1
            
            if (i + 1) % 40 == 0:
                print(f"  ✓ Created {i + 1}/200 incidents...")
        
        print(f"✅ Created {incidents_created} incidents with {notifications_created} notifications\n")
        
        # 3. Create System Logs (last 30 days)
        print("📊 Creating 500 system log entries...")
        log_levels = ["INFO", "WARNING", "ERROR"]
        log_messages = {
            "INFO": [
                "System started successfully",
                "Video stream initialized",
                "Detection model loaded",
                "Emergency notification sent",
                "Database backup completed"
            ],
            "WARNING": [
                "High CPU usage detected",
                "Network latency increased",
                "Video frame dropped",
                "Low confidence detection"
            ],
            "ERROR": [
                "Failed to connect to camera",
                "Database connection timeout",
                "Notification delivery failed",
                "Model inference error"
            ]
        }
        
        for i in range(500):
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            level = random.choices(log_levels, weights=[70, 20, 10])[0]
            message = random.choice(log_messages[level])
            
            cursor.execute("""
                INSERT INTO SystemLog (
                    level, message, timestamp, source
                ) VALUES (?, ?, ?, ?)
            """, (
                level,
                message,
                timestamp.isoformat(),
                "system"
            ))
            logs_created += 1
        
        print(f"✅ Created {logs_created} system logs\n")
        
        # Commit all changes
        conn.commit()
        
        # Print summary
        print("=" * 60)
        print("📈 DATABASE POPULATION COMPLETE!")
        print("=" * 60)
        print(f"✅ Accidents:      {accidents_created}")
        print(f"✅ Alerts:         {alerts_created}")
        print(f"✅ Incidents:      {incidents_created}")
        print(f"✅ Notifications:  {notifications_created}")
        print(f"✅ System Logs:    {logs_created}")
        print(f"✅ Total Records:  {accidents_created + alerts_created + incidents_created + notifications_created + logs_created}")
        print("=" * 60)
        print("\n🎉 Database is now populated with fake data for testing!")
        print("🔍 You can now view analytics at: http://localhost:8050/dashboard/analytics")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    populate_database()
