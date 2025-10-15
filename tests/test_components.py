"""
Test script for RoadSafeNet components
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from ai_model.detector import AccidentDetector
from utils.geolocation import GeolocationService
from utils.translation import TranslationService, SimpleTranslator
from telegram_bot.bot import TelegramAlertService
from utils.logger import setup_logger

logger = setup_logger('test')


def test_config():
    """Test configuration"""
    logger.info("Testing configuration...")
    
    errors = Config.validate()
    if errors:
        logger.warning(f"Configuration warnings: {errors}")
    else:
        logger.info("✓ Configuration OK")
    
    logger.info(f"  - App: {Config.APP_NAME} v{Config.APP_VERSION}")
    logger.info(f"  - Database: {Config.DATABASE_PATH}")
    logger.info(f"  - YOLO Model: {Config.YOLO_MODEL_PATH}")
    logger.info(f"  - Languages: {Config.SUPPORTED_LANGUAGES}")


def test_detector():
    """Test accident detector"""
    logger.info("\nTesting accident detector...")
    
    try:
        detector = AccidentDetector()
        logger.info(f"✓ Detector initialized")
        logger.info(f"  - Model: {detector.model_path}")
        logger.info(f"  - Confidence: {detector.confidence}")
        logger.info(f"  - Device: {'GPU' if detector.model.device.type == 'cuda' else 'CPU'}")
    except Exception as e:
        logger.error(f"✗ Detector initialization failed: {e}")


def test_geolocation():
    """Test geolocation service"""
    logger.info("\nTesting geolocation service...")
    
    try:
        geo = GeolocationService()
        
        # Test coordinates (Times Square, NY)
        result = geo.reverse_geocode(40.7580, -73.9855)
        
        if result:
            logger.info("✓ Geolocation service OK")
            logger.info(f"  - Location: {result['formatted_address']}")
            logger.info(f"  - City: {result['city']}")
        else:
            logger.warning("✗ Geolocation returned no result")
    
    except Exception as e:
        logger.error(f"✗ Geolocation test failed: {e}")


def test_translation():
    """Test translation service"""
    logger.info("\nTesting translation service...")
    
    try:
        # Try full translator
        translator = TranslationService()
        logger.info("✓ Full translation service loaded")
        
        # Test translation
        text = "Accident detected"
        translated = translator.translate(text, "en", "es")
        
        if translated:
            logger.info(f"  - Original: {text}")
            logger.info(f"  - Spanish: {translated}")
        
    except Exception as e:
        logger.warning(f"Full translator not available: {e}")
        logger.info("Testing simple translator...")
        
        translator = SimpleTranslator()
        
        accident_data = {
            "location": "Test Location",
            "time": "14:30",
            "severity": "high"
        }
        
        message = translator.format_message(accident_data, "en")
        logger.info("✓ Simple translator OK")
        logger.info(f"  - Message: {message[:50]}...")


async def test_telegram():
    """Test Telegram bot"""
    logger.info("\nTesting Telegram bot...")
    
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.warning("✗ Telegram bot token not configured")
        return
    
    try:
        bot = TelegramAlertService()
        
        if bot.bot:
            logger.info("✓ Telegram bot initialized")
            
            # Test message (uncomment to actually send)
            # success = await bot.send_test_message()
            # if success:
            #     logger.info("✓ Test message sent successfully")
        else:
            logger.warning("✗ Telegram bot not initialized")
    
    except Exception as e:
        logger.error(f"✗ Telegram test failed: {e}")


async def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("RoadSafeNet Component Tests")
    logger.info("="*60)
    
    test_config()
    test_detector()
    test_geolocation()
    test_translation()
    await test_telegram()
    
    logger.info("\n" + "="*60)
    logger.info("Tests completed!")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
