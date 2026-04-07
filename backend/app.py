"""
TrueFace AI - Flask Application
Main API server for face detection and identification
"""
import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template, session
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from functools import wraps

from config import config, Config
from database import db, StoredFace, UploadedFile, Detection, ProcessingLog, User
from models import FaceProcessor, VideoProcessor
from utils import (
    allowed_file, save_uploaded_file, get_file_size,
    draw_bounding_boxes, validate_image, validate_video
)
from utils.notifier import NotificationManager
from utils.id_gen import get_next_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
           static_folder='../frontend',
           template_folder='../frontend')

# Load configuration
app.config.from_object(config['development'])
Config.init_app(app)

# Initialize extensions
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
db.init_app(app)

# Initialize AI processors
face_processor = None
video_processor = None
notifier = None


def init_processors():
    """Initialize AI processors"""
    global face_processor, video_processor, notifier
    
    if face_processor is None:
        face_processor = FaceProcessor(app.config)
        logger.info("Face processor initialized")
    
    if video_processor is None:
        video_processor = VideoProcessor(app.config, face_processor)
        logger.info("Video processor initialized")

    if notifier is None:
        notifier = NotificationManager(app.config)
        logger.info("Notification manager initialized")


# ============================================================================
# ROUTES - Frontend Pages
# ============================================================================


@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('../frontend/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('../frontend/js', filename)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/results')
def results():
    """Results page"""
    return render_template('results.html')


@app.route('/history')
def history():
    """Detection history page"""
    return render_template('history.html')


@app.route('/admin')
def admin():
    """Admin panel for face database management"""
    return render_template('admin.html')


# ============================================================================
# AUTHENTICATION HELPERS & ROUTES
# ============================================================================

