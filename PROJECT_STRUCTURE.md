# TrueFace AI - Project Structure

## Directory Layout

```
TrueFace AI/
│
├── backend/                          # Backend API Server
│   ├── app.py                       # Main Flask application
│   ├── config.py                    # Configuration settings
│   ├── init_db.py                   # Database initialization script
│   │
│   ├── database/                    # Database models
│   │   ├── __init__.py
│   │   └── models.py                # SQLAlchemy models
│   │
│   ├── models/                      # AI/ML models
│   │   ├── __init__.py
│   │   ├── face_processor.py       # Face detection & recognition
│   │   └── video_processor.py      # Video processing & tracking
│   │
│   ├── utils/                       # Utility functions
│   │   ├── __init__.py
│   │   ├── file_utils.py           # File handling utilities
│   │   └── image_utils.py          # Image processing utilities
│   │
│   ├── uploads/                     # Temporary uploaded files
│   └── temp/                        # Temporary processing files
│
├── frontend/                        # Web Interface
│   ├── index.html                   # Home page
│   ├── results.html                 # Results display page
│   ├── history.html                 # Detection history page
│   ├── admin.html                   # Face database management
│   │
│   ├── css/
│   │   └── styles.css               # Main stylesheet
│   │
│   └── js/
│       ├── main.js                  # Home page logic
│       ├── results.js               # Results page logic
│       ├── history.js               # History page logic
│       └── admin.js                 # Admin page logic
│
├── face_database/                   # Face Database Storage
│   ├── images/                      # Original face images
│   └── embeddings/                  # Face embeddings (.pkl files)
│
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
├── README.md                        # Project documentation
└── PROJECT_STRUCTURE.md            # This file

```

## Component Descriptions

### Backend Components

#### `app.py`
- Main Flask application entry point
- REST API endpoints for:
  - Image/video upload and processing
  - Face database management
  - Detection history retrieval
  - System statistics
- Error handling and CORS configuration

#### `config.py`
- Application configuration
- AI model settings (MTCNN, FaceNet512)
- Confidence thresholds
- File upload limits
- Database configuration

#### `database/models.py`
- **StoredFace**: Face database entries
- **UploadedFile**: Uploaded file records
- **Detection**: Face detection results
- **ProcessingLog**: System logs

#### `models/face_processor.py`
- Face detection using MTCNN
- Face embedding extraction using DeepFace
- Face identification and matching
- Occlusion estimation
- Database management

#### `models/video_processor.py`
- Video frame extraction
- Frame-by-frame face detection
- Face tracking across frames
- Duplicate detection prevention
- Annotated video generation

#### `utils/file_utils.py`
- File upload handling
- File validation
- Temporary file cleanup
- File size formatting

#### `utils/image_utils.py`
- Bounding box drawing
- Face grid creation
- Image enhancement
- Thumbnail generation

### Frontend Components

#### `index.html`
- Home page with upload zones
- System statistics display
- Feature showcase
- Drag-and-drop file upload

#### `results.html`
- Detection results display
- Annotated image viewer
- Face detection cards
- Confidence visualization

#### `history.html`
- Detection history listing
- File type filtering
- Expandable detection details
- Timeline view

#### `admin.html`
- Face database management
- Add new faces
- Delete existing faces
- Database statistics

#### JavaScript Modules
- **main.js**: Upload handling, API communication
- **results.js**: Results visualization
- **history.js**: History filtering and display
- **admin.js**: Database CRUD operations

### Face Database

#### `face_database/images/`
- Original face images for each person
- Named: `{person_id}_{unique_id}.{ext}`

#### `face_database/embeddings/`
- Serialized face embeddings (pickle format)
- Named: `{person_id}.pkl`
- Used for fast face matching

## Data Flow

### Image Processing Flow
```
1. User uploads image → Frontend
2. Frontend sends to /api/upload/image → Backend
3. Backend saves file → uploads/
4. Face detection (MTCNN) → Detect faces
5. Face embedding extraction (DeepFace) → Generate embeddings
6. Face identification → Match against database
7. Save detection records → Database
8. Create annotated image → temp/
9. Return results → Frontend
10. Display results → results.html
```

### Video Processing Flow
```
1. User uploads video → Frontend
2. Frontend sends to /api/upload/video → Backend
3. Backend saves file → uploads/
4. Extract frames (every Nth frame) → temp/
5. For each frame:
   - Detect faces (MTCNN)
   - Extract embeddings (DeepFace)
   - Identify faces
   - Track across frames (prevent duplicates)
6. Save detection records → Database
7. Return results → Frontend
8. Display results → results.html
```

### Face Database Management Flow
```
1. Admin uploads face image → admin.html
2. Frontend sends to /api/face/add → Backend
3. Backend:
   - Saves image → face_database/images/
   - Extracts embedding → DeepFace
   - Saves embedding → face_database/embeddings/
   - Creates database record → StoredFace
4. Face processor reloads database
5. Face available for matching
```

