"""
Telegram Bot Service for sending accident alerts
"""

import asyncio
from telegram import Bot
from telegram.error import TelegramError
from typing import List, Optional, Dict
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from config import Config

logger = logging.getLogger(__name__)


class TelegramAlertService:
    """
    Service for sending accident alerts via Telegram Bot
    """
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Telegram bot service
        
        Args:
            bot_token: Telegram bot token (from BotFather)
        """
        self.bot_token = bot_token or Config.TELEGRAM_BOT_TOKEN
        
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            self.bot = None
        else:
            try:
                self.bot = Bot(token=self.bot_token)
                logger.info("✓ Telegram bot initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.bot = None
        
        self.default_chat_ids = Config.TELEGRAM_CHAT_IDS
        self.last_alert_time = {}  # Track last alert time per location
        self.cooldown = Config.ALERT_COOLDOWN_SECONDS
    
    async def send_message(self, chat_id: str, message: str, 
                          parse_mode: str = "HTML") -> bool:
        """
        Send message to a Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            message: Message text
            parse_mode: Message parse mode (HTML, Markdown)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info(f"✓ Message sent to chat {chat_id}")
            return True
        
        except TelegramError as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    async def send_photo(self, chat_id: str, photo_path: str, 
                        caption: Optional[str] = None) -> bool:
        """
        Send photo to a Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            photo_path: Path to photo file
            caption: Optional photo caption
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            with open(photo_path, 'rb') as photo_file:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="HTML"
                )
            logger.info(f"✓ Photo sent to chat {chat_id}")
            return True
        
        except TelegramError as e:
            logger.error(f"Failed to send photo to {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending photo: {e}")
            return False
    
    async def send_location(self, chat_id: str, latitude: float, 
                           longitude: float) -> bool:
        """
        Send location pin to a Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            await self.bot.send_location(
                chat_id=chat_id,
                latitude=latitude,
                longitude=longitude
            )
            logger.info(f"✓ Location sent to chat {chat_id}")
            return True
        
        except TelegramError as e:
            logger.error(f"Failed to send location to {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending location: {e}")
            return False
    
    def _check_cooldown(self, location_key: str) -> bool:
        """
        Check if enough time has passed since last alert for this location
        
        Args:
            location_key: Unique identifier for location
            
        Returns:
            True if alert can be sent, False if in cooldown period
        """
        if location_key not in self.last_alert_time:
            return True
        
        elapsed = (datetime.now() - self.last_alert_time[location_key]).total_seconds()
        return elapsed >= self.cooldown
    
    async def send_accident_alert(self, accident_data: Dict, 
                                  chat_ids: Optional[List[str]] = None,
                                  include_photo: bool = True,
                                  include_location: bool = True) -> Dict[str, bool]:
        """
        Send comprehensive accident alert to specified chats
        
        Args:
            accident_data: Dictionary with accident information
            chat_ids: List of chat IDs (uses default if not provided)
            include_photo: Include accident photo if available
            include_location: Include location pin
            
        Returns:
            Dictionary mapping chat IDs to send status
        """
        if not self.bot:
            logger.error("Cannot send alert: Telegram bot not initialized")
            return {}
        
        # Check cooldown
        location_key = f"{accident_data.get('location_lat', 0):.4f}_{accident_data.get('location_lon', 0):.4f}"
        
        if not self._check_cooldown(location_key):
            logger.info(f"Alert cooldown active for location {location_key}")
            return {}
        
        chat_ids = chat_ids or self.default_chat_ids
        
        if not chat_ids:
            logger.warning("No chat IDs configured for alerts")
            return {}
        
        # Format message
        message = self._format_alert_message(accident_data)
        
        results = {}
        
        for chat_id in chat_ids:
            try:
                # Send text message
                success = await self.send_message(chat_id, message)
                results[chat_id] = success
                
                if success:
                    # Send location if available
                    if include_location and accident_data.get('location_lat'):
                        await self.send_location(
                            chat_id,
                            accident_data['location_lat'],
                            accident_data['location_lon']
                        )
                    
                    # Send photo if available
                    if include_photo and accident_data.get('image_path'):
                        await self.send_photo(
                            chat_id,
                            accident_data['image_path'],
                            caption="Accident Scene"
                        )
                
                # Small delay between messages
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Error sending alert to {chat_id}: {e}")
                results[chat_id] = False
        
        # Update last alert time
        self.last_alert_time[location_key] = datetime.now()
        
        return results
    
    def _format_alert_message(self, accident_data: Dict) -> str:
        """
        Format accident data into alert message
        
        Args:
            accident_data: Dictionary with accident information
            
        Returns:
            Formatted HTML message
        """
        severity_emoji = {
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🚨"
        }
        
        severity = accident_data.get('severity', 'medium')
        emoji = severity_emoji.get(severity, "⚠️")
        
        message = f"""
{emoji} <b>ROAD ACCIDENT DETECTED</b> {emoji}

📍 <b>Location:</b> {accident_data.get('location_name', 'Unknown')}
📌 <b>Address:</b> {accident_data.get('address', 'Unknown')}
🏙️ <b>City:</b> {accident_data.get('city', 'Unknown')}

⏰ <b>Time:</b> {accident_data.get('timestamp', 'Unknown')}
⚠️ <b>Severity:</b> {severity.upper()}
🎯 <b>Confidence:</b> {accident_data.get('confidence', 0):.1%}

📊 <b>Detected Objects:</b> {accident_data.get('detected_objects_count', 0)}

🚨 <b>IMMEDIATE RESPONSE REQUIRED</b>
""".strip()
        
        if accident_data.get('weather_info'):
            message += f"\n🌤️ <b>Weather:</b> {accident_data['weather_info']}"
        
        return message
    
    async def send_test_message(self, chat_id: Optional[str] = None) -> bool:
        """
        Send test message to verify bot configuration
        
        Args:
            chat_id: Chat ID to send test message (uses first default if not provided)
            
        Returns:
            True if sent successfully
        """
        if not chat_id:
            if not self.default_chat_ids:
                logger.error("No chat IDs configured")
                return False
            chat_id = self.default_chat_ids[0]
        
        message = """
🤖 <b>RoadSafeNet Bot Test</b>

✅ Telegram bot is configured correctly!
✅ You will receive accident alerts on this chat.

<i>This is a test message.</i>
        """.strip()
        
        return await self.send_message(chat_id, message)
    
    async def broadcast_message(self, message: str, 
                               chat_ids: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Broadcast message to multiple chats
        
        Args:
            message: Message to broadcast
            chat_ids: List of chat IDs (uses default if not provided)
            
        Returns:
            Dictionary mapping chat IDs to send status
        """
        chat_ids = chat_ids or self.default_chat_ids
        results = {}
        
        for chat_id in chat_ids:
            success = await self.send_message(chat_id, message)
            results[chat_id] = success
            await asyncio.sleep(0.5)
        
        return results


# Synchronous wrapper for backward compatibility
class TelegramAlertServiceSync:
    """Synchronous wrapper for TelegramAlertService"""
    
    def __init__(self, bot_token: Optional[str] = None):
        self.service = TelegramAlertService(bot_token)
    
    def send_accident_alert(self, accident_data: Dict, 
                           chat_ids: Optional[List[str]] = None) -> Dict[str, bool]:
        """Send accident alert (synchronous)"""
        return asyncio.run(
            self.service.send_accident_alert(accident_data, chat_ids)
        )
    
    def send_test_message(self, chat_id: Optional[str] = None) -> bool:
        """Send test message (synchronous)"""
        return asyncio.run(self.service.send_test_message(chat_id))


if __name__ == "__main__":
    # Test Telegram bot
    async def main():
        service = TelegramAlertService()
        
        if not service.bot:
            print("❌ Telegram bot not configured. Set TELEGRAM_BOT_TOKEN in .env")
            return
        
        # Send test message
        print("Sending test message...")
        success = await service.send_test_message()
        
        if success:
            print("✅ Test message sent successfully!")
        else:
            print("❌ Failed to send test message")
        
        # Test accident alert
        print("\nSending test accident alert...")
        accident_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location_lat": 40.7128,
            "location_lon": -74.0060,
            "location_name": "Times Square",
            "address": "Manhattan, New York",
            "city": "New York",
            "severity": "high",
            "confidence": 0.92,
            "detected_objects_count": 5
        }
        
        results = await service.send_accident_alert(accident_data)
        print(f"Alert sent to {len(results)} chats")
        for chat_id, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} Chat {chat_id}: {status}")
    
    asyncio.run(main())
