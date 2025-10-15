"""
YOLOv10 Accident Detection Module
Real-time accident detection using Ultralytics YOLOv10
"""

import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import Config

logger = logging.getLogger(__name__)


class AccidentDetector:
    """
    YOLOv10-based accident detection system
    Detects potential road accidents based on object detection and spatial analysis
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence: float = None):
        """
        Initialize the accident detector
        
        Args:
            model_path: Path to YOLOv10 model file
            confidence: Confidence threshold for detection
        """
        self.model_path = model_path or str(Config.YOLO_MODEL_PATH)
        self.confidence = confidence or Config.YOLO_CONFIDENCE_THRESHOLD
        self.iou_threshold = Config.YOLO_IOU_THRESHOLD
        
        # Load YOLO model
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"✓ YOLOv10 model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            # Download default model if not found
            logger.info("Downloading YOLOv10n model...")
            self.model = YOLO("yolov10n.pt")
            logger.info("✓ Default YOLOv10n model loaded")
        
        # Accident-related classes from COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.person_class = 0
        self.bicycle_class = 1
        
        # Accident detection parameters
        self.accident_indicators = {
            "multiple_vehicles_close": 0.3,
            "unusual_vehicle_angle": 0.4,
            "person_near_vehicle": 0.3,
            "vehicle_overlap": 0.5
        }
    
    def detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in a frame using YOLOv10
        
        Args:
            frame: Input video frame
            
        Returns:
            List of detected objects with bounding boxes and confidence
        """
        results = self.model(
            frame, 
            conf=self.confidence, 
            iou=self.iou_threshold,
            verbose=False
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                
                detection = {
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "confidence": conf,
                    "class_id": cls,
                    "class_name": self.model.names[cls],
                    "center": [(x1 + x2) / 2, (y1 + y2) / 2],
                    "area": (x2 - x1) * (y2 - y1)
                }
                detections.append(detection)
        
        return detections
    
    def calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate Intersection over Union between two boxes"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Calculate intersection
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Calculate union
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def analyze_accident_probability(self, detections: List[Dict]) -> Tuple[bool, float, Dict]:
        """
        Analyze detections to determine accident probability
        
        Args:
            detections: List of object detections
            
        Returns:
            Tuple of (is_accident, confidence, details)
        """
        if len(detections) < 2:
            return False, 0.0, {}
        
        vehicles = [d for d in detections if d["class_id"] in self.vehicle_classes]
        persons = [d for d in detections if d["class_id"] == self.person_class]
        
        if len(vehicles) < 2 and len(persons) == 0:
            return False, 0.0, {}
        
        accident_score = 0.0
        details = {
            "indicators": [],
            "detected_objects": len(detections),
            "vehicles": len(vehicles),
            "persons": len(persons)
        }
        
        # Check for vehicle overlaps/collisions
        for i, v1 in enumerate(vehicles):
            for v2 in vehicles[i+1:]:
                iou = self.calculate_iou(v1["bbox"], v2["bbox"])
                distance = self.calculate_distance(v1["center"], v2["center"])
                
                # High IoU indicates collision
                if iou > 0.1:
                    score = min(iou * 2, 1.0) * self.accident_indicators["vehicle_overlap"]
                    accident_score += score
                    details["indicators"].append({
                        "type": "vehicle_overlap",
                        "score": score,
                        "iou": iou
                    })
                
                # Very close vehicles
                avg_size = (np.sqrt(v1["area"]) + np.sqrt(v2["area"])) / 2
                if distance < avg_size * 1.5:
                    score = self.accident_indicators["multiple_vehicles_close"]
                    accident_score += score
                    details["indicators"].append({
                        "type": "vehicles_close",
                        "score": score,
                        "distance": distance
                    })
        
        # Check for persons near vehicles (potential casualties)
        for person in persons:
            for vehicle in vehicles:
                distance = self.calculate_distance(person["center"], vehicle["center"])
                avg_size = np.sqrt(vehicle["area"])
                
                if distance < avg_size * 2:
                    score = self.accident_indicators["person_near_vehicle"]
                    accident_score += score
                    details["indicators"].append({
                        "type": "person_near_vehicle",
                        "score": score,
                        "distance": distance
                    })
        
        # Normalize score
        accident_score = min(accident_score, 1.0)
        is_accident = accident_score > 0.5
        
        details["accident_score"] = accident_score
        
        return is_accident, accident_score, details
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame for accident detection
        
        Args:
            frame: Input video frame
            
        Returns:
            Detection results dictionary
        """
        # Detect objects
        detections = self.detect_objects(frame)
        
        # Analyze for accidents
        is_accident, confidence, details = self.analyze_accident_probability(detections)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "is_accident": is_accident,
            "confidence": confidence,
            "detections": detections,
            "details": details,
            "frame_shape": frame.shape
        }
        
        return result
    
    def draw_detections(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """
        Draw detection results on frame
        
        Args:
            frame: Input frame
            result: Detection result from process_frame
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        # Draw detections
        for detection in result["detections"]:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = map(int, bbox)
            
            # Color based on class
            if detection["class_id"] in self.vehicle_classes:
                color = (0, 255, 255)  # Yellow for vehicles
            elif detection["class_id"] == self.person_class:
                color = (255, 0, 255)  # Magenta for persons
            else:
                color = (0, 255, 0)  # Green for others
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{detection['class_name']}: {detection['confidence']:.2f}"
            cv2.putText(
                annotated_frame, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )
        
        # Draw accident warning if detected
        if result["is_accident"]:
            warning_text = f"⚠ ACCIDENT DETECTED! Confidence: {result['confidence']:.2%}"
            cv2.putText(
                annotated_frame, warning_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3
            )
            
            # Add red border
            h, w = annotated_frame.shape[:2]
            cv2.rectangle(annotated_frame, (0, 0), (w-1, h-1), (0, 0, 255), 10)
        
        return annotated_frame
    
    def process_video(self, video_source: str, output_path: Optional[str] = None, 
                     frame_skip: int = 1, callback=None):
        """
        Process video stream for accident detection
        
        Args:
            video_source: Path to video file or camera index
            output_path: Optional path to save annotated video
            frame_skip: Process every Nth frame
            callback: Optional callback function for each detection
        """
        # Open video
        if video_source.isdigit():
            cap = cv2.VideoCapture(int(video_source))
        else:
            cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video source: {video_source}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup video writer if output path provided
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Skip frames
                if frame_count % frame_skip != 0:
                    continue
                
                # Process frame
                result = self.process_frame(frame)
                result["frame_number"] = frame_count
                
                # Draw annotations
                annotated_frame = self.draw_detections(frame, result)
                
                # Call callback if provided
                if callback:
                    callback(result, annotated_frame)
                
                # Write to output
                if writer:
                    writer.write(annotated_frame)
                
                # Display (for local testing)
                cv2.imshow("Accident Detection", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
        
        logger.info(f"Processed {frame_count} frames")


if __name__ == "__main__":
    # Test the detector
    detector = AccidentDetector()
    
    # Test with sample video or camera
    video_source = Config.VIDEO_SOURCE
    
    def detection_callback(result, frame):
        if result["is_accident"]:
            print(f"⚠ Accident detected at frame {result['frame_number']} "
                  f"with confidence {result['confidence']:.2%}")
    
    try:
        detector.process_video(
            video_source=video_source,
            frame_skip=Config.VIDEO_FRAME_SKIP,
            callback=detection_callback
        )
    except Exception as e:
        logger.error(f"Error during detection: {e}")
