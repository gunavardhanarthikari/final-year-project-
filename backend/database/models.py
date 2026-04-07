"""
Database models for TrueFace AI
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Model for application users with role-based access"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True) # Backend DB ID
    readable_id = db.Column(db.String(20), unique=True, nullable=False) # AD001, MG001, etc.
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'ADMIN', 'MANAGER', 'VIEWER'
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploads = db.relationship('UploadedFile', backref='uploader', lazy=True)
    stored_faces = db.relationship('StoredFace', backref='creator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'db_id': self.id,
            'readable_id': self.readable_id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat()
        }


class StoredFace(db.Model):
    """Model for stored face embeddings in the database"""
    __tablename__ = 'stored_faces'
    
    id = db.Column(db.Integer, primary_key=True)
    readable_id = db.Column(db.String(20), unique=True, nullable=False) # FC001, FC002, etc.
    person_id = db.Column(db.String(100), unique=True, nullable=False) # UUID or legacy ID
    person_name = db.Column(db.String(200), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    embedding_path = db.Column(db.String(500), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    detections = db.relationship('Detection', backref='matched_face', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'db_id': self.id,
            'readable_id': self.readable_id,
            'person_id': self.person_id,
            'person_name': self.person_name,
            'image_path': self.image_path,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class UploadedFile(db.Model):
    """Model for uploaded files (images/videos)"""
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Track uploader
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
            'user_id': self.user_id,
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
                'db_id': self.matched_face.id,
                'readable_id': self.matched_face.readable_id,
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
