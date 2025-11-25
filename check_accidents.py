"""Check accident records in database"""
import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()
    
    accidents = await db.accident.find_many(take=10, order={'timestamp': 'desc'})
    
    print(f"\n{'='*60}")
    print(f"Total Accidents Detected: {len(accidents)}")
    print(f"{'='*60}\n")
    
    for i, acc in enumerate(accidents, 1):
        print(f"[{i}] Accident ID: {acc.id}")
        print(f"    Time: {acc.timestamp}")
        print(f"    Location: {acc.location_name}")
        print(f"    City: {acc.city}, {acc.country}")
        print(f"    Severity: {acc.severity.upper()}")
        print(f"    Confidence: {acc.confidence:.2%}")
        print(f"    Frame: {acc.video_frame}")
        print(f"    Status: {acc.status}")
        print(f"    Image: {acc.image_path}")
        print()
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
