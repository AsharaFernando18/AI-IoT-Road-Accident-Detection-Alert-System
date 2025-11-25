"""
Main Application Orchestrator for RoadSafeNet
Coordinates all components: detection, geolocation, translation, alerts
"""

import asyncio
import cv2
import logging
from pathlib import Path
from datetime import datetime
import json
import sys
from typing import Optional, Dict
import numpy as np

sys.path.append(str(Path(__file__).parent))

from config import Config
from ai_model.detector import AccidentDetector
from utils.geolocation import GeolocationService
from utils.translation import TranslationService, SimpleTranslator
from utils.telegram_notifications import notify_nearest_responders
from prisma import Prisma

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RoadSafeNet:
    """
    Main application orchestrator for the RoadSafeNet system
    """
    
    def __init__(self):
        """Initialize all system components"""
        logger.info("="*60)
        logger.info("🚨 Initializing RoadSafeNet System")
        logger.info("="*60)
        
        # Database
        self.db = Prisma()
        
        # AI Detection
        logger.info("Loading accident detection model...")
        self.detector = AccidentDetector()
        
        # Geolocation
        logger.info("Initializing geolocation service...")
        self.geo_service = GeolocationService()
        
        # Translation
        logger.info("Loading translation service...")
        try:
            self.translator = TranslationService()
            logger.info("✓ Full translation service loaded")
        except Exception as e:
            logger.warning(f"Failed to load full translator: {e}")
            logger.info("Using simple template translator")
            self.translator = SimpleTranslator()
        
        # State tracking
        self.last_detection = {}
        self.cooldown_locations = {}
        
        logger.info("✅ RoadSafeNet initialization complete!")
    
    async def initialize_database(self):
        """Connect to database"""
        await self.db.connect()
        logger.info("✓ Database connected")
    
    async def shutdown(self):
        """Cleanup and shutdown"""
        await self.db.disconnect()
        logger.info("✓ Database disconnected")
    
    async def process_detection(self, frame: np.ndarray, 
                               frame_number: int,
                               location_lat: Optional[float] = None,
                               location_lon: Optional[float] = None) -> Optional[Dict]:
        """
        Process a frame for accident detection and handle all downstream actions
        
        Args:
            frame: Video frame to process
            frame_number: Frame number
            location_lat: Optional latitude (if known)
            location_lon: Optional longitude (if known)
            
        Returns:
            Accident data dictionary if detected, None otherwise
        """
        # Detect accidents in frame
        result = self.detector.process_frame(frame)
        
        if not result["is_accident"]:
            return None
        
        logger.warning(f"⚠️  ACCIDENT DETECTED at frame {frame_number}!")
        logger.info(f"Confidence: {result['confidence']:.2%}")
        
        # Get location information
        location_data = None
        if location_lat and location_lon:
            location_data = self.geo_service.reverse_geocode(location_lat, location_lon)
        else:
            # Default location if not provided (can be configured)
            logger.warning("No location coordinates provided, using default")
            location_data = {
                "latitude": 0.0,
                "longitude": 0.0,
                "display_name": "Unknown Location",
                "city": "Unknown",
                "country": "Unknown",
                "formatted_address": "Unknown Location"
            }
        
        # Determine severity based on confidence and number of objects
        severity = self._determine_severity(result)
        
        # Save frame image
        image_path = self._save_frame(frame, frame_number)
        
        # Prepare accident data
        # Convert numpy types to Python types for JSON serialization
        detections_serializable = []
        for det in result["detections"]:
            det_copy = {
                "bbox": [float(x) for x in det["bbox"]],
                "confidence": float(det["confidence"]),
                "class_id": int(det["class_id"]),
                "class_name": det["class_name"],
                "center": [float(x) for x in det["center"]],
                "area": float(det["area"])
            }
            detections_serializable.append(det_copy)
        
        accident_data = {
            "timestamp": datetime.now(),
            "location_lat": float(location_data.get("latitude", 0.0)),
            "location_lon": float(location_data.get("longitude", 0.0)),
            "location_name": location_data.get("display_name", "Unknown"),
            "address": location_data.get("formatted_address", "Unknown"),
            "city": location_data.get("city", "Unknown"),
            "country": location_data.get("country", "Unknown"),
            "severity": severity,
            "confidence": float(result["confidence"]),
            "detected_objects": json.dumps(detections_serializable),
            "image_path": image_path,
            "video_frame": frame_number,
            "status": "pending"
        }
        
        # Store in database
        try:
            accident_record = await self.db.accident.create(data=accident_data)
            logger.info(f"✓ Accident record created with ID: {accident_record.id}")
            
            # Send alerts
            await self._send_alerts(accident_record)
            
            # Log system event
            await self.db.systemlog.create(
                data={
                    "level": "WARNING",
                    "source": "detection",
                    "message": f"Accident detected: {accident_record.id}",
                    "details": json.dumps({
                        "confidence": result["confidence"],
                        "severity": severity,
                        "location": accident_data["location_name"]
                    })
                }
            )
            
            return accident_data
        
        except Exception as e:
            logger.error(f"Failed to process detection: {e}")
            return None
    
    def _determine_severity(self, result: Dict) -> str:
        """Determine accident severity based on detection results"""
        confidence = result["confidence"]
        num_vehicles = len([d for d in result["detections"] 
                          if d["class_id"] in self.detector.vehicle_classes])
        num_persons = len([d for d in result["detections"] 
                         if d["class_id"] == self.detector.person_class])
        
        # Severity logic
        if confidence > 0.9 and (num_vehicles > 3 or num_persons > 0):
            return "critical"
        elif confidence > 0.75 and num_vehicles > 2:
            return "high"
        elif confidence > 0.6:
            return "medium"
        else:
            return "low"
    
    def _save_frame(self, frame: np.ndarray, frame_number: int) -> str:
        """Save frame as image file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"accident_{timestamp}_frame_{frame_number}.jpg"
        filepath = Config.UPLOADS_DIR / filename
        
        # Draw annotations with proper result structure
        annotated = self.detector.draw_detections(frame, {"detections": [], "is_accident": True, "confidence": 1.0})
        cv2.imwrite(str(filepath), annotated)
        
        return str(filepath)
    
    async def _send_alerts(self, accident_record):
        """Send notifications to nearest responders via Telegram"""
        try:
            # Prepare accident data for notification
            accident_data = {
                'latitude': float(accident_record.location_lat),
                'longitude': float(accident_record.location_lon),
                'severity': accident_record.severity,
                'location': accident_record.location_name,
                'city': accident_record.city,
                'timestamp': accident_record.timestamp.isoformat(),
                'description': f"Confidence: {accident_record.confidence:.2%}"
            }
            
            # Send notifications to nearest responders
            notification_results = notify_nearest_responders(accident_data, limit_per_type=3)
            
            # Count successful notifications
            total_sent = sum(
                sum(1 for r in results if r['notified'])
                for results in notification_results.values()
            )
            
            logger.info(f"🚨 Notifications sent to {total_sent} responders")
            
            # Log each notification
            for resp_type, results in notification_results.items():
                for result in results:
                    if result['notified']:
                        logger.info(f"   ✅ {result['username']} ({resp_type}) - {result['distance_km']:.2f} km")
                    else:
                        logger.warning(f"   ❌ {result['username']} ({resp_type}) - {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
    
    async def process_video_stream(self, video_source: str):
        """
        Process video stream for real-time accident detection
        
        Args:
            video_source: Video file path, camera index, or RTSP URL
        """
        logger.info(f"Starting video processing: {video_source}")
        
        # Open video
        if video_source.isdigit():
            cap = cv2.VideoCapture(int(video_source))
        else:
            cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video source: {video_source}")
            return
        
        frame_count = 0
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Skip frames based on configuration
                if frame_count % Config.VIDEO_FRAME_SKIP != 0:
                    continue
                
                # Process frame
                # In real deployment, get actual GPS coordinates from camera
                accident = await self.process_detection(
                    frame, 
                    frame_count,
                    location_lat=None,  # Would come from camera GPS
                    location_lon=None
                )
                
                # Display frame (optional for testing)
                display_frame = self.detector.draw_detections(
                    frame, 
                    {"detections": [], "is_accident": accident is not None}
                )
                cv2.imshow("RoadSafeNet", display_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info(f"Processed {frame_count} frames")
    
    async def run(self):
        """Main run loop"""
        await self.initialize_database()
        
        try:
            # Process video stream
            await self.process_video_stream(Config.VIDEO_SOURCE)
        
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    # Validate configuration
    errors = Config.validate()
    if errors:
        logger.warning("Configuration warnings:")
        for error in errors:
            logger.warning(f"  - {error}")
    
    # Create and run system
    system = RoadSafeNet()
    await system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
