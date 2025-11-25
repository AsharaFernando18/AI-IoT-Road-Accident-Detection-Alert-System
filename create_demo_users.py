import sqlite3
import bcrypt
from datetime import datetime

# Use the correct database path
conn = sqlite3.connect('database/database/roadsafenet.db')
cursor = conn.cursor()

# Demo users data (from KLCC area)
demo_users = [
    {
        'username': 'hospital_kl_demo',
        'email': 'hospital.kl@roadsafenet.demo',
        'password': 'demo123',
        'full_name': 'Hospital Kuala Lumpur',
        'phone': '+60 3-2615 5555',
        'address': 'Jalan Pahang',
        'city': 'Kuala Lumpur',
        'state': 'Wilayah Persekutuan',
        'postal_code': '50586',
        'latitude': 3.1466,
        'longitude': 101.6958,
        'role': 'operator'
    },
    {
        'username': 'police_klcc_demo',
        'email': 'police.klcc@roadsafenet.demo',
        'password': 'demo123',
        'full_name': 'Balai Polis KLCC',
        'phone': '+60 3-2166 6222',
        'address': 'Jalan Ampang',
        'city': 'Kuala Lumpur',
        'state': 'Wilayah Persekutuan',
        'postal_code': '50450',
        'latitude': 3.1583,
        'longitude': 101.7119,
        'role': 'operator'
    },
    {
        'username': 'ambulance_klcc_demo',
        'email': 'ambulance.klcc@roadsafenet.demo',
        'password': 'demo123',
        'full_name': 'Mobile Ambulance KLCC',
        'phone': '+60 3-2698 9999',
        'address': 'Jalan Pinang',
        'city': 'Kuala Lumpur',
        'state': 'Wilayah Persekutuan',
        'postal_code': '50450',
        'latitude': 3.1500,
        'longitude': 101.6800,
        'role': 'operator'
    }
]

print('\n🚀 Creating demo users for KLCC area...\n')

for user_data in demo_users:
    # Check if user already exists
    cursor.execute('SELECT id FROM User WHERE username = ?', (user_data['username'],))
    existing = cursor.fetchone()
    
    if existing:
        print(f'⚠️  User {user_data["username"]} already exists (ID: {existing[0]})')
        continue
    
    # Hash password
    password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Insert user (using only columns that exist in the database)
    cursor.execute('''
        INSERT INTO User (
            username, email, password_hash, full_name,
            city, latitude, longitude, role, is_active,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['username'],
        user_data['email'],
        password_hash,
        user_data['full_name'],
        user_data['city'],
        user_data['latitude'],
        user_data['longitude'],
        user_data['role'],
        True,  # is_active
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    user_id = cursor.lastrowid
    print(f'✅ Created user: {user_data["username"]} (ID: {user_id})')
    print(f'   📍 Location: {user_data["city"]} ({user_data["latitude"]}, {user_data["longitude"]})')
    print(f'   👤 Full Name: {user_data["full_name"]}')
    print(f'   🔑 Password: {user_data["password"]}')
    print()

conn.commit()
conn.close()

print('\n✅ Demo users created successfully!')
print('\n📝 Login credentials:')
print('   Username: hospital_kl_demo  | Password: demo123')
print('   Username: police_klcc_demo  | Password: demo123')
print('   Username: ambulance_klcc_demo | Password: demo123')
print('\n🌐 Login at: http://127.0.0.1:8050/login\n')
