"""
Update user locations for location-based filtering
This script adds city and coordinates to existing users
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from prisma import Prisma

async def update_user_locations():
    """Update users with city and location data"""
    db = Prisma()
    await db.connect()
    
    # Define city locations in Malaysia
    city_data = {
        'Kuala Lumpur': {'lat': 3.1390, 'lon': 101.6869, 'state': 'Federal Territory', 'country': 'Malaysia'},
        'Penang': {'lat': 5.4164, 'lon': 100.3327, 'state': 'Penang', 'country': 'Malaysia'},
        'Johor Bahru': {'lat': 1.4927, 'lon': 103.7414, 'state': 'Johor', 'country': 'Malaysia'},
        'Ipoh': {'lat': 4.5975, 'lon': 101.0901, 'state': 'Perak', 'country': 'Malaysia'},
        'Melaka': {'lat': 2.1896, 'lon': 102.2501, 'state': 'Melaka', 'country': 'Malaysia'},
        'Kuching': {'lat': 1.5535, 'lon': 110.3593, 'state': 'Sarawak', 'country': 'Malaysia'},
    }
    
    # Get all users
    users = await db.user.find_many()
    print(f"\nFound {len(users)} users in database")
    
    # Assign cities to users (round-robin for variety)
    cities = list(city_data.keys())
    
    for i, user in enumerate(users):
        # Skip admin (keep them with all locations access)
        if user.role == 'admin':
            print(f"Skipping {user.username} (admin) - will see all locations")
            continue
        
        # Assign city to operators and viewers
        city = cities[i % len(cities)]
        location = city_data[city]
        
        await db.user.update(
            where={'id': user.id},
            data={
                'city': city,
                'state': location['state'],
                'country': location['country'],
                'latitude': location['lat'],
                'longitude': location['lon']
            }
        )
        
        print(f"✅ Updated {user.username} ({user.role}) -> {city} ({location['lat']}, {location['lon']})")
    
    await db.disconnect()
    print("\n✨ User locations updated successfully!")
    print("Users will now see incidents filtered by their city")
    print("Admins will continue to see all incidents\n")

if __name__ == "__main__":
    asyncio.run(update_user_locations())
