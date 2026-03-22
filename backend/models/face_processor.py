"""
Face detection and recognition processor
"""
import os
import cv2
import pickle
import numpy as np
import logging
from pathlib import Path
from deepface import DeepFace
from mtcnn import MTCNN
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class FaceProcessor:
    """Handles all face-related AI operations"""
    
    def __init__(self, config):
        self.config = config
        self.detector = MTCNN()
        self.face_db_path = Path(config['FACE_EMBEDDINGS_FOLDER'])
        self.recognition_model = config['RECOGNITION_MODEL']
        self.detection_backend = config['DETECTION_BACKEND']
        self.threshold = config['CONFIDENCE_THRESHOLD']
        
        # Cache for loaded embeddings to speed up matching
        self.known_face_embeddings = {}
        self._load_database()
        
    def _load_database(self):
        """Load all stored face embeddings into memory"""
        self.known_face_embeddings = {}
        if not self.face_db_path.exists():
            os.makedirs(self.face_db_path, exist_ok=True)
            return

        for pkl_file in self.face_db_path.glob("*.pkl"):
            person_id = pkl_file.stem
            try:
                with open(pkl_file, 'rb') as f:
                    self.known_face_embeddings[person_id] = pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading embedding for {person_id}: {str(e)}")
        
        logger.info(f"Loaded {len(self.known_face_embeddings)} faces from database")

    def detect_faces(self, image_path: str) -> List[Dict]:
        """Detect all faces in an image using DeepFace's flexible backends"""
        try:
            # Try primary backend (defaulting to mtcnn or retinaface)
            results = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=self.detection_backend,
                enforce_detection=False,
                align=True
            )
            
            # If no faces found with primary, try a fallback (opencv is very fast/lenient)
            if not results or (len(results) == 1 and results[0]['confidence'] == 0):
                logger.info(f"Primary detector {self.detection_backend} found no faces, trying opencv fallback...")
                results = DeepFace.extract_faces(
                    img_path=image_path,
                    detector_backend='opencv',
                    enforce_detection=False,
                    align=True
                )

            detections = []
            for res in results:
                if res['confidence'] == 0 and len(results) > 1:
                    continue # Skip "no face" placeholders if other faces exist
                
                # Full images sometimes get a 0-confidence "whole image" result if detection fails
                if res['confidence'] == 0:
                    continue

                faceregion = res['facial_area']
                # DeepFace returns facial_area with x, y, w, h
                detections.append({
                    'bbox': {
                        'x': int(faceregion['x']), 
                        'y': int(faceregion['y']), 
                        'width': int(faceregion['w']), 
                        'height': int(faceregion['h'])
                    },
                    'keypoints': None, # extract_faces doesn't always return points in same format
                    'confidence': float(res['confidence'])
                })
            
            return detections
        except Exception as e:
            logger.error(f"Detection error: {str(e)}")
            return []

    def extract_face_embedding(self, image_path: str, bbox: Dict) -> Optional[np.ndarray]:
        """Extract face embedding using DeepFace (FaceNet512)"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # Crop face with some margin
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            
            # Margin padding (10%)
            margin_x = int(w * 0.1)
            margin_y = int(h * 0.1)
            
            x1 = max(0, x - margin_x)
            y1 = max(0, y - margin_y)
            x2 = min(img.shape[1], x + w + margin_x)
            y2 = min(img.shape[0], y + h + margin_y)
            
            face_img = img[y1:y2, x1:x2]
            if face_img.size == 0:
                return None
                
            # Generate embedding
            results = DeepFace.represent(
                img_path=face_img,
                model_name=self.recognition_model,
                enforce_detection=False,
                detector_backend='skip', # We already detected it
                align=True
            )
            
            if results and len(results) > 0:
                return np.array(results[0]['embedding'])
            
            return None
        except Exception as e:
            logger.error(f"Embedding extraction error: {str(e)}")
            return None

    def identify_face(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """Match embedding against database using cosine similarity"""
        if not self.known_face_embeddings:
            return None, 0.0
            
        best_match = None
        max_similarity = -1.0
        
        from scipy.spatial.distance import cosine
        
        for person_id, known_embedding in self.known_face_embeddings.items():
            # Calculate similarity: 1 - cosine_distance
            # scipy.spatial.distance.cosine returns distance [0, 2]
            distance = cosine(embedding, known_embedding)
            similarity = 1 - distance
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = person_id
        
        # Check against threshold
        if max_similarity >= self.threshold:
            return best_match, float(max_similarity)
        
        return None, float(max_similarity)

    def estimate_occlusion(self, bbox: Dict, keypoints: Dict, img_shape: Tuple) -> float:
        """
        Estimate face occlusion based on keypoint visibility and placement.
        """
        if not keypoints:
            return 1.0
            
        points = ['left_eye', 'right_eye', 'nose', 'mouth_left', 'mouth_right']
        occlusion_total = 0.0
        
        # Check if each keypoint is within the reported bbox
        # MTCNN can sometimes produce points outside if part of face is missing
        for pt in points:
            if pt in keypoints:
                kx, ky = keypoints[pt]
                # If keypoint is far from where it should be relative to bbox
                # we consider it occluded/unreliable
                rel_x = (kx - bbox['x']) / bbox['width']
                rel_y = (ky - bbox['y']) / bbox['height']
                
                # Expected ranges for normalized face (approx)
                # eyes around y=0.3, nose y=0.5, mouth y=0.7
                if not (0 <= rel_x <= 1 and 0 <= rel_y <= 1):
                    occlusion_total += 0.2
            else:
                occlusion_total += 0.2
                
        return min(occlusion_total, 1.0)

    def add_face_to_database(self, person_id: str, person_name: str, image_path: str) -> bool:
        """Process a reference image and add to database"""
        try:
            detections = self.detect_faces(image_path)
            if not detections:
                return False
            
            # Reference image should have one clear face
            best_face = detections[0]
            if len(detections) > 1:
                # Pick the largest/highest confidence face
                best_face = max(detections, key=lambda d: d['bbox']['width'] * d['bbox']['height'])
                
            embedding = self.extract_face_embedding(image_path, best_face['bbox'])
            if embedding is None:
                return False
                
            # Save embedding
            os.makedirs(self.face_db_path, exist_ok=True)
            pkl_path = self.face_db_path / f"{person_id}.pkl"
            with open(pkl_path, 'wb') as f:
                pickle.dump(embedding, f)
                
            # Update memory cache
            self.known_face_embeddings[person_id] = embedding
            
            return True
        except Exception as e:
            logger.error(f"Error adding face: {str(e)}")
            return False

    def remove_face_from_database(self, person_id: str):
        if person_id in self.known_face_embeddings:
            del self.known_face_embeddings[person_id]
            
        pkl_path = self.face_db_path / f"{person_id}.pkl"
        if pkl_path.exists():
            os.remove(pkl_path)
