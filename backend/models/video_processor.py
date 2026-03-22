"""
Video processing and tracking
"""
import os
import cv2
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Handles video file processing and face tracking"""
    
    def __init__(self, config, face_processor):
        self.config = config
        self.face_processor = face_processor
        self.frame_skip = config['VIDEO_FRAME_SKIP']
        self.max_duration = config['MAX_VIDEO_DURATION']
        self.log_threshold = config['MIN_FRAMES_BETWEEN_LOGS']
        
    def process_video(self, video_path: str, temp_dir: str) -> List[Dict]:
        """
        Process video frame-by-frame (with skipping) and detect faces.
        Returns a list of all unique detections across the video.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Failed to open video: {video_path}")
                return []
            
            # Video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0: fps = 30 # Default if unknown
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Tracking state: person_id -> last_frame_recorded
            tracking_history = {} # person_id -> frame_num
            unknown_history = []  # List of (bbox, frame_num)
            
            all_detections = []
            frame_num = 0
            
            # Create sub-directory for video frames
            video_name = Path(video_path).stem
            video_temp_path = Path(temp_dir) / video_name
            os.makedirs(video_temp_path, exist_ok=True)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check duration limit
                if (frame_num / fps) > self.max_duration:
                    logger.info("Reached maximum video duration, stopping")
                    break
                
                # Process every Nth frame
                if frame_num % self.frame_skip == 0:
                    # Temporary save frame to process
                    frame_path = str(video_temp_path / f"tmp_frame_{frame_num}.jpg")
                    cv2.imwrite(frame_path, frame)
                    
                    # Detect faces in frame
                    detections = self.face_processor.detect_faces(frame_path)
                    
                    for det in detections:
                        bbox = det['bbox']
                        keypoints = det['keypoints']
                        
                        # Extract embedding and identify
                        embedding = self.face_processor.extract_face_embedding(frame_path, bbox)
                        if embedding is None:
                            continue
                            
                        person_id, confidence = self.face_processor.identify_face(embedding)
                        timestamp = frame_num / fps
                        
                        # Occlusion estimation
                        occlusion = self.face_processor.estimate_occlusion(bbox, keypoints, frame.shape)
                        
                        # Tracking/Deduplication Logic
                        should_record = False
                        
                        if person_id:
                            # If person identified, check if they were recorded recently
                            last_recorded = tracking_history.get(person_id, -self.log_threshold - 1)
                            if (frame_num - last_recorded) >= self.log_threshold:
                                should_record = True
                                tracking_history[person_id] = frame_num
                        else:
                            # If unknown, check if a similar bbox was recorded recently 
                            # (Simple overlap check or just record every log_threshold)
                            # For now, record unknowns periodically to avoid clutter
                            should_record = True # For research, maybe record all unknowns per interval
                            person_id = "Unknown"
                        
                        if should_record:
                            # Save face crop
                            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                            face_crop = frame[y:y+h, x:x+w]
                            face_crop_path = str(video_temp_path / f"face_{frame_num}_{person_id if person_id != 'Unknown' else 'unk'}.jpg")
                            cv2.imwrite(face_crop_path, face_crop)
                            
                            all_detections.append({
                                'frame_number': frame_num,
                                'timestamp': timestamp,
                                'bbox': bbox,
                                'person_id': person_id if person_id != 'Unknown' else None,
                                'confidence': float(confidence),
                                'is_match': person_id != "Unknown" and person_id is not None,
                                'face_image_path': face_crop_path,
                                'occlusion_estimated': occlusion
                            })
                    
                    # Cleanup frame file to save space
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
                
                frame_num += 1
                
            cap.release()
            logger.info(f"Finished processing video. Total detections: {len(all_detections)}")
            return all_detections
            
        except Exception as e:
            logger.error(f"Video processing error: {str(e)}", exc_info=True)
            return []
