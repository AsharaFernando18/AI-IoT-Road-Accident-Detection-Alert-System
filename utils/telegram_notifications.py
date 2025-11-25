"""
Telegram notification system for emergency responders
Sends accident alerts to nearest responders via their Telegram bots
"""

import requests
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.nearest_responders import find_all_nearest_responders


def send_telegram_message(bot_token: str, chat_id: str, message: str, parse_mode: str = 'HTML') -> bool:
    """
    Send a message via Telegram Bot API
    
    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID to send message to
        message: Message text to send
        parse_mode: Parse mode for message formatting (HTML or Markdown)
    
    Returns:
        True if message sent successfully, False otherwise
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
        return False


def send_telegram_photo(bot_token: str, chat_id: str, photo_path: str, caption: str = None) -> bool:
    """
    Send a photo via Telegram Bot API
    
    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID to send photo to
        photo_path: Path to the photo file or file-like object
        caption: Optional caption for the photo
    
    Returns:
        True if photo sent successfully, False otherwise
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {
                'chat_id': chat_id,
                'caption': caption or '',
                'parse_mode': 'HTML'
            }
            response = requests.post(url, files=files, data=data, timeout=15)
            response.raise_for_status()
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram photo: {e}")
        return False
    except FileNotFoundError as e:
        print(f"Photo file not found: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error sending photo: {e}")
        return False


def format_accident_message(
    accident_data: dict,
    responder_username: str,
    distance_km: float
) -> str:
    """
    Format accident information into a Telegram message
    
    Args:
        accident_data: Dictionary containing accident information
        responder_username: Username of the responder receiving the notification
        distance_km: Distance from responder to accident location
    
    Returns:
        Formatted HTML message string
    """
    # Extract accident details
    severity = accident_data.get('severity', 'UNKNOWN').upper()
    location = accident_data.get('location', 'Unknown Location')
    city = accident_data.get('city', 'Unknown City')
    latitude = accident_data.get('latitude', 0.0)
    longitude = accident_data.get('longitude', 0.0)
    timestamp = accident_data.get('timestamp', datetime.now().isoformat())
    description = accident_data.get('description', 'No description available')
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        formatted_time = timestamp
    
    # Severity emoji and color
    severity_emojis = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }
    severity_emoji = severity_emojis.get(severity, '⚠️')
    
    # Create map link
    map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    
    # Format message
    message = f"""
🚨 <b>EMERGENCY ACCIDENT ALERT</b> 🚨

{severity_emoji} <b>Severity:</b> {severity}
📍 <b>Location:</b> {location}
🏙️ <b>City:</b> {city}
📏 <b>Distance:</b> {distance_km} km from your location
⏰ <b>Time:</b> {formatted_time}

<b>Description:</b>
{description}

<b>Coordinates:</b>
Latitude: {latitude}
Longitude: {longitude}

🗺️ <a href="{map_link}">View on Map</a>

<b>Responder:</b> {responder_username.capitalize()}

⚡ <b>Action Required:</b> Please respond immediately to this emergency.
"""
    
    return message.strip()


def notify_nearest_responders(
    accident_data: dict,
    limit_per_type: int = 3
) -> dict:
    """
    Find and notify the nearest emergency responders about an accident
    
    Args:
        accident_data: Dictionary containing accident information
            Required keys: latitude, longitude
            Optional keys: severity, location, city, timestamp, description
        limit_per_type: Maximum number of responders to notify per type
    
    Returns:
        Dictionary with notification results
        Format: {
            'police': [
                {'username': 'police', 'distance_km': 5.2, 'notified': True, 'error': None},
                ...
            ],
            'ambulance': [...],
            'hospital': [...]
        }
    """
    # Validate required accident data
    if 'latitude' not in accident_data or 'longitude' not in accident_data:
        raise ValueError("accident_data must contain 'latitude' and 'longitude'")
    
    accident_lat = accident_data['latitude']
    accident_lon = accident_data['longitude']
    
    # Find nearest responders
    nearest_responders = find_all_nearest_responders(
        accident_lat,
        accident_lon,
        limit_per_type=limit_per_type
    )
    
    # Notification results
    notification_results = {
        'police': [],
        'ambulance': [],
        'hospital': []
    }
    
    # Send notifications to each responder type
    for responder_type, responders in nearest_responders.items():
        for responder in responders:
            result = {
                'username': responder['username'],
                'distance_km': responder['distance_km'],
                'notified': False,
                'error': None
            }
            
            try:
                # Format message for this responder
                message = format_accident_message(
                    accident_data,
                    responder['username'],
                    responder['distance_km']
                )
                
                # Get bot token and chat ID
                bot_token = responder['telegram_bot_token']
                chat_id = responder.get('telegram_chat_id')
                
                # Validate both token and chat ID are present
                if not chat_id:
                    result['error'] = "Chat ID not configured"
                    print(f"⚠️ {responder['username']} ({responder_type}) has no chat ID configured")
                    notification_results[responder_type].append(result)
                    continue
                
                # Send text notification first
                success = send_telegram_message(bot_token, chat_id, message)
                
                # Send accident image to hospitals and ambulances
                if success and responder_type in ['hospital', 'ambulance']:
                    accident_image_path = accident_data.get('image_path')
                    if accident_image_path and os.path.exists(accident_image_path):
                        photo_caption = f"🚨 <b>Accident Scene Image</b>\n📍 {accident_data.get('location', 'Unknown')}\n⏰ {accident_data.get('timestamp', 'N/A')}"
                        photo_success = send_telegram_photo(bot_token, chat_id, accident_image_path, photo_caption)
                        if photo_success:
                            print(f"📸 Accident image sent to {responder['username']} ({responder_type})")
                        else:
                            print(f"⚠️ Failed to send image to {responder['username']} ({responder_type})")
                
                result['notified'] = success
                
                if success:
                    print(f"✅ Notified {responder['username']} ({responder_type}) - {responder['distance_km']} km away")
                else:
                    result['error'] = "Failed to send message"
                    print(f"❌ Failed to notify {responder['username']} ({responder_type})")
                    
            except Exception as e:
                result['error'] = str(e)
                print(f"❌ Error notifying {responder['username']} ({responder_type}): {e}")
            
            notification_results[responder_type].append(result)
    
    return notification_results