def login_required(f):
    """Decorator to require login for specific routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user is deleted
        user = User.query.get(session['user_id'])
        if not user or user.is_deleted:
            session.clear()
            return jsonify({'error': 'Account is inactive or deleted'}), 403
            
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require Admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or user.is_deleted or user.role != 'ADMIN':
            return jsonify({'error': 'Admin privileges required'}), 403
            
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    """Decorator to require Manager (High-end) or Admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or user.is_deleted or user.role not in ['ADMIN', 'MANAGER']:
            return jsonify({'error': 'Manager or Admin privileges required'}), 403
            
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user via Email or Readable ID"""
    data = request.get_json()
    identifier = data.get('username') # Can be email or readable_id
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({'error': 'Identifier and password required'}), 400
    
    # Check by email OR readable_id
    user = User.query.filter(
        (User.email == identifier) | (User.readable_id == identifier)
    ).first()
    
    if user and user.check_password(password):
        if user.is_deleted:
            return jsonify({'error': 'Account is inactive'}), 403
            
        session['user_id'] = user.id
        session['username'] = user.readable_id
        session['role'] = user.role
        session.permanent = True
        
        logger.info(f"User login: {user.readable_id} ({user.role})")
        return jsonify({
            'success': True, 
            'user': user.to_dict()
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    """Clear user session"""
    session.clear()
    return jsonify({'success': True}), 200


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check if user is logged in"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'logged_in': True,
                'user': user.to_dict()
            }), 200
    return jsonify({'logged_in': False}), 200


# ============================================================================
# API ROUTES - Image Upload & Processing
# ============================================================================

@app.route('/api/upload/image', methods=['POST'])
def upload_image():
    """Upload and process image for face detection"""
    try:
        init_processors()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
            return jsonify({'error': 'Invalid file type. Allowed: ' + 
                          ', '.join(app.config['ALLOWED_IMAGE_EXTENSIONS'])}), 400
        
        # Save uploaded file
        success, filepath, original_filename = save_uploaded_file(
            file, app.config['UPLOAD_FOLDER'], prefix='img_'
        )
        
        if not success:
            return jsonify({'error': 'Failed to save file'}), 500
        
        # Validate image
        if not validate_image(filepath):
            os.remove(filepath)
            return jsonify({'error': 'Invalid or corrupted image file'}), 400
        
        # Record upload in database
        file_size = get_file_size(filepath)
        uploaded_file = UploadedFile(
            filename=original_filename,
            file_path=filepath,
            file_type='image',
            file_size=file_size,
            user_id=session.get('user_id') # New: Associate with user
        )
        db.session.add(uploaded_file)
        db.session.commit()
        
        # Process image
        start_time = datetime.now()
        logger.info(f"Processing image: {original_filename} ({file_size} bytes)")
        
        # Detect faces
        detections = face_processor.detect_faces(filepath)
        logger.info(f"Face detection complete: found {len(detections)} faces")
        
        detection_results = []
        
        for detection in detections:
            bbox = detection['bbox']
            keypoints = detection['keypoints']
            
            # Extract embedding
            embedding = face_processor.extract_face_embedding(filepath, bbox)
            
            if embedding is None:
                continue
            
            # Identify face
            person_id, confidence = face_processor.identify_face(embedding)
            
            # Get matched face from database
            matched_face = None
            if person_id:
                matched_face = StoredFace.query.filter_by(person_id=person_id).first()
            
            # Estimate occlusion
            import cv2
            img = cv2.imread(filepath)
            occlusion = face_processor.estimate_occlusion(bbox, keypoints, img.shape)
            
            # Save cropped face
            from utils.image_utils import draw_bounding_boxes
            face_crop_path = str(app.config['TEMP_FOLDER'] / f"face_{uploaded_file.id}_{len(detection_results)}.jpg")
            
            # Crop and save face
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            padding = int(max(w, h) * 0.1)
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(img.shape[1], x + w + padding)
            y2 = min(img.shape[0], y + h + padding)
            face_crop = img[y1:y2, x1:x2]
            cv2.imwrite(face_crop_path, face_crop)
            
            # Create detection record
            detection_record = Detection(
                file_id=uploaded_file.id,
                matched_face_id=matched_face.id if matched_face else None,
                bbox_x=bbox['x'],
                bbox_y=bbox['y'],
                bbox_width=bbox['width'],
                bbox_height=bbox['height'],
                confidence_score=confidence,
                is_match=person_id is not None,
                face_image_path=face_crop_path,
                occlusion_estimated=occlusion
            )
            db.session.add(detection_record)
            
            detection_results.append({
                'bbox': bbox,
                'person_id': person_id,
                'person_name': matched_face.person_name if matched_face else 'Unknown',
                'confidence': confidence,
                'is_match': person_id is not None,
                'occlusion': occlusion,
                'face_image_path': os.path.basename(face_crop_path)
            })
            
        # Post-process results for deduplication
        # For known faces, only keep the best match (highest confidence)
        unique_matches = {}
        unknown_faces = []
        
        for det in detection_results:
            pid = det['person_id']
            if pid:
                # If seen before, keep the one with higher confidence
                if pid not in unique_matches or det['confidence'] > unique_matches[pid]['confidence']:
                    unique_matches[pid] = det
            else:
                unknown_faces.append(det)
        
        final_results = list(unique_matches.values()) + unknown_faces
        total_faces_found = len(detection_results)
        
        # Update processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        uploaded_file.processed = True
        uploaded_file.processing_time = processing_time
        
        db.session.commit()
        
        # Trigger Dual Alerts for Matches
        for pid, det in unique_matches.items():
            if det['is_match']:
                # Find the matched face database record
                face = StoredFace.query.filter_by(person_id=pid).first()
                if face:
                    # Collect recipients: Admin + Uploader
                    alert_list = []
                    alert_list.extend(app.config.get('ALERT_RECIPIENTS', []))
                    
                    uploader = User.query.get(session.get('user_id'))
                    if uploader and uploader.email and uploader.email not in alert_list:
                        alert_list.append(uploader.email)
                    
                    # Find the detection to get the face image path
                    detection_record = Detection.query.filter_by(
                        file_id=uploaded_file.id, 
                        matched_face_id=face.id
                    ).first()
                    
                    if alert_list and detection_record:
                        notifier.send_match_alert(
                            det['person_name'], 
                            det['confidence'] * 100, 
                            detection_record.face_image_path,
                            recipients=alert_list
                        )

        # Create annotated image
        annotated_path = str(app.config['TEMP_FOLDER'] / f"annotated_{uploaded_file.id}.jpg")
        draw_bounding_boxes(filepath, detection_results, annotated_path)
        
        return jsonify({
            'success': True,
            'file_id': uploaded_file.id,
            'filename': original_filename,
            'detections': final_results,
            'total_faces': total_faces_found,
            'processing_time': processing_time,
            'annotated_image': f'/api/file/temp/annotated_{uploaded_file.id}.jpg'
        }), 200
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size: 100MB'}), 413
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# API ROUTES - Video Upload & Processing
# ============================================================================

@app.route('/api/upload/video', methods=['POST'])
def upload_video():
    """Upload and process video for face detection"""
    try:
        init_processors()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename, app.config['ALLOWED_VIDEO_EXTENSIONS']):
            return jsonify({'error': 'Invalid file type. Allowed: ' + 
                          ', '.join(app.config['ALLOWED_VIDEO_EXTENSIONS'])}), 400
        
        # Save uploaded file
        success, filepath, original_filename = save_uploaded_file(
            file, app.config['UPLOAD_FOLDER'], prefix='vid_'
        )
        
        if not success:
            return jsonify({'error': 'Failed to save file'}), 500
        
        # Validate video
        if not validate_video(filepath):
            os.remove(filepath)
            return jsonify({'error': 'Invalid or corrupted video file'}), 400
        
        # Record upload in database
        file_size = get_file_size(filepath)
        uploaded_file = UploadedFile(
            filename=original_filename,
            file_path=filepath,
            file_type='video',
            file_size=file_size,
            user_id=session.get('user_id') # New: Associate with user
        )
        db.session.add(uploaded_file)
        db.session.commit()
        
        # Process video
        start_time = datetime.now()
        
        detections = video_processor.process_video(
            filepath, 
            str(app.config['TEMP_FOLDER'])
        )
        
        # Save detections to database
        for det in detections:
            # Get matched face
            matched_face = None
            if det['person_id']:
                matched_face = StoredFace.query.filter_by(person_id=det['person_id']).first()
            
            detection_record = Detection(
                file_id=uploaded_file.id,
                matched_face_id=matched_face.id if matched_face else None,
                frame_number=det['frame_number'],
                timestamp=det['timestamp'],
                bbox_x=det['bbox']['x'],
                bbox_y=det['bbox']['y'],
                bbox_width=det['bbox']['width'],
                bbox_height=det['bbox']['height'],
                confidence_score=det['confidence'],
                is_match=det['is_match'],
                face_image_path=det['face_image_path'],
                occlusion_estimated=det['occlusion_estimated']
            )
            db.session.add(detection_record)
        
        # Update processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        uploaded_file.processed = True
        uploaded_file.processing_time = processing_time
        
        db.session.commit()
        
        # Prepare response with deduplication
        unique_matches = {}
        top_unknown = None
        video_name = Path(uploaded_file.file_path).stem
        
        for det in detections:
            matched_face = StoredFace.query.filter_by(person_id=det['person_id']).first() if det['person_id'] else None
            
            filename = os.path.basename(det['face_image_path'])
            relative_path = f"{video_name}/{filename}"
            
            result_item = {
                'frame_number': det['frame_number'],
                'timestamp': det['timestamp'],
                'person_id': det['person_id'],
                'person_name': matched_face.person_name if matched_face else 'Unknown',
                'confidence': det['confidence'],
                'is_match': det['is_match'],
                'face_image_path': relative_path,
                'occlusion': det['occlusion_estimated']
            }
            
            pid = det['person_id']
            if pid:
                # Deduplicate by person_id, keep highest confidence
                if pid not in unique_matches or result_item['confidence'] > unique_matches[pid]['confidence']:
                    unique_matches[pid] = result_item
            else:
                # For unknowns, keep the one with best face detection confidence (visibility)
                if not top_unknown or result_item['confidence'] > top_unknown['confidence']:
                    top_unknown = result_item
        
        detection_summary = list(unique_matches.values())
        if top_unknown:
            detection_summary.append(top_unknown)
            
        # Trigger Dual Alerts for Unique Matches
        for pid, match_data in unique_matches.items():
            # Find the original detection to get the absolute path
            original_det = next((d for d in detections if d['person_id'] == pid), None)
            if original_det and match_data['is_match']:
                # Collect recipients: Admin + Uploader
                alert_list = []
                alert_list.extend(app.config.get('ALERT_RECIPIENTS', []))
                
                uploader = User.query.get(session.get('user_id'))
                if uploader and uploader.email and uploader.email not in alert_list:
                    alert_list.append(uploader.email)
                
                if alert_list:
                    notifier.send_match_alert(
                        match_data['person_name'],
                        match_data['confidence'] * 100,
                        original_det['face_image_path'],
                        recipients=alert_list
                    )

        # Use first detection as representative image
        representative_image = None
        if detection_summary:
            representative_image = f"/api/file/temp/{detection_summary[0]['face_image_path']}"

        return jsonify({
            'success': True,
            'file_id': uploaded_file.id,
            'filename': original_filename,
            'is_video': True,
            'detections': detection_summary,
            'total_detections': len(detections), # Total raw detections
            'processing_time': processing_time,
            'annotated_image': representative_image
        }), 200
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size: 100MB'}), 413
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# API ROUTES - Face Database Management
# ============================================================================

@app.route('/api/face/add', methods=['POST'])
@login_required
def add_face():
    """Add new face to database"""
    try:
        init_processors()
        
        # Get form data
        person_name = request.form.get('person_name')
        
        if not person_name:
            return jsonify({'error': 'Person name is required'}), 400
        
        # Generate unique IDs
        readable_id = get_next_id(StoredFace, role='FACE')
        person_id = f"PID_{uuid.uuid4().hex[:8].upper()}"
        
        # Check if person already exists (unlikely with UUID but good practice)
        existing = StoredFace.query.filter_by(person_id=person_id).first()
        if existing:
            # Retry once
            person_id = f"PID_{uuid.uuid4().hex[:8].upper()}"
        
        # Get uploaded image
        if 'file' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save image
        success, filepath, original_filename = save_uploaded_file(
            file, app.config['FACE_IMAGES_FOLDER'], prefix=f'{person_id}_'
        )
        
        if not success:
            return jsonify({'error': 'Failed to save image'}), 500
        
        # Add face to processor database
        try:
            embedding_path = str(app.config['FACE_EMBEDDINGS_FOLDER'] / f'{person_id}.pkl')
            
            # This might fail if model download fails or face not detected
            result = face_processor.add_face_to_database(person_id, person_name, filepath)
            
            if not result:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': 'No face detected or quality too low. Please use a clear front-facing photo.'}), 400
                
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'AI processing failed: {str(e)}'}), 500
        
        # Add to database
        stored_face = StoredFace(
            readable_id=readable_id,
            person_id=person_id,
            person_name=person_name,
            image_path=filepath,
            embedding_path=embedding_path,
            created_by=session.get('user_id')
        )
        db.session.add(stored_face)
        db.session.commit()
        
        logger.info(f"Added face to database: {person_id} - {person_name}")
        
        return jsonify({
            'success': True,
            'person_id': person_id,
            'person_name': person_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error adding face: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/face/list', methods=['GET'])
@login_required
def list_faces():
    """Get list of all stored faces"""
    try:
        faces = StoredFace.query.all()
        
        return jsonify({
            'success': True,
            'faces': [face.to_dict() for face in faces],
            'total': len(faces)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing faces: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/face/<int:face_id>', methods=['DELETE'])
@login_required
def delete_face(face_id):
    """Delete face from database"""
    try:
        init_processors()
        
        face = StoredFace.query.get(face_id)
        
        if not face:
            return jsonify({'error': 'Face not found'}), 404
        
        # Remove from processor
        face_processor.remove_face_from_database(face.person_id)
        
        # Remove image file
        if os.path.exists(face.image_path):
            os.remove(face.image_path)
        
        # Remove from database
        db.session.delete(face)
        db.session.commit()
        
        logger.info(f"Deleted face: {face.person_id}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error deleting face: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# API ROUTES - Admin Dashboard & User Management
# ============================================================================

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def get_admin_dashboard():
    """Get system-wide statistics for the admin dashboard"""
    try:
        total_faces = StoredFace.query.count()
        total_uploads = UploadedFile.query.count()
        total_detections = Detection.query.count()
        total_matches = Detection.query.filter_by(is_match=True).count()
        
        # Recent activity (last 10 uploads)
        recent_uploads = UploadedFile.query.order_by(UploadedFile.upload_time.desc()).limit(10).all()
        
        # User counts by role
        user_stats = {
            'ADMIN': User.query.filter_by(role='ADMIN', is_deleted=False).count(),
            'MANAGER': User.query.filter_by(role='MANAGER', is_deleted=False).count(),
            'VIEWER': User.query.filter_by(role='VIEWER', is_deleted=False).count()
        }
        
        return jsonify({
            'success': True,
            'stats': {
                'total_stored_faces': total_faces,
                'total_uploads': total_uploads,
                'total_detections': total_detections,
                'total_matches': total_matches,
                'match_rate': round(total_matches / total_detections * 100, 2) if total_detections > 0 else 0,
                'user_counts': user_stats
            },
            'recent_activity': [u.to_dict() for u in recent_uploads]
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def list_users():
    """List all active users"""
    try:
        users = User.query.filter_by(is_deleted=False).all()
        return jsonify({
            'success': True,
            'users': [u.to_dict() for u in users]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/user/create', methods=['POST'])
@admin_required
def create_user():
    """Create a new user with auto-generated Readable ID"""
    try:
        data = request.get_json()
        email = data.get('email')
        full_name = data.get('full_name')
        password = data.get('password', 'User@123') # Default password if not provided
        role = data.get('role', 'VIEWER') # Default role
        
        if not email or not full_name:
            return jsonify({'error': 'Email and Full Name are required'}), 400
            
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
            
        # Generate Readable ID (AD001, MG001, VW001)
        readable_id = get_next_id(User, role=role)
        
        new_user = User(
            readable_id=readable_id,
            email=email,
            full_name=full_name,
            role=role
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"User created successfully with ID: {readable_id}",
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"User creation error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
@admin_required
def soft_delete_user(user_id):
    """Soft delete a user"""
    try:
        user = User.query.get(user_id)
        if not user or user.is_deleted:
            return jsonify({'error': 'User not found'}), 404
            
        if user.readable_id == session.get('username'):
            return jsonify({'error': 'Cannot delete your own account'}), 400
            
        user.is_deleted = True
        db.session.commit()
        
        logger.info(f"User soft-deleted: {user.readable_id}")
        return jsonify({'success': True, 'message': f"User {user.readable_id} deactivated"}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API ROUTES - Face Database Management (Enhanced)
# ============================================================================

@app.route('/api/face/add-from-upload', methods=['POST'])
@manager_required
def add_face_from_upload():
    """Add a detected face directly from an upload results page"""
    try:
        data = request.get_json()
        detection_id = data.get('detection_id')
        person_name = data.get('person_name')
        
        if not detection_id or not person_name:
            return jsonify({'error': 'Detection ID and Person Name are required'}), 400
            
        detection = Detection.query.get(detection_id)
        if not detection:
            return jsonify({'error': 'Detection record not found'}), 404
            
        # Get the cropped face image path
        face_img_path = detection.face_image_path
        if not face_img_path or not os.path.exists(face_img_path):
            # Try to recreate from original file if path is relative
            return jsonify({'error': 'Detected face image not found on server'}), 400

        # Generate IDs
        readable_id = get_next_id(StoredFace, role='FACE')
        person_id = f"PID_{uuid.uuid4().hex[:8].upper()}"
        
        # Save face image to permanent face_database
        face_filename = f"{readable_id}_{os.path.basename(face_img_path)}"
        permanent_path = app.config['FACE_IMAGES_FOLDER'] / face_filename
        
        import shutil
        shutil.copy(face_img_path, permanent_path)
        
        # Generate embedding
        # Use existing face_processor
        try:
            init_processors()
            result = face_processor.add_face_to_database(person_id, person_name, str(permanent_path))
            if not result:
                return jsonify({'error': 'Failed to process face embedding'}), 500
        except Exception as e:
            return jsonify({'error': f"AI processing error: {str(e)}"}), 500

        # Create StoredFace record
        embedding_path = str(app.config['FACE_EMBEDDINGS_FOLDER'] / f'{person_id}.pkl')
        new_face = StoredFace(
            readable_id=readable_id,
            person_id=person_id,
            person_name=person_name,
            image_path=str(permanent_path),
            embedding_path=embedding_path,
            created_by=session.get('user_id')
        )
        
        db.session.add(new_face)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Face added to database with ID: {readable_id}",
            'face': new_face.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding face from upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# API ROUTES - Detection History
# ============================================================================

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Get detection history"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        file_type = request.args.get('file_type', None)
        
        # Build query
        query = UploadedFile.query.filter_by(processed=True)
        
        if file_type:
            query = query.filter_by(file_type=file_type)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        files = query.order_by(UploadedFile.upload_time.desc()).limit(limit).offset(offset).all()
        
        results = []
        for file in files:
            file_data = file.to_dict()
            
            # Get detections for this file
            detections = Detection.query.filter_by(file_id=file.id).all()
            file_data['detections'] = [det.to_dict() for det in detections]
            file_data['total_detections'] = len(detections)
            
            results.append(file_data)
        
        return jsonify({
            'success': True,
            'history': results,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/history/<int:file_id>', methods=['GET'])
@login_required
def get_file_detections(file_id):
    """Get detections for specific file"""
    try:
        file = UploadedFile.query.get(file_id)
        
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        detections = Detection.query.filter_by(file_id=file_id).all()
        
        return jsonify({
            'success': True,
            'file': file.to_dict(),
            'detections': [det.to_dict() for det in detections],
            'total_detections': len(detections)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting file detections: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# API ROUTES - File Serving
# ============================================================================

@app.route('/api/file/temp/<path:filename>')
def serve_temp_file(filename):
    """Serve temporary files"""
    return send_from_directory(app.config['TEMP_FOLDER'], filename)


@app.route('/api/file/face/<path:filename>')
def serve_face_image(filename):
    """Serve face images"""
    return send_from_directory(app.config['FACE_IMAGES_FOLDER'], filename)


# ============================================================================
# API ROUTES - System Info
# ============================================================================

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get system statistics"""
    try:
        total_faces = StoredFace.query.count()
        total_uploads = UploadedFile.query.count()
        total_detections = Detection.query.count()
        total_matches = Detection.query.filter_by(is_match=True).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_stored_faces': total_faces,
                'total_uploads': total_uploads,
                'total_detections': total_detections,
                'total_matches': total_matches,
                'match_rate': total_matches / total_detections if total_detections > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    return jsonify({'error': 'File too large. Maximum size: 100MB'}), 413


# ============================================================================
# Database Initialization
# ============================================================================

def init_database():
    """Initialize database tables with default records"""
    with app.app_context():
        # db.drop_all() # Uncomment to reset DB for migration
        db.create_all()
        
        # Create default admin user if none exists
        admin = User.query.filter_by(readable_id='AD001').first()
        if not admin:
            # Check if there's any user with role 'ADMIN'
            existing_admin = User.query.filter_by(role='ADMIN').first()
            if not existing_admin:
                admin = User(
                    readable_id='AD001',
                    email='admin@trueface.ai',
                    full_name='System Administrator',
                    role='ADMIN'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info("Default admin user created: AD001 / admin123")
            
        logger.info("Database initialized successfully")


# ============================================================================
# Main Entry Point
# ============================================================================

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run application
    logger.info("Starting TrueFace AI server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
