"""
Populate database with fake data - matches exact Prisma schema
"""
import sqlite3
import random
from datetime import datetime, timedelta
import json

# Database path - CORRECT PATH
DB_PATH = "C:\\Users\\ASUS\\Desktop\\AI-IoT-Road-Accident-Detection-Alert-System\\database\\database\\roadsafenet.db"

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
INCIDENT_TYPES = ["collision", "rollover", "pedestrian", "rear-end", "side-impact", "motorcycle"]

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
        cursor.execute("SELECT id, role FROM Responder")
        responders = cursor.fetchall()
        print(f"✅ Found {len(responders)} responders in database")
        if responders:
            print(f"   Responder roles: {', '.join(set(r[1] for r in responders))}\n")
        else:
            print("   ⚠️  Warning: No responders found. Notifications won't be created.\n")
        
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
            
            # Add small random offset to coordinates
            lat = location["lat"] + random.uniform(-0.01, 0.01)
            lon = location["lon"] + random.uniform(-0.01, 0.01)
            
            detected_objects = json.dumps([
                {"class": "car", "confidence": random.uniform(0.7, 0.99)},
                {"class": "accident", "confidence": confidence}
            ])
            
            # Insert Accident - matches exact schema
            cursor.execute("""
                INSERT INTO Accident (
                    timestamp, location_lat, location_lon, location_name,
                    address, city, country, severity, confidence,
                    detected_objects, status, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                lat, lon,
                location["name"],
                f"{location['name']}, {location['city']}",
                location["city"],
                "Malaysia",
                severity,
                confidence,
                detected_objects,
                status,
                f"Auto-detected accident - Type: {random.choice(INCIDENT_TYPES)}",
                timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            accident_id = cursor.lastrowid
            accidents_created += 1
            
            # Create 2-4 alerts per accident
            num_alerts = random.randint(2, 4)
            for _ in range(num_alerts):
                lang = random.choice(["en", "ms", "zh", "ta"])
                alert_timestamp = timestamp + timedelta(seconds=random.randint(1, 30))
                alert_status = random.choices(["sent", "failed", "pending"], weights=[80, 10, 10])[0]
                
                messages = {
                    "en": f"🚨 {severity.upper()} accident detected at {location['name']}",
                    "ms": f"🚨 Kemalangan {severity.upper()} dikesan di {location['name']}",
                    "zh": f"🚨 在{location['name']}检测到{severity.upper()}事故",
                    "ta": f"🚨 {location['name']}இல் {severity.upper()} விபத்து கண்டறியப்பட்டது"
                }
                
                # Insert Alert - matches exact schema (no severity column)
                cursor.execute("""
                    INSERT INTO Alert (
                        accident_id, language, message, sent_at, status
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    accident_id,
                    lang,
                    messages[lang],
                    alert_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    alert_status
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
            minutes_ago = random.randint(0, 59)
            timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            location = random.choice(MALAYSIA_LOCATIONS)
            severity = random.choices(SEVERITIES, weights=[25, 40, 25, 10])[0]
            incident_type = random.choice(INCIDENT_TYPES)
            status = random.choices(
                ["pending", "dispatched", "resolved"],
                weights=[15, 25, 60]
            )[0]
            
            lat = location["lat"] + random.uniform(-0.01, 0.01)
            lon = location["lon"] + random.uniform(-0.01, 0.01)
            confidence = random.uniform(0.70, 0.99)
            
            # Insert Incident - matches exact schema
            cursor.execute("""
                INSERT INTO Incident (
                    timestamp, location_lat, location_lon, address,
                    city, country, severity, status, type,
                    confidence, description, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                lat, lon,
                f"{location['name']}, {location['city']}",
                location["city"],
                "Malaysia",
                severity,
                status,
                incident_type,
                confidence,
                f"{incident_type.title()} incident at {location['name']}",
                timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            incident_id = cursor.lastrowid
            incidents_created += 1
            
            # Create 3-5 notifications per incident
            if responders:
                num_notifications = random.randint(3, 5)
                for _ in range(num_notifications):
                    responder = random.choice(responders)
                    responder_id = responder[0]
                    responder_role = responder[1]
                    
                    notif_timestamp = timestamp + timedelta(minutes=random.randint(1, 10))
                    notif_status = random.choices(
                        ["sent", "delivered", "failed"],
                        weights=[30, 65, 5]
                    )[0]
                    
                    delivered_time = None
                    if notif_status == "delivered":
                        delivered_time = (notif_timestamp + timedelta(seconds=random.randint(5, 60))).strftime('%Y-%m-%d %H:%M:%S')
                    
                    lang = random.choice(["en", "ms"])
                    
                    # Insert Notification - matches exact schema
                    cursor.execute("""
                        INSERT INTO Notification (
                            incident_id, responder_id, language, message,
                            sent_to, sent_time, delivered_time, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        incident_id,
                        responder_id,
                        lang,
                        f"🚨 {severity.upper()}: {incident_type} at {location['name']}. Immediate response required.",
                        responder_role,
                        notif_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        delivered_time,
                        notif_status
                    ))
                    notifications_created += 1
            
            if (i + 1) % 40 == 0:
                print(f"  ✓ Created {i + 1}/200 incidents...")
        
        print(f"✅ Created {incidents_created} incidents with {notifications_created} notifications\n")
        
        # 3. Create System Logs (last 30 days)
        print("📊 Creating 500 system log entries...")
        log_levels = ["INFO", "WARNING", "ERROR"]
        log_sources = ["detection", "translation", "telegram", "api", "system"]
        log_messages = {
            "INFO": [
                "System started successfully",
                "Video stream initialized",
                "Detection model loaded",
                "Emergency notification sent",
                "Database backup completed",
                "Alert dispatched to emergency services",
                "User login successful"
            ],
            "WARNING": [
                "High CPU usage detected",
                "Network latency increased",
                "Video frame dropped",
                "Low confidence detection",
                "Notification retry attempted",
                "Database connection slow"
            ],
            "ERROR": [
                "Failed to connect to camera",
                "Database connection timeout",
                "Notification delivery failed",
                "Model inference error",
                "Translation service unavailable"
            ]
        }
        
        for i in range(500):
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            level = random.choices(log_levels, weights=[70, 20, 10])[0]
            source = random.choice(log_sources)
            message = random.choice(log_messages[level])
            
            # Insert SystemLog - matches exact schema
            cursor.execute("""
                INSERT INTO SystemLog (
                    timestamp, level, source, message
                ) VALUES (?, ?, ?, ?)
            """, (
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                level,
                source,
                message
            ))
            logs_created += 1
            
            if (i + 1) % 100 == 0:
                print(f"  ✓ Created {i + 1}/500 logs...")
        
        print(f"✅ Created {logs_created} system logs\n")
        
        # Commit all changes
        conn.commit()
        
        # Print summary
        print("=" * 60)
        print("📈 DATABASE POPULATION COMPLETE!")
        print("=" * 60)
        print(f"✅ Accidents:      {accidents_created:>6}")
        print(f"✅ Alerts:         {alerts_created:>6}")
        print(f"✅ Incidents:      {incidents_created:>6}")
        print(f"✅ Notifications:  {notifications_created:>6}")
        print(f"✅ System Logs:    {logs_created:>6}")
        print(f"{'─' * 60}")
        total = accidents_created + alerts_created + incidents_created + notifications_created + logs_created
        print(f"✅ Total Records:  {total:>6}")
        print("=" * 60)
        print("\n🎉 Database is now populated with fake data for testing!")
        print("🔍 You can now view analytics at: http://localhost:8050/dashboard/analytics")
        print("\n💡 Tip: Start your backend and frontend servers to see the data:")
        print("   Backend:  python backend/api.py")
        print("   Frontend: python frontend/app.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    populate_database()
