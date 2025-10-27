"""
Enhanced Geolocation Service with Emergency Services Finder for Malaysia
Finds nearby hospitals, police stations, and ambulance services
"""

import requests
import time
import random
from typing import Dict, List, Optional, Tuple
from math import radians, sin, cos, sqrt, atan2
from config import Config
from utils.logger import logger


class EmergencyServicesLocator:
    """Find nearby emergency services in Malaysia"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.user_agent = Config.NOMINATIM_USER_AGENT
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
        # Malaysia demo locations (major cities) with real coordinates
        self.malaysia_locations = [
            {"name": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869, "state": "Federal Territory"},
            {"name": "Petaling Jaya", "lat": 3.1073, "lon": 101.6067, "state": "Selangor"},
            {"name": "Shah Alam", "lat": 3.0733, "lon": 101.5185, "state": "Selangor"},
            {"name": "Johor Bahru", "lat": 1.4927, "lon": 103.7414, "state": "Johor"},
            {"name": "Georgetown", "lat": 5.4141, "lon": 100.3288, "state": "Penang"},
            {"name": "Ipoh", "lat": 4.5975, "lon": 101.0901, "state": "Perak"},
            {"name": "Malacca City", "lat": 2.1896, "lon": 102.2501, "state": "Malacca"},
            {"name": "Kota Kinabalu", "lat": 5.9804, "lon": 116.0735, "state": "Sabah"},
            {"name": "Kuching", "lat": 1.5535, "lon": 110.3593, "state": "Sarawak"},
        ]
        
        # Demo emergency services data for Malaysia
        self.demo_hospitals = [
            {
                "name": "Hospital Kuala Lumpur",
                "address": "Jalan Pahang, 50586 Kuala Lumpur",
                "phone": "+60 3-2615 5555",
                "city": "Kuala Lumpur",
                "state": "Federal Territory"
            },
            {
                "name": "Hospital Universiti Kebangsaan Malaysia (HUKM)",
                "address": "Jalan Yaacob Latif, 56000 Cheras, Kuala Lumpur",
                "phone": "+60 3-9145 5555",
                "city": "Cheras",
                "state": "Federal Territory"
            },
            {
                "name": "Hospital Pantai Kuala Lumpur",
                "address": "8, Jalan Bukit Pantai, 59100 Kuala Lumpur",
                "phone": "+60 3-2296 0888",
                "city": "Kuala Lumpur",
                "state": "Federal Territory"
            },
            {
                "name": "Hospital Ampang",
                "address": "Jalan Mewah Utara, Pandan Mewah, 68000 Ampang",
                "phone": "+60 3-4289 5000",
                "city": "Ampang",
                "state": "Selangor"
            }
        ]
        
        self.demo_police_stations = [
            {
                "name": "Balai Polis Sentul",
                "address": "Jalan Sentul Pasar, 51100 Kuala Lumpur",
                "phone": "+60 3-4042 2222",
                "city": "Kuala Lumpur",
                "state": "Federal Territory"
            },
            {
                "name": "Balai Polis Wangsa Maju",
                "address": "Section 2, Wangsa Maju, 53300 Kuala Lumpur",
                "phone": "+60 3-4142 0222",
                "city": "Wangsa Maju",
                "state": "Federal Territory"
            },
            {
                "name": "Ibu Pejabat Polis Daerah (IPD) Kuala Lumpur",
                "address": "Jalan Hang Tuah, 50100 Kuala Lumpur",
                "phone": "+60 3-2115 9999",
                "city": "Kuala Lumpur",
                "state": "Federal Territory"
            }
        ]
        
        self.demo_ambulance_services = [
            {
                "name": "999 Emergency Ambulance Service",
                "phone": "999",
                "city": "Nationwide",
                "state": "Malaysia"
            },
            {
                "name": "St John Ambulance Malaysia",
                "address": "Jalan Tun Ismail, 50480 Kuala Lumpur",
                "phone": "+60 3-2691 8880",
                "city": "Kuala Lumpur",
                "state": "Federal Territory"
            },
            {
                "name": "Red Crescent Malaysia",
                "address": "JKR 829, Jalan Belfield, 50460 Kuala Lumpur",
                "phone": "+60 3-2161 0600",
                "city": "Kuala Lumpur",
                "state": "Federal Territory"
            }
        ]
    
    def _rate_limit(self):
        """Enforce rate limiting for API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def get_random_malaysia_location(self) -> Dict:
        """Get a random demo location in Malaysia"""
        location = random.choice(self.malaysia_locations)
        # Add small random offset to coordinates
        lat_offset = random.uniform(-0.02, 0.02)
        lon_offset = random.uniform(-0.02, 0.02)
        
        return {
            "city": location["name"],
            "state": location["state"],
            "country": "Malaysia",
            "latitude": location["lat"] + lat_offset,
            "longitude": location["lon"] + lon_offset,
            "full_address": f"Accident Location near {location['name']}, {location['state']}, Malaysia"
        }
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """
        Convert coordinates to address using Nominatim API
        Falls back to demo data if API fails
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with address details
        """
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1
            }
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            address = data.get('address', {})
            
            return {
                'full_address': data.get('display_name', 'Unknown'),
                'road': address.get('road', ''),
                'suburb': address.get('suburb', ''),
                'city': address.get('city', address.get('town', address.get('village', ''))),
                'state': address.get('state', ''),
                'postcode': address.get('postcode', ''),
                'country': address.get('country', 'Malaysia'),
                'latitude': latitude,
                'longitude': longitude
            }
            
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            # Return demo location if API fails
            return self.get_random_malaysia_location()
    
    def find_nearest_emergency_services(
        self, 
        latitude: float, 
        longitude: float
    ) -> Dict[str, List[Dict]]:
        """
        Find nearest hospitals, police stations, and ambulance services
        Uses demo data for Malaysia
        
        Args:
            latitude: Accident location latitude
            longitude: Accident location longitude
            
        Returns:
            Dictionary with lists of nearby emergency services
        """
        
        # Calculate distances and sort
        hospitals = []
        for hospital in self.demo_hospitals:
            # Assign approximate coordinates near major cities
            h_lat = latitude + random.uniform(-0.03, 0.03)
            h_lon = longitude + random.uniform(-0.03, 0.03)
            distance = self.calculate_distance(latitude, longitude, h_lat, h_lon)
            
            hospitals.append({
                **hospital,
                'latitude': h_lat,
                'longitude': h_lon,
                'distance_km': round(distance, 2)
            })
        
        police_stations = []
        for station in self.demo_police_stations:
            p_lat = latitude + random.uniform(-0.02, 0.02)
            p_lon = longitude + random.uniform(-0.02, 0.02)
            distance = self.calculate_distance(latitude, longitude, p_lat, p_lon)
            
            police_stations.append({
                **station,
                'latitude': p_lat,
                'longitude': p_lon,
                'distance_km': round(distance, 2)
            })
        
        ambulances = []
        for ambulance in self.demo_ambulance_services:
            a_lat = latitude + random.uniform(-0.01, 0.01)
            a_lon = longitude + random.uniform(-0.01, 0.01)
            distance = self.calculate_distance(latitude, longitude, a_lat, a_lon)
            
            ambulances.append({
                **ambulance,
                'latitude': a_lat,
                'longitude': a_lon,
                'distance_km': round(distance, 2)
            })
        
        # Sort by distance
        hospitals.sort(key=lambda x: x['distance_km'])
        police_stations.sort(key=lambda x: x['distance_km'])
        ambulances.sort(key=lambda x: x['distance_km'])
        
        return {
            'hospitals': hospitals[:3],  # Top 3 nearest
            'police_stations': police_stations[:2],  # Top 2 nearest
            'ambulances': ambulances[:2]  # Top 2 nearest
        }
    
    def calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        distance = R * c
        return distance
    
    def generate_google_maps_link(self, latitude: float, longitude: float) -> str:
        """Generate Google Maps link for location"""
        return f"https://www.google.com/maps?q={latitude},{longitude}"
    
    def generate_route_link(
        self, 
        from_lat: float, 
        from_lon: float, 
        to_lat: float, 
        to_lon: float
    ) -> str:
        """Generate Google Maps route link from one location to another"""
        return f"https://www.google.com/maps/dir/{from_lat},{from_lon}/{to_lat},{to_lon}"
