"""
Video Clip Extraction Utility
Extracts 30-second clips from CCTV footage for police investigations
"""

import cv2
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from utils.logger import logger


class VideoClipExtractor:
    """Extract video clips from CCTV footage"""
    
    def __init__(self, output_dir: str = "uploads/clips"):
        """
        Initialize video clip extractor
        
        Args:
            output_dir: Directory to save extracted clips
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_clip(
        self,
        video_source: str,
        current_frame_number: int,
        clip_duration: int = 30,
        fps: Optional[float] = None
    ) -> Optional[str]:
        """
        Extract a video clip around the accident detection moment
        
        Args:
            video_source: Path to video file or camera stream
            current_frame_number: Frame number where accident was detected
            clip_duration: Duration of clip in seconds (default: 30)
            fps: Frames per second (if known, otherwise will be detected)
            
        Returns:
            Path to extracted clip file or None if extraction fails
        """
        try:
            # Open video
            cap = cv2.VideoCapture(video_source)
            
            if not cap.isOpened():
                logger.error(f"Failed to open video source: {video_source}")
                return None
            
            # Get video properties
            if fps is None:
                fps = cap.get(cv2.CAP_PROP_FPS)
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate frame range (15 seconds before, 15 seconds after)
            frames_before = int(fps * (clip_duration / 2))
            frames_after = int(fps * (clip_duration / 2))
            
            start_frame = max(0, current_frame_number - frames_before)
            end_frame = min(total_frames, current_frame_number + frames_after)
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"accident_clip_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                str(output_path),
                fourcc,
                fps,
                (width, height)
            )
            
            # Set starting position
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Extract frames
            frames_written = 0
            for frame_num in range(start_frame, end_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add timestamp overlay
                frame_with_overlay = self._add_timestamp_overlay(
                    frame, 
                    frame_num, 
                    fps,
                    current_frame_number
                )
                
                out.write(frame_with_overlay)
                frames_written += 1
            
            # Release resources
            cap.release()
            out.release()
            
            if frames_written > 0:
                logger.info(f"✅ Extracted {frames_written} frames to {output_path}")
                return str(output_path)
            else:
                logger.error("❌ No frames were written to clip")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting video clip: {e}")
            return None
    
    def _add_timestamp_overlay(
        self,
        frame,
        frame_number: int,
        fps: float,
        accident_frame: int
    ):
        """Add timestamp and marker overlay to frame"""
        
        # Calculate time in seconds
        time_seconds = frame_number / fps
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds % 1) * 1000)
        
        # Format timestamp
        timestamp_text = f"Time: {minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        frame_text = f"Frame: {frame_number}"
        
        # Add red marker if this is the accident frame
        if frame_number == accident_frame:
            timestamp_text += " ⚠️ ACCIDENT DETECTED"
            color = (0, 0, 255)  # Red
            thickness = 3
        else:
            color = (255, 255, 255)  # White
            thickness = 2
        
        # Add text overlays
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        
        # Black background for better readability
        cv2.rectangle(frame, (10, 10), (500, 80), (0, 0, 0), -1)
        
        # Add text
        cv2.putText(frame, timestamp_text, (20, 40), font, font_scale, color, thickness)
        cv2.putText(frame, frame_text, (20, 70), font, font_scale, (255, 255, 255), 2)
        
        return frame
    
    def extract_thumbnail(
        self,
        video_source: str,
        frame_number: int,
        output_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract a single frame as thumbnail image
        
        Args:
            video_source: Path to video file
            frame_number: Frame number to extract
            output_name: Optional custom output filename
            
        Returns:
            Path to extracted image or None if extraction fails
        """
        try:
            cap = cv2.VideoCapture(video_source)
            
            if not cap.isOpened():
                logger.error(f"Failed to open video source: {video_source}")
                return None
            
            # Set frame position
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error(f"Failed to read frame {frame_number}")
                return None
            
            # Generate output filename
            if output_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"accident_{timestamp}.jpg"
            
            output_path = self.output_dir.parent / "images" / output_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            cv2.imwrite(str(output_path), frame)
            
            logger.info(f"✅ Extracted thumbnail to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Error extracting thumbnail: {e}")
            return None
