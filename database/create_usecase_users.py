"""
Create user accounts for all actors in the use case diagram
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from prisma import Prisma
import bcrypt as bcrypt_lib


async def create_usecase_users():
    """Create user accounts for all use case actors"""
    db = Prisma()
    await db.connect()
    
    try:
        # Define users for each actor in the use case diagram
        users = [
            {
                "username": "police",
                "email": "police@roadsafenet.com",
                "password": "police123",
                "full_name": "Police Department",
                "role": "operator",  # Can view and respond to incidents
            },
            {
                "username": "ambulance",
                "email": "ambulance@roadsafenet.com",
                "password": "ambulance123",
                "full_name": "Ambulance Services",
                "role": "operator",
            },
            {
                "username": "hospital",
                "email": "hospital@roadsafenet.com",
                "password": "hospital123",
                "full_name": "Hospital Emergency",
                "role": "operator",
            },
            {
                "username": "traffic_authority",
                "email": "traffic@roadsafenet.com",
                "password": "traffic123",
                "full_name": "Traffic Authority",
                "role": "admin",  # Can manage system and view analytics
            },
            {
                "username": "resident1",
                "email": "resident1@roadsafenet.com",
                "password": "resident123",
                "full_name": "John Resident",
                "role": "viewer",  # Can only view public information
            },
            {
                "username": "resident2",
                "email": "resident2@roadsafenet.com",
                "password": "resident123",
                "full_name": "Sarah Resident",
                "role": "viewer",
            },
            {
                "username": "admin",
                "email": "admin@roadsafenet.com",
                "password": "admin123",
                "full_name": "System Administrator",
                "role": "admin",
            },
        ]
        
        print("🔄 Creating user accounts for use case actors...\n")
        print("=" * 80)
        
        created_count = 0
        existing_count = 0
        
        for user_data in users:
            # Check if user already exists
            existing_user = await db.user.find_first(
                where={"username": user_data["username"]}
            )
            
            if existing_user:
                print(f"⏭️  User '{user_data['username']}' already exists - skipping")
                existing_count += 1
                continue
            
            # Hash password using bcrypt
            password_bytes = user_data["password"].encode('utf-8')
            hashed = bcrypt_lib.hashpw(password_bytes, bcrypt_lib.gensalt())
            
            # Create user
            new_user = await db.user.create(
                data={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password_hash": hashed.decode('utf-8'),
                    "full_name": user_data["full_name"],
                    "role": user_data["role"],
                    "is_active": True
                }
            )
            
            print(f"✅ Created user: {new_user.username:20s} | Role: {new_user.role:10s} | Email: {new_user.email}")
            created_count += 1
        
        print("=" * 80)
        print("\n📊 Summary:")
        print(f"   ✅ Created: {created_count} users")
        print(f"   ⏭️  Existing: {existing_count} users")
        print(f"   📋 Total: {len(users)} users")
        
        print("\n" + "=" * 80)
        print("🔐 LOGIN CREDENTIALS")
        print("=" * 80)
        print("\n📋 Use Case Actors - Login Details:\n")
        
        for user_data in users:
            print(f"👤 {user_data['full_name']}")
            print(f"   Username: {user_data['username']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Role:     {user_data['role']}")
            print(f"   Email:    {user_data['email']}")
            print()
        
        print("=" * 80)
        print("\n💡 Role Permissions:")
        print("   • admin    - Full system access (Analytics, Users, Settings, System Management)")
        print("   • operator - View incidents, respond to emergencies (Emergency Notification System)")
        print("   • viewer   - View public dashboard and analytics only (Web Dashboard)")
        print("\n✅ All use case actor accounts created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating users: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(create_usecase_users())