def send_test_notification(responder_username: str) -> bool:
    """
    Send a test notification to a specific responder
    
    Args:
        responder_username: Username of the responder to test
    
    Returns:
        True if test notification sent successfully
    """
    test_accident = {
        'severity': 'MEDIUM',
        'location': 'Jalan Ampang, Kuala Lumpur',
        'city': 'Kuala Lumpur',
        'latitude': 3.1390,
        'longitude': 101.6869,
        'timestamp': datetime.now().isoformat(),
        'description': 'TEST NOTIFICATION - Two-vehicle collision at intersection. Minor injuries reported.'
    }
    
    # Find this specific responder
    from utils.nearest_responders import get_database_path
    import sqlite3
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, latitude, longitude, telegram_bot_token
                FROM User
                WHERE username = ?
                  AND is_active = 1
                  AND telegram_bot_token IS NOT NULL
                  AND telegram_bot_token != ''
            ''', (responder_username,))
            
            result = cursor.fetchone()
            
            if not result:
                print(f"❌ Responder '{responder_username}' not found or has no bot token configured")
                return False
            
            _, username, lat, lon, bot_token = result
            
            # Calculate distance (use 0 for test)
            distance = 0.0
            
            # Format and send message
            message = format_accident_message(test_accident, username, distance)
            chat_id = bot_token.split(':')[0]  # Extract bot ID
            
            success = send_telegram_message(bot_token, chat_id, message)
            
            if success:
                print(f"✅ Test notification sent to {username}")
            else:
                print(f"❌ Failed to send test notification to {username}")
            
            return success
            
    except Exception as e:
        print(f"❌ Error sending test notification: {e}")
        return False


if __name__ == '__main__':
    print("Telegram Notification System Test\n")
    print("=" * 50)
    
    # Test with sample accident data
    test_accident = {
        'severity': 'HIGH',
        'location': 'Jalan Tun Razak, Kuala Lumpur',
        'city': 'Kuala Lumpur',
        'latitude': 3.1578,
        'longitude': 101.7123,
        'timestamp': datetime.now().isoformat(),
        'description': 'Multi-vehicle collision on highway. Emergency response required. Multiple casualties reported.'
    }
    
    print("\n📍 Test Accident Location:")
    print(f"   Location: {test_accident['location']}")
    print(f"   Coordinates: {test_accident['latitude']}, {test_accident['longitude']}")
    print(f"   Severity: {test_accident['severity']}")
    print()
    
    print("🔍 Finding and notifying nearest responders...\n")
    
    try:
        results = notify_nearest_responders(test_accident, limit_per_type=3)
        
        print("\n" + "=" * 50)
        print("📊 NOTIFICATION RESULTS")
        print("=" * 50)
        
        for responder_type, notifications in results.items():
            print(f"\n{responder_type.upper()}:")
            if notifications:
                for notification in notifications:
                    status = "✅ SUCCESS" if notification['notified'] else "❌ FAILED"
                    print(f"  {status} - {notification['username']} ({notification['distance_km']} km)")
                    if notification['error']:
                        print(f"    Error: {notification['error']}")
            else:
                print("  No responders found with valid configuration")
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error during notification test: {e}")
