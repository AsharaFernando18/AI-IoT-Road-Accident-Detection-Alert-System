"""
Utility module for finding nearest emergency responders
Uses Haversine formula to calculate distances and find closest responders
"""

import sqlite3
import os
from math import radians, sin, cos, sqrt, atan2
from typing import List, Dict, Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Radius of earth in kilometers
    radius = 6371
    distance = radius * c
    
    return distance


def get_database_path() -> str:
    """Get the path to the database file"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')


def find_nearest_responders(
    accident_lat: float, 
    accident_lon: float, 
    responder_type: str,
    limit: int = 3
) -> List[Dict]:
    """
    Find the nearest emergency responders of a specific type to an accident location
    
    Args:
        accident_lat: Latitude of accident location
        accident_lon: Longitude of accident location
        responder_type: Type of responder ('police', 'ambulance', or 'hospital')
        limit: Maximum number of responders to return (default: 3)
    
    Returns:
        List of dictionaries containing responder information with distance
        Format: [
            {
                'id': int,
                'username': str,
                'latitude': float,
                'longitude': float,
                'telegram_bot_token': str,
                'distance_km': float
            },
            ...
        ]
    """
    db_path = get_database_path()
    responders = []
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Query active responders with valid location, bot token, and chat ID
            # Search for username that starts with the responder type (e.g., 'hospital' matches 'hospital_kl_demo')
            cursor.execute('''
                SELECT id, username, latitude, longitude, telegram_bot_token, telegram_chat_id
                FROM User
                WHERE (username = ? OR username LIKE ?)
                  AND is_active = 1
                  AND latitude IS NOT NULL
                  AND longitude IS NOT NULL
                  AND telegram_bot_token IS NOT NULL
                  AND telegram_bot_token != ''
                  AND telegram_chat_id IS NOT NULL
                  AND telegram_chat_id != ''
            ''', (responder_type, f'{responder_type}_%'))
            
            results = cursor.fetchall()
            
            # Calculate distance for each responder
            for row in results:
                responder_id, username, lat, lon, token, chat_id = row
                distance = haversine_distance(accident_lat, accident_lon, lat, lon)
                
                responders.append({
                    'id': responder_id,
                    'username': username,
                    'latitude': lat,
                    'longitude': lon,
                    'telegram_bot_token': token,
                    'telegram_chat_id': chat_id,
                    'distance_km': round(distance, 2)
                })
            
            # Sort by distance and limit results
            responders.sort(key=lambda x: x['distance_km'])
            return responders[:limit]
            
    except Exception as e:
        print(f"Error finding nearest responders: {e}")
        return []


def find_all_nearest_responders(
    accident_lat: float,
    accident_lon: float,
    limit_per_type: int = 3
) -> Dict[str, List[Dict]]:
    """
    Find the nearest emergency responders of all types to an accident location
    
    Args:
        accident_lat: Latitude of accident location
        accident_lon: Longitude of accident location
        limit_per_type: Maximum number of responders per type (default: 3)
    
    Returns:
        Dictionary with responder types as keys and lists of responder info as values
        Format: {
            'police': [...],
            'ambulance': [...],
            'hospital': [...]
        }
    """
    responder_types = ['police', 'ambulance', 'hospital']
    all_responders = {}
    
    for responder_type in responder_types:
        nearest = find_nearest_responders(
            accident_lat, 
            accident_lon, 
            responder_type, 
            limit_per_type
        )
        all_responders[responder_type] = nearest
    
    return all_responders


def get_responder_count() -> Dict[str, int]:
    """
    Get count of active responders by type who have bot tokens configured
    
    Returns:
        Dictionary with responder types and their counts
        Format: {'police': 1, 'ambulance': 1, 'hospital': 1}
    """
    db_path = get_database_path()
    counts = {}
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for responder_type in ['police', 'ambulance', 'hospital']:
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM User
                    WHERE (username = ? OR username LIKE ?)
                      AND is_active = 1
                      AND latitude IS NOT NULL
                      AND longitude IS NOT NULL
                      AND telegram_bot_token IS NOT NULL
                      AND telegram_bot_token != ''
                      AND telegram_chat_id IS NOT NULL
                      AND telegram_chat_id != ''
                ''', (responder_type, f'{responder_type}_%'))
                
                count = cursor.fetchone()[0]
                counts[responder_type] = count
                
    except Exception as e:
        print(f"Error getting responder counts: {e}")
        return {'police': 0, 'ambulance': 0, 'hospital': 0}
    
    return counts


if __name__ == '__main__':
    # Test the functions
    print("Testing Nearest Responders Finder\n")
    
    # Test location: Kuala Lumpur city center
    test_lat = 3.1390
    test_lon = 101.6869
    
    print(f"Test accident location: {test_lat}, {test_lon}\n")
    
    # Get responder counts
    print("Active responders with bot tokens:")
    counts = get_responder_count()
    for responder_type, count in counts.items():
        print(f"  {responder_type.capitalize()}: {count}")
    print()
    
    # Find nearest responders of each type
    all_nearest = find_all_nearest_responders(test_lat, test_lon, limit_per_type=3)
    
    for responder_type, responders in all_nearest.items():
        print(f"{responder_type.capitalize()} (nearest {len(responders)}):")
        if responders:
            for i, responder in enumerate(responders, 1):
                print(f"  {i}. {responder['username']} - {responder['distance_km']} km away")
                print(f"     Location: ({responder['latitude']}, {responder['longitude']})")
                print(f"     Bot Token: {responder['telegram_bot_token'][:20]}...")
        else:
            print("  No responders found with valid configuration")
        print()
