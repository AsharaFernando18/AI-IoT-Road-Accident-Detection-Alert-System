"""
Update researchers and policy_makers to see all locations
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from prisma import Prisma

async def update_users_all_locations():
    """Update specific users to see all locations"""
    db = Prisma()
    await db.connect()
    
    # Users that should see all locations
    users_to_update = ['researchers', 'policy_makers']
    
    for username in users_to_update:
        user = await db.user.find_first(where={'username': username})
        if user:
            await db.user.update(
                where={'id': user.id},
                data={
                    'city': None,
                    'state': None,
                    'country': None,
                    'latitude': None,
                    'longitude': None
                }
            )
            print(f"✅ Updated {username} to see all locations")
        else:
            print(f"⚠️ User {username} not found")
    
    await db.disconnect()
    print("\n✨ Update complete!")
    print("Researchers and policy_makers can now see all incidents from all cities\n")

if __name__ == "__main__":
    asyncio.run(update_users_all_locations())
