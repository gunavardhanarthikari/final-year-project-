"""
Utility functions for file handling and validation
"""
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder: Path, prefix: str = '') -> Tuple[bool, str, str]:
    """
    Save uploaded file with unique filename
    Returns (success, filepath, original_filename)
    """
    try:
        if not file or file.filename == '':
            return False, '', ''
        
        # Secure the filename
        original_filename = secure_filename(file.filename)
        
        # Generate unique filename
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_filename = f"{prefix}{uuid.uuid4().hex}.{file_ext}"
        
        # Save file
        filepath = upload_folder / unique_filename
        file.save(str(filepath))
        
        logger.info(f"Saved file: {original_filename} as {unique_filename}")
        return True, str(filepath), original_filename
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return False, '', ''


def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0


def cleanup_temp_files(folder: Path, max_age_hours: int = 24):
    """
    Clean up temporary files older than max_age_hours
    """
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filepath in folder.glob('*'):
            if filepath.is_file():
                file_age = current_time - filepath.stat().st_mtime
                if file_age > max_age_seconds:
                    filepath.unlink()
                    logger.info(f"Deleted old temp file: {filepath.name}")
                    
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")


def create_thumbnail(image_path: str, output_path: str, max_size: Tuple[int, int] = (200, 200)) -> bool:
    """
    Create thumbnail from image
    Returns True if successful
    """
    try:
        from PIL import Image
        
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(output_path)
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        return False


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def validate_image(filepath: str) -> bool:
    """Validate if file is a valid image"""
    try:
        from PIL import Image
        img = Image.open(filepath)
        img.verify()
        return True
    except:
        return False


def validate_video(filepath: str) -> bool:
    """Validate if file is a valid video"""
    try:
        import cv2
        cap = cv2.VideoCapture(filepath)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            return ret
        return False
    except:
        return False
