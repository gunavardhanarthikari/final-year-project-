"""
Image processing utilities
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def draw_bounding_boxes(image_path: str, detections: List[Dict], 
                        output_path: str) -> bool:
    """
    Draw bounding boxes on image with labels
    Returns True if successful
    """
    try:
        img = cv2.imread(image_path)
        
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return False
        
        for detection in detections:
            bbox = detection.get('bbox', {})
            x = bbox.get('x', 0)
            y = bbox.get('y', 0)
            w = bbox.get('width', 0)
            h = bbox.get('height', 0)
            
            # Determine color based on match status
            is_match = detection.get('is_match', False)
            color = (0, 255, 0) if is_match else (0, 0, 255)  # Green for match, Red for no match
            
            # Draw rectangle
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
            
            # Prepare label
            person_id = detection.get('person_id', 'Unknown')
            confidence = detection.get('confidence', 0.0)
            label = f"{person_id}: {confidence:.2%}"
            
            # Draw label background
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (x, y - 30), (x + label_size[0], y), color, -1)
            
            # Draw label text
            cv2.putText(img, label, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw confidence bar
            bar_width = int(w * confidence)
            cv2.rectangle(img, (x, y + h + 5), (x + bar_width, y + h + 15), color, -1)
        
        # Save annotated image
        cv2.imwrite(output_path, img)
        logger.info(f"Saved annotated image: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error drawing bounding boxes: {str(e)}")
        return False


def create_face_grid(face_paths: List[str], output_path: str, 
                    grid_size: Tuple[int, int] = (5, 4)) -> bool:
    """
    Create grid of face images
    Returns True if successful
    """
    try:
        from PIL import Image
        
        rows, cols = grid_size
        face_size = 150
        
        # Create blank canvas
        grid_img = Image.new('RGB', (cols * face_size, rows * face_size), (255, 255, 255))
        
        for idx, face_path in enumerate(face_paths[:rows * cols]):
            if not Path(face_path).exists():
                continue
            
            row = idx // cols
            col = idx % cols
            
            # Load and resize face
            face_img = Image.open(face_path)
            face_img = face_img.resize((face_size, face_size), Image.Resampling.LANCZOS)
            
            # Paste into grid
            grid_img.paste(face_img, (col * face_size, row * face_size))
        
        grid_img.save(output_path)
        logger.info(f"Created face grid: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating face grid: {str(e)}")
        return False


def enhance_image_quality(image_path: str, output_path: str) -> bool:
    """
    Enhance image quality for better face detection
    Returns True if successful
    """
    try:
        img = cv2.imread(image_path)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Denoise
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        cv2.imwrite(output_path, enhanced)
        
        return True
        
    except Exception as e:
        logger.error(f"Error enhancing image: {str(e)}")
        return False
