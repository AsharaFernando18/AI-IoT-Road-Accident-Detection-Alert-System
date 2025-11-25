"""
Real-time Video Streaming with YOLOv10 Accident Detection
Streams processed video with bounding boxes to the dashboard
"""

import cv2
import asyncio
from flask import Response
import sys
from pathlib import Path
import numpy as np
from threading import Thread, Lock
import time
import logging
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from ai_model.detector import AccidentDetector

logger = logging.getLogger(__name__)

class VideoStream:
    """Video streaming with real-time YOLOv10 detection"""
    
    def __init__(self):
        self.detector = AccidentDetector()
        self.output_frame = None
        self.lock = Lock()
        self.is_running = False
        self.current_detection = None
        self.latest_accident = None  # Store latest accident for popup
        self.accident_notifications = []  # Store notification history
        self.last_accident_time = 0  # Cooldown to prevent spam
        self.detection_enabled = True  # Control detection on/off
        self.cap = None  # Video capture object for cleanup
        
    def start(self):
        """Start the video processing thread"""
        if not self.is_running:
            self.is_running = True
            thread = Thread(target=self.process_video, daemon=True)
            thread.start()
            return thread
    
    def process_video(self):
        """Process video frames with YOLOv10 detection - OPTIMIZED"""
        # Open video source
        video_source = Config.VIDEO_SOURCE
        if video_source.isdigit():
            self.cap = cv2.VideoCapture(int(video_source))
        else:
            self.cap = cv2.VideoCapture(video_source)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open video source {video_source}")
            return
        
        cap = self.cap  # Local reference for convenience
        
        # Get video properties for optimization
        target_fps = 15  # Reduced target FPS for smoother streaming
        frame_delay = 1.0 / target_fps
        
        frame_count = 0
        last_detection_result = None
        
        try:
            while self.is_running:
                ret, frame = cap.read()
                
                if not ret:
                    # Loop video if it's a file
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0
                    continue
                
                frame_count += 1
                
                # Check if detection is enabled
                if self.detection_enabled:
                    # OPTIMIZED: Process every 3rd frame for better performance
                    # Skip intermediate frames completely
                    if frame_count % 3 == 0:
                        # Run detection
                        result = self.detector.process_frame(frame)
                        
                        # Draw detections on frame
                        annotated_frame = self.detector.draw_detections(frame, result)
                        
                        # Store current detection status
                        self.current_detection = {
                            'is_accident': result['is_accident'],
                            'confidence': result['confidence'],
                            'frame_number': frame_count,
                            'location': {
                                'lat': Config.MOCK_LOCATION_LAT,
                                'lon': Config.MOCK_LOCATION_LON,
                                'name': Config.MOCK_LOCATION_NAME
                            }
                        }
                        
                        # If accident detected, trigger emergency notifications
                        if result['is_accident'] and result['confidence'] > 0.65:
                            current_time = time.time()
                            
                            # Cooldown: Only trigger every 60 seconds
                            if current_time - self.last_accident_time > 60:
                                logger.warning(f"🚨 ACCIDENT DETECTED at frame {frame_count}! Confidence: {result['confidence']:.2%}")
                                
                                # Store accident data for popup
                                self.latest_accident = {
                                    'timestamp': current_time,
                                    'frame_number': frame_count,
                                    'confidence': result['confidence'],
                                    'location': {
                                        'lat': Config.MOCK_LOCATION_LAT,
                                        'lon': Config.MOCK_LOCATION_LON,
                                        'name': Config.MOCK_LOCATION_NAME
                                    }
                                }
                                logger.info(f"✅ latest_accident set: {self.latest_accident}")
                                
                                # Run notifications in background thread to avoid blocking
                                from threading import Thread
                                notification_thread = Thread(
                                    target=self._send_emergency_notifications,
                                    args=(Config.MOCK_LOCATION_LAT, Config.MOCK_LOCATION_LON, Config.MOCK_LOCATION_NAME, result['confidence']),
                                    daemon=True
                                )
                                notification_thread.start()
                                
                                self.last_accident_time = current_time
                        
                        # Cache result for reuse (avoid copying frame data)
                        last_detection_result = (result, annotated_frame)
                    else:
                        # Reuse last detection result for intermediate frames
                        if last_detection_result is not None:
                            result, annotated_frame = last_detection_result
                        else:
                            # First frames before any detection
                            annotated_frame = frame
                else:
                    # Detection disabled - show raw video
                    annotated_frame = frame
                
                # Update output frame (single copy to avoid overhead)
                with self.lock:
                    self.output_frame = annotated_frame
                
                # Control frame rate for smooth playback
                time.sleep(frame_delay)
        
        finally:
            cap.release()
    
    def _send_emergency_notifications(self, lat: float, lon: float, location_name: str, confidence: float):
        """Send Telegram notifications to nearest emergency responders and save to database"""
        from utils.telegram_notifications import notify_nearest_responders
        import sqlite3
        import os
        import cv2
        
        try:
            timestamp = datetime.now().isoformat()
            
            # Capture current frame as accident image
            accident_image_path = None
            try:
                with self.lock:
                    if self.output_frame is not None:
                        # Create accidents directory if it doesn't exist
                        accidents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'accidents')
                        os.makedirs(accidents_dir, exist_ok=True)
                        
                        # Save accident frame with timestamp
                        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                        accident_image_path = os.path.join(accidents_dir, f'accident_{timestamp_str}.jpg')
                        cv2.imwrite(accident_image_path, self.output_frame)
                        logger.info(f"📸 Accident image saved: {accident_image_path}")
            except Exception as img_error:
                logger.error(f"Error saving accident image: {img_error}")
            
            # Save accident to database first
            try:
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                severity = 'HIGH' if confidence > 0.8 else 'MEDIUM'
                
                cursor.execute('''
                    INSERT INTO Accident (
                        timestamp, location_name, city, country, severity, status,
                        location_lat, location_lon, confidence, notes, detected_objects,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    location_name,
                    'Kuala Lumpur',
                    'Malaysia',
                    severity,
                    'ACTIVE',
                    lat,
                    lon,
                    confidence,
                    f"Dashboard Detection - Confidence: {confidence:.2%}",
                    '[]',  # Empty JSON array for detected_objects (required field)
                    timestamp,  # created_at
                    timestamp   # updated_at
                ))
                
                accident_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                logger.info(f"💾 Accident saved to database (ID: {accident_id})")
                
            except Exception as db_error:
                logger.error(f"Error saving accident to database: {db_error}")
            
            # Prepare accident data for Telegram notification (include image path)
            accident_data = {
                'latitude': lat,
                'longitude': lon,
                'severity': 'high' if confidence > 0.8 else 'medium',
                'location': location_name,
                'city': 'Kuala Lumpur',
                'timestamp': timestamp,
                'description': f"Dashboard Detection - Confidence: {confidence:.2%}",
                'image_path': accident_image_path  # Add image path for hospitals/ambulances
            }
            
            # Send Telegram notifications to all 3 responder types
            logger.info(f"🚨 Sending Telegram notifications for accident at {location_name}")
            notification_results = notify_nearest_responders(accident_data, limit_per_type=3)
            
            # Process results and create notification history + save to Alert table
            total_sent = 0
            for responder_type, results in notification_results.items():
                for result in results:
                    if result['notified']:
                        notification = {
                            'id': len(self.accident_notifications) + 1,
                            'type': responder_type,
                            'service_name': result['username'],
                            'distance': round(result['distance_km'], 2),
                            'status': 'sent',
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'location': location_name,
                            'confidence': confidence
                        }
                        self.accident_notifications.append(notification)
                        logger.info(f"   ✅ {result['username']} ({responder_type}) - {result['distance_km']:.2f} km - TELEGRAM SENT")
                        total_sent += 1
                        
                        # Save alert to database for Recent Notifications section
                        try:
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            alert_message = f"🚨 Accident alert sent to {result['username']} ({responder_type}) - {result['distance_km']:.2f} km away"
                            cursor.execute('''
                                INSERT INTO Alert (
                                    accident_id, language, message, status, sent_at, recipient
                                ) VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                accident_id,
                                'en',
                                alert_message,
                                'sent',
                                timestamp,
                                result['username']
                            ))
                            conn.commit()
                            conn.close()
                        except Exception as alert_error:
                            logger.error(f"Error saving alert to database: {alert_error}")
                    else:
                        logger.warning(f"   ❌ {result['username']} ({responder_type}) - {result.get('error', 'Unknown error')}")
            
            logger.info(f"📤 Sent {total_sent} Telegram notifications for accident at {location_name}")
            
        except Exception as e:
            logger.error(f"Error sending Telegram notifications: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_frame(self):
        """Get the current processed frame"""
        with self.lock:
            if self.output_frame is None:
                return None
            return self.output_frame.copy()
    
    def generate_frames(self):
        """Generate frames for streaming - HIGHLY OPTIMIZED"""
        while True:
            frame = self.get_frame()
            
            if frame is None:
                time.sleep(0.05)  # Reduced sleep time
                continue
            
            # OPTIMIZED: Resize frame for faster transmission
            # Scale down to 854x480 (480p) for smooth web streaming
            height, width = frame.shape[:2]
            if width > 854:
                new_width = 854
                new_height = int(height * (new_width / width))
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # OPTIMIZED: Lower JPEG quality to 65 for much smaller file size
            # Balance between quality and performance
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
            
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Yield frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def stop(self):
        """Stop the video processing and release resources"""
        self.is_running = False
        
        # Release video capture if it exists
        if self.cap is not None:
            try:
                self.cap.release()
                print("📹 Video capture released")
            except Exception as e:
                print(f"⚠️ Error releasing video capture: {e}")
        
        # Clear output frame
        with self.lock:
            self.output_frame = None
        
        print("✅ Video detection stopped successfully")


# Global video stream instance
video_stream = VideoStream()


def get_video_stream():
    """Get the video stream instance"""
    return video_stream


def video_feed():
    """Video streaming route handler"""
    return Response(
        video_stream.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
