"""
Create Missing User Accounts from Use Case Diagram
- policy_makers (viewer role) - for analytics and reporting
- researchers (viewer role) - for data analysis and trends
"""

import asyncio
import bcrypt
from prisma import Prisma

# Database connection
db = Prisma()

# Users to create based on use case diagram
users = [
    {
        "username": "policy_makers",
        "password": "policy123",
        "email": "policy_makers@roadsafenet.com",
        "full_name": "Policy Makers",
        "role": "viewer"  # Can view analytics, reports, heat maps, risk areas
    },
    {
        "username": "researchers",
        "password": "research123",
        "email": "researchers@roadsafenet.com",
        "full_name": "Researchers",
        "role": "viewer"  # Can analyze trends, store data, view analytics
    },
]

async def create_users():
    """Create missing user accounts"""
    await db.connect()
    
    created_count = 0
    existing_count = 0
    
    print("\n" + "="*70)
    print("🎭 Creating Missing Actors from Use Case Diagram")
    print("="*70 + "\n")
    
    for user_data in users:
        # Check if user already exists
        existing_user = await db.user.find_unique(
            where={"username": user_data["username"]}
        )
        
        if existing_user:
            print(f"⏭️  User '{user_data['username']}' already exists - skipping")
            existing_count += 1
            continue
        
        # Hash password
        password_hash = bcrypt.hashpw(
            user_data["password"].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Create user
        user = await db.user.create(
            data={
                "username": user_data["username"],
                "email": user_data["email"],
                "password_hash": password_hash,
                "full_name": user_data["full_name"],
                "role": user_data["role"],
                "is_active": True
            }
        )
        
        print(f"✅ Created user: {user.username:<20} | Role: {user.role:<10} | Email: {user.email}")
        created_count += 1
    
    print("\n" + "="*70)
    print("📊 Summary:")
    print(f"   ✅ Created: {created_count} users")
    print(f"   ⏭️  Existing: {existing_count} users")
    
    # Get total user count
    total_users = await db.user.count()
    print(f"   📋 Total: {total_users} users")
    print("="*70)
    
    # Display all user credentials
    print("\n🔑 Login Credentials for All Actors:")
    print("="*70)
    
    all_users = await db.user.find_many(order={"role": "asc", "username": "asc"})
    
    # Map to show passwords (only for display purposes)
    password_map = {
        "admin": "admin123",
        "traffic_authority": "traffic123",
        "police": "police123",
        "ambulance": "ambulance123",
        "hospital": "hospital123",
        "resident1": "resident123",
        "resident2": "resident123",
        "policy_makers": "policy123",
        "researchers": "research123"
    }
    
    for user in all_users:
        password = password_map.get(user.username, "***")
        role_badge = {
            "admin": "🔐 Admin",
            "operator": "👮 Operator",
            "viewer": "👁️  Viewer"
        }.get(user.role, user.role)
        
        print(f"   {user.username:<20} / {password:<15} → {role_badge}")
    
    print("="*70 + "\n")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(create_users())
