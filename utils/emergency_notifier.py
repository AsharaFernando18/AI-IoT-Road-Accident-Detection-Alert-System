"""
Emergency Services Notifier
Finds nearest emergency services and sends notifications when accidents occur
"""

import math
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmergencyNotifier:
    """Handles finding and notifying nearest emergency services"""
    
    def __init__(self):
        self.notification_history = []
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def find_nearest_services(self, accident_lat: float, accident_lon: float, 
                             hospitals: List[Dict], police_stations: List[Dict], 
                             ambulances: List[Dict]) -> Dict:
        """
        Find nearest hospital, police station, and ambulance to accident location
        
        Returns dict with nearest services and their distances
        """
        result = {
            'hospital': None,
            'police_station': None,
            'ambulance': None,
            'distances': {}
        }
        
        # Find nearest hospital
        if hospitals:
            nearest_hospital = min(
                hospitals,
                key=lambda h: self.calculate_distance(
                    accident_lat, accident_lon, h['lat'], h['lon']
                )
            )
            distance = self.calculate_distance(
                accident_lat, accident_lon, 
                nearest_hospital['lat'], nearest_hospital['lon']
            )
            result['hospital'] = nearest_hospital
            result['distances']['hospital'] = round(distance, 2)
        
        # Find nearest police station
        if police_stations:
            nearest_police = min(
                police_stations,
                key=lambda p: self.calculate_distance(
                    accident_lat, accident_lon, p['lat'], p['lon']
                )
            )
            distance = self.calculate_distance(
                accident_lat, accident_lon,
                nearest_police['lat'], nearest_police['lon']
            )
            result['police_station'] = nearest_police
            result['distances']['police_station'] = round(distance, 2)
        
        # Find nearest ambulance
        if ambulances:
            nearest_ambulance = min(
                ambulances,
                key=lambda a: self.calculate_distance(
                    accident_lat, accident_lon, a['lat'], a['lon']
                )
            )
            distance = self.calculate_distance(
                accident_lat, accident_lon,
                nearest_ambulance['lat'], nearest_ambulance['lon']
            )
            result['ambulance'] = nearest_ambulance
            result['distances']['ambulance'] = round(distance, 2)
        
        return result
    
    def create_notification_message(self, accident_location: str, 
                                   accident_lat: float, accident_lon: float,
                                   service_type: str, service_name: str, 
                                   distance: float) -> str:
        """Create notification message for emergency service"""
        
        messages = {
            'hospital': f"""
🚨 EMERGENCY ALERT - ACCIDENT REPORTED 🚨

Location: {accident_location}
Coordinates: {accident_lat:.6f}, {accident_lon:.6f}
Distance from {service_name}: {distance} km

MEDICAL ASSISTANCE REQUIRED
Please dispatch ambulance immediately!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: RoadSafeNet AI Detection System
""",
            'police_station': f"""
🚨 TRAFFIC ACCIDENT ALERT 🚨

Location: {accident_location}
Coordinates: {accident_lat:.6f}, {accident_lon:.6f}
Distance from {service_name}: {distance} km

POLICE ASSISTANCE REQUIRED
Traffic control and investigation needed

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: RoadSafeNet AI Detection System
""",
            'ambulance': f"""
🚨 URGENT - ACCIDENT VICTIM ASSISTANCE 🚨

Location: {accident_location}
Coordinates: {accident_lat:.6f}, {accident_lon:.6f}
Your Distance: {distance} km

IMMEDIATE DISPATCH REQUIRED
Proceed to accident location immediately!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: RoadSafeNet AI Detection System
"""
        }
        
        return messages.get(service_type, "Emergency notification")
    
    def send_notifications(self, accident_data: Dict, nearest_services: Dict) -> List[Dict]:
        """
        Send notifications to nearest emergency services
        
        Returns list of sent notifications
        """
        notifications = []
        timestamp = datetime.now()
        
        accident_location = accident_data.get('location_name', 'Unknown Location')
        accident_lat = accident_data.get('latitude')
        accident_lon = accident_data.get('longitude')
        
        # Send to hospital
        if nearest_services['hospital']:
            hospital = nearest_services['hospital']
            message = self.create_notification_message(
                accident_location, accident_lat, accident_lon,
                'hospital', hospital['name'],
                nearest_services['distances']['hospital']
            )
            
            notification = {
                'id': len(self.notification_history) + 1,
                'type': 'hospital',
                'service_name': hospital['name'],
                'distance': nearest_services['distances']['hospital'],
                'message': message,
                'status': 'sent',
                'timestamp': timestamp.isoformat()
            }
            notifications.append(notification)
            self.notification_history.append(notification)
            logger.info(f"✓ Notification sent to {hospital['name']}")
        
        # Send to police station
        if nearest_services['police_station']:
            police = nearest_services['police_station']
            message = self.create_notification_message(
                accident_location, accident_lat, accident_lon,
                'police_station', police['name'],
                nearest_services['distances']['police_station']
            )
            
            notification = {
                'id': len(self.notification_history) + 1,
                'type': 'police_station',
                'service_name': police['name'],
                'distance': nearest_services['distances']['police_station'],
                'message': message,
                'status': 'sent',
                'timestamp': timestamp.isoformat()
            }
            notifications.append(notification)
            self.notification_history.append(notification)
            logger.info(f"✓ Notification sent to {police['name']}")
        
        # Send to ambulance
        if nearest_services['ambulance']:
            ambulance = nearest_services['ambulance']
            message = self.create_notification_message(
                accident_location, accident_lat, accident_lon,
                'ambulance', ambulance['id'],
                nearest_services['distances']['ambulance']
            )
            
            notification = {
                'id': len(self.notification_history) + 1,
                'type': 'ambulance',
                'service_name': f"Ambulance {ambulance['id']}",
                'distance': nearest_services['distances']['ambulance'],
                'message': message,
                'status': 'sent',
                'timestamp': timestamp.isoformat()
            }
            notifications.append(notification)
            self.notification_history.append(notification)
            logger.info(f"✓ Notification sent to Ambulance {ambulance['id']}")
        
        return notifications
    
    def get_notification_history(self) -> List[Dict]:
        """Get all sent notifications"""
        return self.notification_history
