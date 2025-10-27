"""
Enhanced Emergency Notification Bot
Sends role-specific alerts to Hospital, Police, and Ambulance services
"""

import asyncio
import aiohttp
import aiofiles
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from config import Config
from utils.logger import logger
from utils.translation import TranslationService


class EmergencyNotificationBot:
    """Enhanced bot for sending role-specific emergency notifications"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.translator = TranslationService()
        
        # Cooldown tracking per responder
        self.last_alert_time = {}
        self.cooldown_minutes = 5
    
    async def send_ambulance_alert(
        self,
        chat_id: str,
        incident_data: Dict,
        language: str = "en"
    ) -> bool:
        """
        Send alert to ambulance with route and hospital info
        
        Args:
            chat_id: Telegram chat ID of ambulance service
            incident_data: Dictionary with incident details
            language: Target language for message
        """
        try:
            cooldown_key = f"ambulance_{chat_id}"
            if not self._check_cooldown(cooldown_key):
                logger.info(f"⏸️  Skipping ambulance alert (cooldown): {chat_id}")
                return False
            
            # Prepare message
            message = self._format_ambulance_message(incident_data, language)
            
            # Send text message
            await self._send_message(chat_id, message)
            
            # Send accident image
            if incident_data.get('image_path'):
                await self._send_photo(
                    chat_id,
                    incident_data['image_path'],
                    caption=f"🚨 Accident Scene - Severity: {incident_data['severity'].upper()}"
                )
            
            # Send location pin
            location = incident_data.get('location', {})
            if location.get('latitude') and location.get('longitude'):
                await self._send_location(
                    chat_id,
                    location['latitude'],
                    location['longitude']
                )
            
            # Send route to hospital
            route_link = incident_data.get('route_to_hospital')
            if route_link:
                route_msg = self._translate_if_needed(
                    f"🗺️ **Route to Hospital:**\n{route_link}",
                    language
                )
                await self._send_message(chat_id, route_msg)
            
            self._update_cooldown(cooldown_key)
            logger.info(f"✅ Ambulance alert sent to {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send ambulance alert: {e}")
            return False
    
    async def send_hospital_alert(
        self,
        chat_id: str,
        incident_data: Dict,
        language: str = "en"
    ) -> bool:
        """
        Send alert to hospital to prepare for incoming patient
        
        Args:
            chat_id: Telegram chat ID of hospital
            incident_data: Dictionary with incident details
            language: Target language for message
        """
        try:
            cooldown_key = f"hospital_{chat_id}"
            if not self._check_cooldown(cooldown_key):
                logger.info(f"⏸️  Skipping hospital alert (cooldown): {chat_id}")
                return False
            
            message = self._format_hospital_message(incident_data, language)
            
            # Send text message
            await self._send_message(chat_id, message)
            
            # Send accident image for medical assessment
            if incident_data.get('image_path'):
                await self._send_photo(
                    chat_id,
                    incident_data['image_path'],
                    caption="🏥 Incoming Emergency - Prepare Trauma Unit"
                )
            
            self._update_cooldown(cooldown_key)
            logger.info(f"✅ Hospital alert sent to {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send hospital alert: {e}")
            return False
    
    async def send_police_alert(
        self,
        chat_id: str,
        incident_data: Dict,
        language: str = "en"
    ) -> bool:
        """
        Send alert to police with video clip and investigation details
        
        Args:
            chat_id: Telegram chat ID of police station
            incident_data: Dictionary with incident details
            language: Target language for message
        """
        try:
            cooldown_key = f"police_{chat_id}"
            if not self._check_cooldown(cooldown_key):
                logger.info(f"⏸️  Skipping police alert (cooldown): {chat_id}")
                return False
            
            message = self._format_police_message(incident_data, language)
            
            # Send text message
            await self._send_message(chat_id, message)
            
            # Send accident image
            if incident_data.get('image_path'):
                await self._send_photo(
                    chat_id,
                    incident_data['image_path'],
                    caption="🚔 Accident Scene - Investigation Required"
                )
            
            # Send video clip if available (priority for police)
            if incident_data.get('video_clip_path'):
                await self._send_video(
                    chat_id,
                    incident_data['video_clip_path'],
                    caption="📹 CCTV Footage - 30 seconds clip"
                )
            
            # Send location
            location = incident_data.get('location', {})
            if location.get('latitude') and location.get('longitude'):
                await self._send_location(
                    chat_id,
                    location['latitude'],
                    location['longitude']
                )
            
            # Send maps link
            maps_link = incident_data.get('maps_link')
            if maps_link:
                link_msg = self._translate_if_needed(
                    f"📍 **Google Maps Link:**\n{maps_link}",
                    language
                )
                await self._send_message(chat_id, link_msg)
            
            self._update_cooldown(cooldown_key)
            logger.info(f"✅ Police alert sent to {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send police alert: {e}")
            return False
    
    def _format_ambulance_message(
        self,
        incident: Dict,
        language: str
    ) -> str:
        """Format message for ambulance service"""
        
        location = incident.get('location', {})
        hospital = incident.get('nearest_hospital', {})
        
        # Base message in English
        message = f"""
🚨 **EMERGENCY ALERT - AMBULANCE DISPATCH REQUIRED**

**Incident ID:** #{incident.get('id', 'N/A')}
**Time:** {incident.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
**Severity:** {incident.get('severity', 'UNKNOWN').upper()} ⚠️

📍 **Accident Location:**
{location.get('full_address', 'Location details pending')}
Coordinates: {location.get('latitude', 0):.6f}, {location.get('longitude', 0):.6f}

🏥 **Nearest Hospital:**
**{hospital.get('name', 'Hospital Kuala Lumpur')}**
📍 {hospital.get('address', 'Jalan Pahang, Kuala Lumpur')}
📞 {hospital.get('phone', '+60 3-XXXX XXXX')}
📏 Distance: {hospital.get('distance_km', 'N/A')} km

⏱️ **IMMEDIATE ACTION REQUIRED**
Estimated arrival time: ~{hospital.get('distance_km', 5) * 2} minutes

🗺️ Route and location will be sent in next messages.
"""
        
        # Translate if needed
        return self._translate_if_needed(message, language)
    
    def _format_hospital_message(self, incident: Dict, language: str) -> str:
        """Format message for hospital"""
        
        location = incident.get('location', {})
        
        message = f"""
🏥 **INCOMING EMERGENCY - PREPARE TRAUMA UNIT**

**Alert ID:** #{incident.get('id', 'N/A')}
**ETA:** 5-10 minutes
**Severity:** {incident.get('severity', 'UNKNOWN').upper()}

📋 **Incident Details:**
Type: Road Traffic Accident
Time: {incident.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
Location: {location.get('city', 'Unknown')}, {location.get('state', 'Malaysia')}

⚕️ **Preparation Needed:**
✓ Trauma team on standby
✓ Emergency room ready  
✓ Ambulance dispatched to scene

📍 **Accident Location:**
{location.get('full_address', 'Details pending')}

🚑 Ambulance en route with patient details to follow.
"""
        
        return self._translate_if_needed(message, language)
    
    def _format_police_message(
        self,
        incident: Dict,
        language: str
    ) -> str:
        """Format message for police station"""
        
        location = incident.get('location', {})
        
        message = f"""
🚔 **TRAFFIC ACCIDENT REPORTED - INVESTIGATION REQUIRED**

**Case ID:** #{incident.get('id', 'N/A')}
**Report Time:** {incident.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
**Severity:** {incident.get('severity', 'UNKNOWN').upper()}
**Status:** {incident.get('status', 'pending')}

📍 **Location:**
{location.get('full_address', 'Location details pending')}
City: {location.get('city', 'Unknown')}
State: {location.get('state', 'Malaysia')}
Coordinates: {location.get('latitude', 0):.6f}, {location.get('longitude', 0):.6f}

🔍 **Investigation Details:**
Type: {incident.get('type', 'Road Traffic Accident')}
Confidence: {incident.get('confidence', 0) * 100:.1f}%
Witnesses: To be determined
Traffic disruption: Likely

📹 **Evidence:**
- CCTV footage attached (30-second clip)
- Scene photographs attached
- Location coordinates provided

⚠️ **Action Required:**
1. Dispatch patrol to scene
2. Secure accident site
3. Begin investigation
4. Traffic management needed

🗺️ Google Maps link and video footage will be sent in next messages.
"""
        
        return self._translate_if_needed(message, language)
    
    def _translate_if_needed(self, text: str, language: str) -> str:
        """Translate text if target language is not English"""
        if language != "en":
            try:
                return self.translator.translate(text, target_lang=language)
            except Exception as e:
                logger.warning(f"Translation failed, using English: {e}")
                return text
        return text
    
    async def _send_message(self, chat_id: str, text: str) -> bool:
        """Send text message via Telegram API"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    return result.get('ok', False)
                    
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def _send_photo(
        self,
        chat_id: str,
        photo_path: str,
        caption: str = ""
    ) -> bool:
        """Send photo via Telegram API"""
        try:
            url = f"{self.base_url}/sendPhoto"
            
            # Check if file exists
            if not Path(photo_path).exists():
                logger.error(f"Photo file not found: {photo_path}")
                return False
            
            async with aiohttp.ClientSession() as session:
                async with aiofiles.open(photo_path, 'rb') as photo:
                    photo_data = await photo.read()
                    
                    form_data = aiohttp.FormData()
                    form_data.add_field('chat_id', chat_id)
                    form_data.add_field('photo', photo_data, filename='accident.jpg')
                    if caption:
                        form_data.add_field('caption', caption)
                    
                    async with session.post(url, data=form_data) as response:
                        result = await response.json()
                        return result.get('ok', False)
                        
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return False
    
    async def _send_video(
        self,
        chat_id: str,
        video_path: str,
        caption: str = ""
    ) -> bool:
        """Send video via Telegram API"""
        try:
            url = f"{self.base_url}/sendVideo"
            
            # Check if file exists
            if not Path(video_path).exists():
                logger.error(f"Video file not found: {video_path}")
                return False
            
            async with aiohttp.ClientSession() as session:
                async with aiofiles.open(video_path, 'rb') as video:
                    video_data = await video.read()
                    
                    form_data = aiohttp.FormData()
                    form_data.add_field('chat_id', chat_id)
                    form_data.add_field('video', video_data, filename='accident_clip.mp4')
                    if caption:
                        form_data.add_field('caption', caption)
                    
                    async with session.post(url, data=form_data) as response:
                        result = await response.json()
                        return result.get('ok', False)
                        
        except Exception as e:
            logger.error(f"Failed to send video: {e}")
            return False
    
    async def _send_location(
        self,
        chat_id: str,
        latitude: float,
        longitude: float
    ) -> bool:
        """Send location via Telegram API"""
        try:
            url = f"{self.base_url}/sendLocation"
            payload = {
                'chat_id': chat_id,
                'latitude': latitude,
                'longitude': longitude
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    return result.get('ok', False)
                    
        except Exception as e:
            logger.error(f"Failed to send location: {e}")
            return False
    
    def _check_cooldown(self, cooldown_key: str) -> bool:
        """Check if cooldown period has passed for a specific responder"""
        if cooldown_key not in self.last_alert_time:
            return True
        
        time_since_last = datetime.now() - self.last_alert_time[cooldown_key]
        return time_since_last > timedelta(minutes=self.cooldown_minutes)
    
    def _update_cooldown(self, cooldown_key: str):
        """Update last alert time for a specific responder"""
        self.last_alert_time[cooldown_key] = datetime.now()
