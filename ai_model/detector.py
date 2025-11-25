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
    ENHANCED YOLOv10-based accident detection system
    Detects potential road accidents using advanced spatial analysis and temporal tracking
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence: float = None):
        """
        Initialize the enhanced accident detector
        
        Args:
            model_path: Path to YOLOv10 model file
            confidence: Confidence threshold for detection
        """
        self.model_path = model_path or str(Config.YOLO_MODEL_PATH)
        self.confidence = confidence or Config.YOLO_CONFIDENCE_THRESHOLD
        self.iou_threshold = Config.YOLO_IOU_THRESHOLD
        
        # Load YOLO model - Use larger model for better accuracy
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"✓ YOLOv10 model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            # Try YOLOv10m (medium model - better than 'n')
            logger.info("Downloading YOLOv10m model for better accuracy...")
            try:
                self.model = YOLO("yolov10m.pt")
                logger.info("✓ YOLOv10m model loaded (improved accuracy)")
            except Exception as fallback_error:
                # Fallback to yolov10n
                logger.warning(f"Could not load yolov10m: {fallback_error}")
                self.model = YOLO("yolov10n.pt")
                logger.info("✓ YOLOv10n model loaded (fallback)")
        
        # Accident-related classes from COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.person_class = 0
        self.bicycle_class = 1
        
        # Enhanced temporal tracking for multi-frame verification
        self.detection_history = []  # Store last N frames
        self.history_length = 5  # Analyze last 5 frames
        self.accident_frame_threshold = 3  # Must detect in 3/5 frames
        
        # Previous frame detections for motion analysis
        self.prev_detections = None
        
        # Enhanced accident detection parameters
        self.accident_indicators = {
            "vehicle_collision": 0.7,      # Direct collision/overlap (CRITICAL)
            "abnormal_orientation": 0.6,   # Flipped/tilted vehicles
            "multiple_vehicles_close": 0.4, # Cluster of vehicles
            "person_near_vehicle": 0.3,    # Pedestrian involvement
            "motorcycle_incident": 0.5,    # Motorcycle crashes
            "sudden_stop": 0.4            # Rapid deceleration
        }
    
    def detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """
        ENHANCED: Detect objects in a frame using YOLOv10 with better filtering
        
        Args:
            frame: Input video frame
            
        Returns:
            List of detected objects with bounding boxes and confidence
        """
        # Run detection with optimized parameters for speed
        results = self.model(
            frame, 
            conf=self.confidence,
            iou=self.iou_threshold,
            verbose=False,
            imgsz=416,  # Reduced from 640 to 416 for 2.4x faster inference
            half=False,  # Full precision
            device='cpu'  # Explicit CPU to avoid GPU overhead
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                
                # Calculate additional features
                width = x2 - x1
                height = y2 - y1
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                area = width * height
                aspect_ratio = width / height if height > 0 else 0
                
                detection = {
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "confidence": conf,
                    "class_id": cls,
                    "class_name": self.model.names[cls],
                    "center": [center_x, center_y],
                    "area": area,
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio
                }
                detections.append(detection)
        
        return detections
    
    def calculate_motion_score(self, current_detections: List[Dict]) -> float:
        """
        Calculate motion/change score between frames for sudden stop detection
        
        Returns:
            Motion score (higher = more movement/change)
        """
        if self.prev_detections is None or len(self.prev_detections) == 0:
            self.prev_detections = current_detections
            return 0.0
        
        # Track significant position changes
        motion_score = 0.0
        matched_vehicles = 0
        
        current_vehicles = [d for d in current_detections if d["class_id"] in self.vehicle_classes]
        prev_vehicles = [d for d in self.prev_detections if d["class_id"] in self.vehicle_classes]
        
        # Match vehicles between frames (simple nearest neighbor)
        for curr_v in current_vehicles:
            min_dist = float('inf')
            closest_prev = None
            
            for prev_v in prev_vehicles:
                dist = self.calculate_distance(curr_v["center"], prev_v["center"])
                if dist < min_dist:
                    min_dist = dist
                    closest_prev = prev_v
            
            # If vehicle moved significantly less than expected (sudden stop)
            if closest_prev and min_dist < 100:  # Same vehicle if within 100px
                # Check if size changed dramatically (collision/deformation)
                size_change = abs(curr_v["area"] - closest_prev["area"]) / closest_prev["area"]
                
                # Check if orientation changed (flipped/crashed)
                aspect_change = abs(curr_v["aspect_ratio"] - closest_prev["aspect_ratio"])
                
                if size_change > 0.3 or aspect_change > 0.5:
                    motion_score += 0.3
                    matched_vehicles += 1
        
        self.prev_detections = current_detections
        return min(motion_score, 1.0)
    
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
        ENHANCED v2: Advanced accident analysis with multi-indicator fusion
        Uses stricter thresholds and better logic to minimize false positives
        
        Args:
            detections: List of object detections
            
        Returns:
            Tuple of (is_accident, confidence, details)
        """
        # Minimum requirements for accident detection
        if len(detections) < 1:
            return False, 0.0, {}
        
        # Categorize detections
        vehicles = [d for d in detections if d["class_id"] in self.vehicle_classes 
                   and d["class_id"] != 3]  # Exclude motorcycles from vehicles
        motorcycles = [d for d in detections if d["class_id"] == 3]
        persons = [d for d in detections if d["class_id"] == self.person_class]
        
        # Need at least 1 vehicle OR motorcycle
        if len(vehicles) == 0 and len(motorcycles) == 0:
            return False, 0.0, {}
        
        accident_score = 0.0
        critical_indicators = 0  # Count of critical evidence
        
        details = {
            "indicators": [],
            "detected_objects": len(detections),
            "vehicles": len(vehicles),
            "motorcycles": len(motorcycles),
            "persons": len(persons),
            "critical_evidence": []
        }
        
        all_vehicles = vehicles + motorcycles
        
        # Calculate motion score for sudden changes
        motion_score = self.calculate_motion_score(detections)
        
        # ============= CRITICAL INDICATORS (High confidence) =============
        
        # INDICATOR 1: Direct Vehicle Collision/Overlap (HIGHEST PRIORITY)
        # IoU > 0.25 means significant overlap - vehicles occupying same space
        max_collision_score = 0.0
        for i, v1 in enumerate(all_vehicles):
            for v2 in all_vehicles[i+1:]:
                iou = self.calculate_iou(v1["bbox"], v2["bbox"])
                
                if iou > 0.25:  # STRICT: 25%+ overlap is abnormal
                    # This is CRITICAL evidence of collision
                    score = min(iou * 4.0, 1.0) * self.accident_indicators["vehicle_collision"]
                    max_collision_score = max(max_collision_score, score)
                    critical_indicators += 1
                    details["critical_evidence"].append({
                        "type": "COLLISION",
                        "iou": round(iou, 3),
                        "confidence": "CRITICAL"
                    })
        
        if max_collision_score > 0:
            accident_score += max_collision_score
            details["indicators"].append({
                "type": "vehicle_collision",
                "score": max_collision_score,
                "severity": "CRITICAL"
            })
        
        # INDICATOR 2: Abnormal Vehicle Orientation (Flipped/Crashed)
        # Vehicles normally are wider than tall - if reversed, likely crashed
        for vehicle in all_vehicles:
            aspect_ratio = vehicle.get("aspect_ratio", 1.0)
            
            # Normal cars/trucks: aspect > 1.3
            # Flipped/crashed: aspect < 0.85
            if aspect_ratio < 0.85 and vehicle["confidence"] > 0.7:
                score = self.accident_indicators["abnormal_orientation"]
                accident_score += score
                critical_indicators += 1
                details["critical_evidence"].append({
                    "type": "FLIPPED_VEHICLE",
                    "aspect_ratio": round(aspect_ratio, 2),
                    "confidence": "CRITICAL"
                })
                details["indicators"].append({
                    "type": "abnormal_orientation",
                    "score": score,
                    "aspect_ratio": aspect_ratio,
                    "severity": "CRITICAL"
                })
        
        # INDICATOR 3: Sudden Motion Change (Vehicle deformation/crash impact)
        if motion_score > 0.2:
            score = motion_score * self.accident_indicators["sudden_stop"]
            accident_score += score
            critical_indicators += 1
            details["indicators"].append({
                "type": "sudden_motion_change",
                "score": score,
                "motion_score": motion_score,
                "severity": "HIGH"
            })
        
        # ============= MODERATE INDICATORS (Supporting evidence) =============
        
        # INDICATOR 4: Multiple Vehicles Clustering (Pile-up potential)
        # 3+ vehicles abnormally close together
        if len(all_vehicles) >= 3:
            close_vehicle_pairs = 0
            for i, v1 in enumerate(all_vehicles):
                for v2 in all_vehicles[i+1:]:
                    distance = self.calculate_distance(v1["center"], v2["center"])
                    avg_size = (np.sqrt(v1["area"]) + np.sqrt(v2["area"])) / 2
                    
                    # STRICT: distance < 0.7 x average size
                    if distance < avg_size * 0.7:
                        close_vehicle_pairs += 1
            
            if close_vehicle_pairs >= 3:  # Need 3+ pairs for confidence
                score = min(close_vehicle_pairs / 4.0, 0.5) * self.accident_indicators["multiple_vehicles_close"]
                accident_score += score
                details["indicators"].append({
                    "type": "vehicle_clustering",
                    "score": score,
                    "close_pairs": close_vehicle_pairs,
                    "severity": "MODERATE"
                })
        
        # INDICATOR 5: Motorcycle Incident (High risk)
        # Motorcycles are vulnerable - if fallen or person nearby
        if len(motorcycles) > 0:
            for motorcycle in motorcycles:
                # Check if motorcycle appears fallen (aspect ratio)
                if motorcycle.get("aspect_ratio", 1.0) < 1.0:  # Wider than tall = fallen
                    score = self.accident_indicators["motorcycle_incident"]
                    accident_score += score
                    critical_indicators += 1
                    details["indicators"].append({
                        "type": "fallen_motorcycle",
                        "score": score,
                        "severity": "HIGH"
                    })
                    break
                
                # Check person very close to motorcycle
                for person in persons:
                    distance = self.calculate_distance(person["center"], motorcycle["center"])
                    avg_size = np.sqrt(motorcycle["area"])
                    if distance < avg_size * 1.0:  # Very close
                        score = self.accident_indicators["motorcycle_incident"] * 0.6
                        accident_score += score
                        details["indicators"].append({
                            "type": "motorcycle_person_incident",
                            "score": score,
                            "severity": "HIGH"
                        })
                        break
        
        # INDICATOR 6: Person on Roadway (Potential casualty)
        # Only significant if very close to vehicle
        high_risk_persons = 0
        for person in persons:
            for vehicle in all_vehicles:
                distance = self.calculate_distance(person["center"], vehicle["center"])
                avg_size = np.sqrt(vehicle["area"])
                
                # STRICT: person within vehicle boundary zone
                if distance < avg_size * 0.8:
                    high_risk_persons += 1
                    break
        
        if high_risk_persons > 0:
            score = min(high_risk_persons * 0.2, 0.3) * self.accident_indicators["person_near_vehicle"]
            accident_score += score
            details["indicators"].append({
                "type": "person_in_danger",
                "score": score,
                "count": high_risk_persons,
                "severity": "MODERATE"
            })
        
        # Normalize score
        accident_score = min(accident_score, 1.0)
        
        # ============= MULTI-FRAME TEMPORAL VERIFICATION =============
        # Add current detection to history
        self.detection_history.append(accident_score)
        if len(self.detection_history) > self.history_length:
            self.detection_history.pop(0)
        
        # Calculate temporal confidence
        # Accident must be detected consistently across multiple frames
        if len(self.detection_history) >= 3:
            high_score_frames = sum(1 for score in self.detection_history if score > 0.5)
            temporal_confidence = high_score_frames / len(self.detection_history)
        else:
            temporal_confidence = 0.0
        
        # ============= FINAL DECISION LOGIC =============
        # Use strict multi-criteria decision
        
        # PRIMARY: High single-frame score + critical evidence
        primary_detection = (
            accident_score > 0.70 and 
            critical_indicators >= 1
        )
        
        # SECONDARY: Moderate score but consistent across frames
        secondary_detection = (
            accident_score > 0.55 and
            temporal_confidence > 0.6 and
            critical_indicators >= 1
        )
        
        # TERTIARY: Multiple critical indicators even with lower score
        tertiary_detection = (
            critical_indicators >= 2 and
            accident_score > 0.50
        )
        
        is_accident = primary_detection or secondary_detection or tertiary_detection
        
        # Calculate final confidence
        if is_accident:
            final_confidence = min(
                accident_score * 0.6 +  # Single frame score
                temporal_confidence * 0.2 +  # Temporal consistency
                (critical_indicators * 0.1),  # Evidence strength
                1.0
            )
        else:
            final_confidence = accident_score
        
        details["accident_score"] = round(accident_score, 3)
        details["temporal_confidence"] = round(temporal_confidence, 3)
        details["critical_indicators"] = critical_indicators
        details["detection_method"] = (
            "PRIMARY" if primary_detection else
            "SECONDARY" if secondary_detection else
            "TERTIARY" if tertiary_detection else
            "NONE"
        )
        details["threshold_used"] = {
            "primary": 0.70,
            "secondary": 0.55,
            "tertiary": 0.50
        }
        details["decision"] = "⚠️ ACCIDENT DETECTED" if is_accident else "✓ Normal Traffic"
        
        return is_accident, final_confidence, details
    
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
