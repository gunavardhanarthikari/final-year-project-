"""
Database initialization script
Run this to create the database tables
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db, logger

def init_db():
    """Initialize database"""
    with app.app_context():
        # Create all tables
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Print table information
        from database.models import StoredFace, UploadedFile, Detection, ProcessingLog
        
        print("\n" + "="*50)
        print("Database initialized successfully!")
        print("="*50)
        print("\nTables created:")
        print("  - stored_faces")
        print("  - uploaded_files")
        print("  - detections")
        print("  - processing_logs")
        print("\nYou can now run the application with: python backend/app.py")
        print("="*50 + "\n")

if __name__ == '__main__':
    init_db()
