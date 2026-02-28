# TrueFace AI - Quick Start Guide

## Prerequisites

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Windows 10/11, Linux, or macOS

## Installation

### Option 1: Automated Setup (Windows)

1. **Run setup script**:
   ```bash
   setup.bat
   ```
   This will:
   - Create virtual environment
   - Install all dependencies
   - Initialize database

2. **Run the application**:
   ```bash
   run.bat
   ```

3. **Open browser**:
   Navigate to `http://localhost:5000`

### Option 2: Manual Setup (All Platforms)

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment**:
   
   **Windows**:
   ```bash
   venv\Scripts\activate
   ```
   
   **Linux/Mac**:
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**:
   ```bash
   python backend/init_db.py
   ```

5. **Run application**:
   ```bash
   python backend/app.py
   ```

6. **Open browser**:
   Navigate to `http://localhost:5000`

## First-Time Setup

### Important Notes

1. **Model Download**: On first run, DeepFace will automatically download AI models (~200MB). This is a one-time process and may take 5-10 minutes depending on your internet connection.

2. **Face Database**: Start by adding faces to the database:
   - Navigate to **Database** page
   - Click "Add New Face"
   - Upload a clear face image
   - Enter Person ID and Name
   - Click "Add to Database"

3. **Test Detection**:
   - Go to **Home** page
   - Upload a test image or video
   - Wait for processing
   - View results

## Usage Guide

### Adding Faces to Database

1. Navigate to **Database** page
2. Fill in the form:
   - **Person ID**: Unique identifier (e.g., EMP001, STU123)
   - **Person Name**: Full name
   - **Face Image**: Clear, front-facing photo
3. Click "Add to Database"
4. Face embedding will be generated and stored

### Processing Images

1. Go to **Home** page
2. Click or drag image to upload zone
3. Click "Process Image"
4. Wait for processing (usually 2-5 seconds)
5. View results with:
   - Annotated image with bounding boxes
   - Detected faces with confidence scores
   - Match status for each face

### Processing Videos

1. Go to **Home** page
2. Click or drag video to upload zone
3. Click "Process Video"
4. Wait for processing (time depends on video length)
5. View results with:
   - Frame-by-frame detections
   - Timestamps for each detection
   - Matched persons across frames

### Viewing History

1. Navigate to **History** page
2. Use filters to view:
   - All files
   - Images only
   - Videos only
3. Expand any entry to see detailed detections
4. Review confidence scores and timestamps

## Configuration

### Adjusting Settings

Edit `backend/config.py` to customize:

```python
# Confidence threshold (0.0 - 1.0)
CONFIDENCE_THRESHOLD = 0.6

# Video frame skip (process every Nth frame)
VIDEO_FRAME_SKIP = 5

# Maximum video duration (seconds)
MAX_VIDEO_DURATION = 300

# Face detection model
DETECTION_BACKEND = 'mtcnn'  # Options: 'opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface'

# Face recognition model
RECOGNITION_MODEL = 'Facenet512'  # Options: 'VGG-Face', 'Facenet', 'Facenet512', 'OpenFace', 'DeepFace', 'ArcFace'
```

## Troubleshooting

### Common Issues

**Problem**: "No module named 'deepface'"
- **Solution**: Ensure virtual environment is activated and dependencies are installed

**Problem**: Face not detected in image
- **Solution**: 
  - Ensure face is clearly visible
  - Good lighting conditions
  - Face is not too small in image
  - Minimal motion blur

**Problem**: Low confidence scores
- **Solution**:
  - Add multiple reference images for same person
  - Use high-quality reference images
  - Ensure similar lighting conditions

**Problem**: Video processing is slow
- **Solution**:
  - Increase `VIDEO_FRAME_SKIP` in config
  - Process shorter video clips
  - Use lower resolution videos

**Problem**: "Out of memory" error
- **Solution**:
  - Close other applications
  - Process shorter videos
  - Reduce batch size in config

**Problem**: Models not downloading
- **Solution**:
  - Check internet connection
  - Manually download models from DeepFace GitHub
  - Check firewall settings

### Getting Help

1. Check `PROJECT_STRUCTURE.md` for technical details
2. Review error logs in console
3. Verify all dependencies are installed correctly

## Performance Tips

### For Better Accuracy

1. **Reference Images**:
   - Use clear, front-facing photos
   - Good lighting
   - Neutral expression
   - High resolution (at least 640x480)

2. **Test Images/Videos**:
   - Similar lighting to reference images
   - Clear, unblurred faces
   - Face size at least 100x100 pixels

### For Faster Processing

1. **Images**:
   - Resize large images before upload
   - Use JPEG format for smaller file size

2. **Videos**:
   - Use lower resolution (720p is sufficient)
   - Shorter clips (under 2 minutes)
   - Increase frame skip in config

## System Requirements

### Minimum Requirements
- **CPU**: Dual-core 2.0 GHz
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Python**: 3.8+

### Recommended Requirements
- **CPU**: Quad-core 2.5 GHz or better
- **RAM**: 8GB or more
- **Storage**: 5GB free space
- **GPU**: Optional (CUDA-compatible for faster processing)
- **Python**: 3.9 or 3.10

## Next Steps

1. **Add Test Faces**: Add 5-10 faces to the database
2. **Test Detection**: Upload test images and videos
3. **Review Results**: Check accuracy and confidence scores
4. **Adjust Settings**: Fine-tune configuration for your use case
5. **Production Deployment**: See deployment guide in README.md

## Support

For technical documentation, see:
- `README.md` - Project overview
- `PROJECT_STRUCTURE.md` - Architecture details
- `requirements.txt` - Dependencies list

---

**TrueFace AI** - Academic Research Project 2026