## API Endpoints

### Upload Endpoints
- `POST /api/upload/image` - Upload and process image
- `POST /api/upload/video` - Upload and process video

### Face Database Endpoints
- `POST /api/face/add` - Add new face to database
- `GET /api/face/list` - List all stored faces
- `DELETE /api/face/<id>` - Delete face from database

### History Endpoints
- `GET /api/history` - Get detection history (paginated)
- `GET /api/history/<file_id>` - Get detections for specific file

### System Endpoints
- `GET /api/stats` - Get system statistics

### File Serving Endpoints
- `GET /api/file/temp/<filename>` - Serve temporary files
- `GET /api/file/face/<filename>` - Serve face images

## Database Schema

### stored_faces
- id (Primary Key)
- person_id (Unique)
- person_name
- image_path
- embedding_path
- created_at
- updated_at

### uploaded_files
- id (Primary Key)
- filename
- file_path
- file_type (image/video)
- file_size
- upload_time
- processed
- processing_time

### detections
- id (Primary Key)
- file_id (Foreign Key → uploaded_files)
- matched_face_id (Foreign Key → stored_faces)
- frame_number
- timestamp
- bbox_x, bbox_y, bbox_width, bbox_height
- confidence_score
- is_match
- face_image_path
- detection_time
- occlusion_estimated

### processing_logs
- id (Primary Key)
- file_id (Foreign Key → uploaded_files)
- log_type
- message
- timestamp

## AI/ML Configuration

### Face Detection
- **Model**: MTCNN (Multi-task Cascaded Convolutional Networks)
- **Purpose**: Robust face detection with keypoint localization
- **Handles**: Partial occlusion, various angles, lighting conditions

### Face Recognition
- **Model**: FaceNet512
- **Purpose**: Generate 512-dimensional face embeddings
- **Comparison**: Cosine similarity
- **Threshold**: 0.6 (configurable)

### Occlusion Handling
- **Estimation**: Keypoint visibility analysis
- **Threshold**: Supports up to 50% occlusion
- **Strategy**: Robust feature extraction with context padding

### Video Processing
- **Frame Skip**: Process every 5th frame (configurable)
- **Tracking**: Distance-based face tracking
- **Deduplication**: Minimum 30 frames between same person logs

## Performance Considerations

### Optimization Strategies
1. **Frame Skipping**: Reduce video processing time
2. **Batch Processing**: Process multiple detections efficiently
3. **Embedding Caching**: Store embeddings for fast matching
4. **Lazy Loading**: Load AI models on first use
5. **Async Processing**: Background video processing

### Resource Usage
- **Memory**: ~2-4GB for AI models
- **CPU**: Optimized for CPU inference
- **GPU**: Optional GPU acceleration (set USE_GPU=True)
- **Storage**: Minimal (embeddings are compact)

## Security Considerations

### Data Protection
- Face embeddings stored securely
- No public access to face database
- File upload validation
- Size limits enforced
- Temporary file cleanup

### Access Control
- Admin panel for database management
- API authentication (can be added)
- CORS configuration
- Input validation

## Extensibility

### Future Enhancements
1. **Multi-face tracking**: Track multiple people across video
2. **Live camera feed**: Real-time face detection
3. **Advanced analytics**: Age, gender, emotion detection
4. **Export functionality**: Export detection reports
5. **Batch upload**: Process multiple files
6. **API authentication**: JWT-based auth
7. **User management**: Multi-user support
8. **Cloud storage**: S3/Azure blob storage integration

### Model Upgrades
- Switch to ArcFace for better accuracy
- Use RetinaFace for improved detection
- Implement ensemble models
- Add face quality assessment
- Implement liveness detection

## Development Workflow

### Setup
1. Create virtual environment
2. Install dependencies
3. Initialize database
4. Run application

### Testing
1. Add test faces to database
2. Upload test images/videos
3. Verify detection accuracy
4. Check history and logs

### Deployment
1. Set production configuration
2. Use production WSGI server (Gunicorn)
3. Configure reverse proxy (Nginx)
4. Set up SSL/TLS
5. Configure monitoring

## Troubleshooting

### Common Issues

**Issue**: Face not detected
- **Solution**: Ensure face is clearly visible, good lighting, minimal blur

**Issue**: Low confidence scores
- **Solution**: Add more reference images, improve image quality

**Issue**: Slow video processing
- **Solution**: Increase frame skip, reduce video resolution

**Issue**: Memory errors
- **Solution**: Process shorter videos, reduce batch size

**Issue**: Model download fails
- **Solution**: Check internet connection, DeepFace downloads models on first use

## License & Attribution

- **DeepFace**: https://github.com/serengil/deepface
- **MTCNN**: https://github.com/ipazc/mtcnn
- **Flask**: https://flask.palletsprojects.com/
- **OpenCV**: https://opencv.org/

---

**TrueFace AI** - Academic Research Project 2026
