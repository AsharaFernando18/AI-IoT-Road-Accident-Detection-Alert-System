"""
Simple accident detection script for CCTV video
Runs YOLOv10 detection without translation services for faster startup
"""

import asyncio
import cv2
import logging
from pathlib import Path
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent))

from ai_model.detector import AccidentDetector
from prisma import Prisma
from utils.telegram_notifications import notify_nearest_responders

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def detect_accidents_in_video(video_path: str):
    """
    Process video for accident detection
    """
    logger.info("="*60)
    logger.info("🚨 Starting Accident Detection System")
    logger.info("="*60)
    
    # Initialize detector
    logger.info("Loading YOLOv10 accident detection model...")
    detector = AccidentDetector()
    logger.info("✓ Model loaded successfully")
    
    # Initialize database
    db = Prisma()
    await db.connect()
    logger.info("✓ Database connected")
    
    # Open video
    logger.info(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logger.error(f"Failed to open video: {video_path}")
        return
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"Video FPS: {fps}, Total frames: {total_frames}")
    logger.info("="*60)
    
    frame_count = 0
    accidents_detected = 0
    process_every_n_frames = 5  # Process every 5th frame for speed
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.info("End of video reached")
                break
            
            frame_count += 1
            
            # Process every nth frame
            if frame_count % process_every_n_frames != 0:
                continue
            
            # Run detection
            result = detector.process_frame(frame)
            
            if result['is_accident']:
                accidents_detected += 1
                timestamp = frame_count / fps
                logger.warning(f"🚨 ACCIDENT DETECTED at frame {frame_count} ({timestamp:.2f}s)")
                logger.info(f"   Confidence: {result['confidence']:.2%}")
                logger.info(f"   Detections: {len(result['detections'])}")
                
                # Save detection to database
                try:
                    # Use KLCC coordinates (where demo users are located)
                    accident_lat = 3.1578  # KLCC area
                    accident_lon = 101.7123
                    
                    accident = await db.accident.create(
                        data={
                            'location': f'CCTV Video - Frame {frame_count}',
                            'latitude': accident_lat,
                            'longitude': accident_lon,
                            'city': 'Kuala Lumpur',
                            'severity': 'high' if result['confidence'] > 0.8 else 'medium',
                            'description': f'Accident detected in CCTV footage at {timestamp:.2f}s',
                            'status': 'pending',
                            'timestamp': datetime.now()
                        }
                    )
                    logger.info(f"   ✓ Accident #{accident.id} saved to database")
                    
                    # Send notifications to nearest responders
                    try:
                        accident_data = {
                            'latitude': accident_lat,
                            'longitude': accident_lon,
                            'severity': accident.severity,
                            'location': accident.location,
                            'city': accident.city,
                            'timestamp': accident.timestamp.isoformat(),
                            'description': accident.description
                        }
                        
                        notification_results = notify_nearest_responders(accident_data, limit_per_type=3)
                        
                        # Count successful notifications
                        total_sent = sum(
                            sum(1 for r in results if r['notified'])
                            for results in notification_results.values()
                        )
                        
                        logger.info(f"   🚨 Notifications sent to {total_sent} responders")
                        
                        for resp_type, results in notification_results.items():
                            for result in results:
                                if result['notified']:
                                    logger.info(f"      ✅ {result['username']} ({resp_type}) - {result['distance_km']:.2f} km")
                                else:
                                    logger.warning(f"      ❌ {result['username']} ({resp_type}) - {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        logger.error(f"   ✗ Failed to send notifications: {e}")
                        
                except Exception as e:
                    logger.error(f"   ✗ Failed to save accident: {e}")
            
            # Progress update every 100 frames
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                logger.info(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
    
    finally:
        cap.release()
        await db.disconnect()
        logger.info("="*60)
        logger.info(f"📊 Detection Summary:")
        logger.info(f"   Total frames processed: {frame_count // process_every_n_frames}")
        logger.info(f"   Accidents detected: {accidents_detected}")
        logger.info("="*60)


async def main():
    video_path = "frontend/static/CCTV.mp4"
    
    if not Path(video_path).exists():
        logger.error(f"Video file not found: {video_path}")
        return
    
    await detect_accidents_in_video(video_path)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Detection stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
