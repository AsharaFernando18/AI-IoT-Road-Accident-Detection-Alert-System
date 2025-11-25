"""
Update accident locations with city information
This script adds city data to existing accidents for location-based filtering
"""

import sqlite3
import random
import os

def update_accident_locations():
    """Update accidents with city data based on their coordinates"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'roadsafenet.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # City boundaries (approximate)
    city_boundaries = {
        'Kuala Lumpur': {'lat_min': 3.0, 'lat_max': 3.3, 'lon_min': 101.5, 'lon_max': 101.8},
        'Penang': {'lat_min': 5.2, 'lat_max': 5.5, 'lon_min': 100.2, 'lon_max': 100.5},
        'Johor Bahru': {'lat_min': 1.4, 'lat_max': 1.6, 'lon_min': 103.6, 'lon_max': 103.9},
        'Ipoh': {'lat_min': 4.5, 'lat_max': 4.7, 'lon_min': 100.9, 'lon_max': 101.2},
        'Melaka': {'lat_min': 2.1, 'lat_max': 2.3, 'lon_min': 102.1, 'lon_max': 102.4},
        'Kuching': {'lat_min': 1.4, 'lat_max': 1.6, 'lon_min': 110.2, 'lon_max': 110.5},
    }
    
    # Get all accidents
    cursor.execute('SELECT id, location_lat, location_lon FROM Accident')
    accidents = cursor.fetchall()
    print(f"\nFound {len(accidents)} accidents in database")
    
    updated_count = 0
    cities = list(city_boundaries.keys())
    
    for accident_id, lat, lon in accidents:
        # Try to match city by coordinates
        matched_city = None
        for city, bounds in city_boundaries.items():
            if (bounds['lat_min'] <= lat <= bounds['lat_max'] and 
                bounds['lon_min'] <= lon <= bounds['lon_max']):
                matched_city = city
                break
        
        # If no match, assign random city for testing purposes
        if not matched_city:
            matched_city = random.choice(cities)
        
        # Update accident with city
        cursor.execute(
            'UPDATE Accident SET city = ?, country = ? WHERE id = ?',
            (matched_city, 'Malaysia', accident_id)
        )
        
        updated_count += 1
        print(f"✅ Accident #{accident_id} -> {matched_city}")
    
    conn.commit()
    conn.close()
    print(f"\n✨ Updated {updated_count} accidents with city information!")
    print("Incidents will now be filtered by user's city\n")

if __name__ == "__main__":
    update_accident_locations()
