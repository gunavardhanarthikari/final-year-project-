"""
Configuration settings for TrueFace AI
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'trueface-ai-secret-key-2026'
    
    # Database
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR / "trueface.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = BASE_DIR / 'backend' / 'uploads'
    TEMP_FOLDER = BASE_DIR / 'backend' / 'temp'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
    
    # Face Database
    FACE_DB_FOLDER = BASE_DIR / 'face_database'
    FACE_IMAGES_FOLDER = FACE_DB_FOLDER / 'images'
    FACE_EMBEDDINGS_FOLDER = FACE_DB_FOLDER / 'embeddings'
    
    # Face Recognition Settings
    CONFIDENCE_THRESHOLD = 0.5  # Slightly lower to handle heavy occlusion
    OCCLUSION_THRESHOLD = 0.5   # Handle up to 50% occlusion
    
    # Face Detection Model
    DETECTION_BACKEND = 'retinaface' # RetinaFace is best for masks/helmets
    RECOGNITION_MODEL = 'Facenet512' # High-accuracy model
    
    # Video Processing
    VIDEO_FRAME_SKIP = 5  # Process every Nth frame
    MAX_VIDEO_DURATION = 300  # 5 minutes max
    
    # Face Tracking (avoid duplicate detections)
    FACE_TRACKING_THRESHOLD = 0.3  # Distance threshold for same person
    MIN_FRAMES_BETWEEN_LOGS = 30  # Minimum frames between logging same person
    
    # Performance
    USE_GPU = False  # Set to True if GPU available
    BATCH_SIZE = 8
    
    # API
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
    
    @staticmethod
    def init_app(app):
        """Initialize application directories"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.TEMP_FOLDER, exist_ok=True)
        os.makedirs(Config.FACE_DB_FOLDER, exist_ok=True)
        os.makedirs(Config.FACE_IMAGES_FOLDER, exist_ok=True)
        os.makedirs(Config.FACE_EMBEDDINGS_FOLDER, exist_ok=True)
        
        # Create .gitkeep files
        for folder in [Config.UPLOAD_FOLDER, Config.TEMP_FOLDER, 
                      Config.FACE_IMAGES_FOLDER, Config.FACE_EMBEDDINGS_FOLDER]:
            gitkeep = folder / '.gitkeep'
            if not gitkeep.exists():
                gitkeep.touch()


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
