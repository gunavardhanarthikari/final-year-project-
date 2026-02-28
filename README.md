# TrueFace AI

**AI-Powered Face Identification Under Partial Occlusion**

A professional academic-grade web application for robust face detection and identification, capable of recognizing faces even when 40-50% occluded by masks, scarves, glasses, or other obstructions.

## Features

- **Robust Face Detection**: Detects faces under various occlusion conditions
- **Face Identification**: Matches detected faces against pre-stored database
- **Image & Video Support**: Process both static images and video files
- **Detection History**: Track all detections with confidence scores
- **Professional UI**: Clean, academic-grade interface

## System Architecture

```
TrueFace AI/
├── backend/                 # Flask API server
│   ├── app.py              # Main application
│   ├── models/             # AI models & face processing
│   ├── database/           # Database models & operations
│   ├── utils/              # Utility functions
│   └── uploads/            # Temporary file storage
├── frontend/               # Web interface
│   ├── index.html          # Home page
│   ├── results.html        # Results display
│   ├── history.html        # Detection history
│   ├── admin.html          # Face database management
│   ├── css/                # Stylesheets
│   └── js/                 # JavaScript modules
├── face_database/          # Stored face embeddings
└── requirements.txt        # Python dependencies
```

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **AI/ML**: DeepFace, MTCNN, FaceNet, OpenCV
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: SQLite

## Installation

1. **Clone the repository**
   ```bash
   cd "f:\COLLEGE PROJECT 2"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python backend/init_db.py
   ```

5. **Run the application**
   ```bash
   python backend/app.py
   ```

6. **Access the application**
   Open browser: `http://localhost:5000`

## Usage

### Adding Faces to Database
1. Navigate to Admin Panel
2. Upload face images with labels (name/ID)
3. System generates and stores embeddings

### Face Detection & Identification
1. Upload image or video file
2. System processes and detects faces
3. View results with bounding boxes and confidence scores
4. Check detection history for all past detections

## API Endpoints

- `POST /api/upload/image` - Upload and process image
- `POST /api/upload/video` - Upload and process video
- `GET /api/history` - Retrieve detection history
- `POST /api/face/add` - Add face to database
- `GET /api/face/list` - List all stored faces
- `DELETE /api/face/<id>` - Remove face from database

## Performance

- Optimized for partial occlusion (40-50% coverage)
- Real-time processing for images
- Efficient frame-by-frame video processing
- Confidence thresholding for accurate matches

## Academic Use

This system is designed for academic demonstrations, research, and evaluation purposes. The architecture is modular and extensible for future enhancements.

## License

Academic Project - 2026
