"""
Geolocation Service using OpenStreetMap Nominatim API
Reverse geocoding and location lookup for accident detection
"""

import requests
from typing import Dict, Optional, Tuple
import logging
import time
from functools import lru_cache
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import Config

logger = logging.getLogger(__name__)


class GeolocationService:
    """
    Service for reverse geocoding and location lookup using OpenStreetMap
    """
    
    def __init__(self):
        """Initialize geolocation service"""
        self.base_url = Config.NOMINATIM_BASE_URL
        self.user_agent = Config.NOMINATIM_USER_AGENT
        self.cache = {}
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Nominatim requires 1 second between requests
    
    def _wait_for_rate_limit(self):
        """Ensure compliance with Nominatim rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    @lru_cache(maxsize=1000)
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Convert coordinates to address using reverse geocoding
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with address details or None if failed
        """
        # Check cache
        cache_key = f"{latitude:.6f},{longitude:.6f}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        # Rate limiting
        self._wait_for_rate_limit()
        
        try:
            url = f"{self.base_url}/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
                "zoom": 18
            }
            headers = {
                "User-Agent": self.user_agent
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                logger.error(f"Geocoding error: {data['error']}")
                return None
            
            # Extract address components
            address = data.get("address", {})
            
            result = {
                "latitude": latitude,
                "longitude": longitude,
                "display_name": data.get("display_name", "Unknown Location"),
                "road": address.get("road", ""),
                "suburb": address.get("suburb", ""),
                "city": address.get("city") or address.get("town") or address.get("village", ""),
                "state": address.get("state", ""),
                "country": address.get("country", ""),
                "postcode": address.get("postcode", ""),
                "country_code": address.get("country_code", "").upper(),
                "formatted_address": self._format_address(address)
            }
            
            # Cache result
            self.cache[cache_key] = result
            
            logger.info(f"✓ Reverse geocoded: {result['formatted_address']}")
            
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to reverse geocode ({latitude}, {longitude}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in reverse geocoding: {e}")
            return None
    
    def _format_address(self, address: Dict) -> str:
        """Format address components into readable string"""
        components = []
        
        if address.get("road"):
            components.append(address["road"])
        
        if address.get("suburb"):
            components.append(address["suburb"])
        
        city = address.get("city") or address.get("town") or address.get("village")
        if city:
            components.append(city)
        
        if address.get("state"):
            components.append(address["state"])
        
        if address.get("country"):
            components.append(address["country"])
        
        return ", ".join(components) if components else "Unknown Location"
    
    def forward_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates
        
        Args:
            address: Address string
            
        Returns:
            Tuple of (latitude, longitude) or None if failed
        """
        self._wait_for_rate_limit()
        
        try:
            url = f"{self.base_url}/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            headers = {
                "User-Agent": self.user_agent
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No results found for address: {address}")
                return None
            
            result = data[0]
            latitude = float(result["lat"])
            longitude = float(result["lon"])
            
            logger.info(f"✓ Geocoded '{address}' to ({latitude}, {longitude})")
            
            return latitude, longitude
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to geocode address '{address}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in geocoding: {e}")
            return None
    
    def get_distance(self, lat1: float, lon1: float, 
                     lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = (sin(delta_lat / 2) ** 2 + 
             cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        
        return distance
    
    def get_nearby_places(self, latitude: float, longitude: float, 
                          radius: int = 1000) -> list:
        """
        Get nearby places (hospitals, police stations, etc.)
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in meters
            
        Returns:
            List of nearby places
        """
        # This would require Overpass API for more detailed POI data
        # For now, return empty list
        # Future enhancement: Integrate Overpass API
        return []


if __name__ == "__main__":
    # Test geolocation service
    service = GeolocationService()
    
    # Test reverse geocoding (example coordinates)
    test_coords = [
        (40.7128, -74.0060),  # New York
        (51.5074, -0.1278),   # London
        (35.6762, 139.6503),  # Tokyo
    ]
    
    for lat, lon in test_coords:
        result = service.reverse_geocode(lat, lon)
        if result:
            print(f"\nCoordinates: ({lat}, {lon})")
            print(f"Address: {result['formatted_address']}")
            print(f"City: {result['city']}")
            print(f"Country: {result['country']}")
    
    # Test forward geocoding
    test_addresses = [
        "Times Square, New York",
        "Eiffel Tower, Paris"
    ]
    
    for address in test_addresses:
        coords = service.forward_geocode(address)
        if coords:
            print(f"\nAddress: {address}")
            print(f"Coordinates: {coords}")
