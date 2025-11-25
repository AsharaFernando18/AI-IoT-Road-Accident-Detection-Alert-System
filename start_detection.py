"""
Quick Start Accident Detection for Malaysia
Run this to start detecting accidents from webcam with Malaysia-focused alerts
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from main import RoadSafeNet
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Quick start for Malaysia accident detection"""
    print("\n" + "="*60)
    print("🚨 RoadSafeNet - Malaysia Accident Detection System")
    print("="*60)
    print("\n📹 Starting webcam detection...")
    print("🗺️  Location: Malaysia")
    print("📱 Alerts: Telegram enabled")
    print("🌐 Dashboard: http://localhost:8050")
    print("\nℹ️  Press 'q' in the video window to stop\n")
    print("="*60 + "\n")
    
    # Initialize system
    system = RoadSafeNet()
    
    try:
        await system.run()
    except KeyboardInterrupt:
        logger.info("\n\n✋ Detection stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ System terminated by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
