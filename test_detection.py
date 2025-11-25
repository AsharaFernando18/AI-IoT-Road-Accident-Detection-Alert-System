"""
Accident Detection Test Script
Test the YOLOv10 accident detection system with various video sources
"""

import asyncio
import cv2
import sys
from pathlib import Path
import logging

sys.path.append(str(Path(__file__).parent))

from config import Config
from ai_model.detector import AccidentDetector
from main import RoadSafeNet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_webcam():
    """Test with webcam (real-time)"""
    logger.info("="*60)
    logger.info("Testing Accident Detection with Webcam")
    logger.info("="*60)
    
    system = RoadSafeNet()
    await system.initialize_database()
    
    try:
        logger.info("Press 'q' to quit")
        await system.process_video_stream("0")
    finally:
        await system.shutdown()


async def test_video_file(video_path: str):
    """Test with video file"""
    logger.info("="*60)
    logger.info(f"Testing Accident Detection with Video: {video_path}")
    logger.info("="*60)
    
    if not Path(video_path).exists():
        logger.error(f"Video file not found: {video_path}")
        return
    
    system = RoadSafeNet()
    await system.initialize_database()
    
    try:
        logger.info("Press 'q' to quit")
        await system.process_video_stream(video_path)
    finally:
        await system.shutdown()


async def test_detector_only():
    """Test just the detector without full system"""
    logger.info("="*60)
    logger.info("Testing YOLOv10 Detector Only (No Database)")
    logger.info("="*60)
    
    detector = AccidentDetector()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Failed to open webcam")
        return
    
    logger.info("Press 'q' to quit")
    frame_count = 0
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Process every 2nd frame for speed
            if frame_count % 2 != 0:
                continue
            
            # Detect
            result = detector.process_frame(frame)
            
            # Log if accident detected
            if result["is_accident"]:
                logger.warning(f"⚠️ ACCIDENT DETECTED! Confidence: {result['confidence']:.2%}")
                logger.info(f"Details: {result['details']}")
            
            # Draw and display
            annotated = detector.draw_detections(frame, result)
            cv2.imshow("YOLOv10 Accident Detection", annotated)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info(f"Processed {frame_count} frames")


async def test_with_sample_videos():
    """Download and test with sample accident videos from YouTube"""
    logger.info("="*60)
    logger.info("Testing with Sample Accident Videos")
    logger.info("="*60)
    
    try:
        import yt_dlp
        
        # Sample accident videos (for educational/testing purposes)
        sample_videos = [
            "https://www.youtube.com/watch?v=YOUR_VIDEO_ID",  # Replace with actual accident video
        ]
        
        logger.info("This feature requires video URLs to be configured")
        logger.info("Please add accident video URLs to test with")
        
    except ImportError:
        logger.error("yt-dlp not installed. Install with: pip install yt-dlp")


def display_menu():
    """Display test menu"""
    print("\n" + "="*60)
    print("🚨 RoadSafeNet Accident Detection Test Menu")
    print("="*60)
    print("\n[1] Test with Webcam (Full System)")
    print("[2] Test with Video File (Full System)")
    print("[3] Test Detector Only (No Database)")
    print("[4] Test Detection Threshold")
    print("[5] View System Configuration")
    print("[6] Exit")
    print("\n" + "="*60)


async def test_threshold():
    """Test different confidence thresholds"""
    logger.info("="*60)
    logger.info("Testing Detection Thresholds")
    logger.info("="*60)
    
    thresholds = [0.3, 0.5, 0.7, 0.9]
    
    for threshold in thresholds:
        logger.info(f"\n--- Testing with threshold: {threshold} ---")
        detector = AccidentDetector(confidence=threshold)
        
        # Test with a few frames from webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Failed to open webcam")
            return
        
        for i in range(10):  # Test 10 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            result = detector.process_frame(frame)
            if result["is_accident"]:
                logger.info(f"Frame {i}: ACCIDENT - Confidence: {result['confidence']:.2%}")
            else:
                logger.info(f"Frame {i}: No accident")
        
        cap.release()


def view_config():
    """Display system configuration"""
    print("\n" + "="*60)
    print("🔧 System Configuration")
    print("="*60)
    print(f"\nYOLO Model: {Config.YOLO_MODEL_PATH}")
    print(f"Confidence Threshold: {Config.YOLO_CONFIDENCE_THRESHOLD}")
    print(f"IOU Threshold: {Config.YOLO_IOU_THRESHOLD}")
    print(f"Video Source: {Config.VIDEO_SOURCE}")
    print(f"Frame Skip: {Config.VIDEO_FRAME_SKIP}")
    print(f"Database: {Config.DATABASE_URL}")
    print(f"Telegram Bot: {'Configured' if Config.TELEGRAM_BOT_TOKEN else 'Not Configured'}")
    print(f"Supported Languages: {', '.join(Config.SUPPORTED_LANGUAGES)}")
    print("\nAccident Detection Classes:")
    for cls in Config.ACCIDENT_CLASSES:
        print(f"  - {cls}")
    print("="*60 + "\n")


async def main():
    """Main test menu"""
    while True:
        display_menu()
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                await test_webcam()
            
            elif choice == "2":
                video_path = input("\nEnter video file path: ").strip()
                await test_video_file(video_path)
            
            elif choice == "3":
                await test_detector_only()
            
            elif choice == "4":
                await test_threshold()
            
            elif choice == "5":
                view_config()
            
            elif choice == "6":
                logger.info("Exiting...")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-6.")
        
        except KeyboardInterrupt:
            logger.info("\n\nTest interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
