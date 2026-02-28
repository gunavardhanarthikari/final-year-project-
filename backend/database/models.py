"""
Database models for TrueFace AI
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class StoredFace(db.Model):
    """Model for stored face embeddings in the database"""
    __tablename__ = 'stored_faces'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(100), unique=True, nullable=False)
    person_name = db.Column(db.String(200), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    embedding_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    detections = db.relationship('Detection', backref='matched_face', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person_name,
            'image_path': self.image_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class UploadedFile(db.Model):
    """Model for uploaded files (images/videos)"""
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
    file_size = db.Column(db.Integer)  # in bytes
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processing_time = db.Column(db.Float)  # in seconds
    
    # Relationships
    detections = db.relationship('Detection', backref='source_file', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_time': self.upload_time.isoformat(),
            'processed': self.processed,
            'processing_time': self.processing_time
        }


class Detection(db.Model):
    """Model for face detection results"""
    __tablename__ = 'detections'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=False)
    matched_face_id = db.Column(db.Integer, db.ForeignKey('stored_faces.id'), nullable=True)
    
    # Detection details
    frame_number = db.Column(db.Integer, default=0)  # 0 for images, frame# for videos
    timestamp = db.Column(db.Float, default=0.0)  # Video timestamp in seconds
    
    # Bounding box coordinates
    bbox_x = db.Column(db.Integer, nullable=False)
    bbox_y = db.Column(db.Integer, nullable=False)
    bbox_width = db.Column(db.Integer, nullable=False)
    bbox_height = db.Column(db.Integer, nullable=False)
    
    # Match information
    confidence_score = db.Column(db.Float, default=0.0)
    is_match = db.Column(db.Boolean, default=False)
    
    # Cropped face image path
    face_image_path = db.Column(db.String(500))
    
    # Metadata
    detection_time = db.Column(db.DateTime, default=datetime.utcnow)
    occlusion_estimated = db.Column(db.Float, default=0.0)  # Estimated occlusion percentage
    
    def to_dict(self):
        """Convert model to dictionary"""
        result = {
            'id': self.id,
            'file_id': self.file_id,
            'frame_number': self.frame_number,
            'timestamp': self.timestamp,
            'bounding_box': {
                'x': self.bbox_x,
                'y': self.bbox_y,
                'width': self.bbox_width,
                'height': self.bbox_height
            },
            'confidence_score': round(self.confidence_score, 4),
            'is_match': self.is_match,
            'face_image_path': self.face_image_path,
            'detection_time': self.detection_time.isoformat(),
            'occlusion_estimated': round(self.occlusion_estimated, 2)
        }
        
        # Add matched person info if available
        if self.matched_face:
            result['matched_person'] = {
                'id': self.matched_face.person_id,
                'name': self.matched_face.person_name
            }
        else:
            result['matched_person'] = None
            
        return result


class ProcessingLog(db.Model):
    """Model for system processing logs"""
    __tablename__ = 'processing_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=True)
    log_type = db.Column(db.String(50), nullable=False)  # 'info', 'warning', 'error'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'log_type': self.log_type,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }
