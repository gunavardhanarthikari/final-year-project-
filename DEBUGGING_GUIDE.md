# 🐛 TrueFace AI - Advanced Debugging Guide

This guide covers professional methods to debug and troubleshoot the TrueFace AI application.

## 1. Frontend Debugging (Browser)

The frontend is your first line of defense. Use Chrome/Edge Developer Tools (`F12`).

### 🔍 Inspecting API Calls (Network Tab)
If an upload fails or results don't appear:
1.  Open **Developer Tools** (`F12`) -> **Network** tab.
2.  Perform the action (e.g., upload an image).
3.  Look for the red request (e.g., `upload_image`).
4.  Click on it -> Check **Response** tab.
    *   *500 Error*: Backend crashed (check terminal).
    *   *400 Error*: Invalid input (wrong file type?).
    *   *413 Error*: File too large.

### 📜 JavaScript Logs (Console Tab)
1.  Open **Console** tab.
2.  Look for red errors.
    *   `Uncaught TypeError`: UI code failing (HTML ID mismatch?).
    *   `Failed to fetch`: Backend is down or unreachable.

---

## 2. Backend Debugging (Terminal)

The Python Flask server logs detailed information to the terminal where you ran `python backend/app.py`.

### 📝 Reading Stack Traces
When a **500 Internal Server Error** occurs:
1.  Go to your terminal.
2.  Scroll up to find the `Traceback (most recent call last):`.
3.  Look for the **last line** of the error description.
    *   `OutOfMemoryError`: Image is too big or GPU VRAM is full.
    *   `ValueError: Face could not be detected`: MTCNN failed to find a face.
    *   `ImportError`: Missing dependency (run `pip install ...`).

### ⚙️ Verbose Logging
To see more details, add print statements in `backend/models/face_processor.py`:

```python
# In face_processor.py
def detect_faces(self, image_path):
    print(f"[DEBUG] Processing image: {image_path}")
    # ... code ...
    print(f"[DEBUG] Found {len(faces)} faces")
```

---

## 3. Visual Debugging (Temp Files)

The system saves intermediate files that are great for debugging:

### 📂 Check `backend/temp/`
*   **Annotated Images**: See what the AI "saw" (bounding boxes).
    *   *If boxes are wrong*: Detection model issue (try changing `DETECTION_BACKEND` in `config.py`).
    *   *If image is black*: Image loading issue (OpenCV).

### 📂 Check `face_database/images/`
*   Verify uploaded face images are clear.
*   Corrupt or blurry images here will cause poor recognition accuracy.

---

## 4. AI Model Debugging

If accuracy is low or detection fails:

### 🔧 Configuration Tuning (`backend/config.py`)

1.  **Change Detection Model**:
    ```python
    # Try 'opencv' or 'retinaface' if 'mtcnn' is failing
    DETECTION_BACKEND = 'retinaface' 
    ```

2.  **Adjust Threshold**:
    ```python
    # Lower it if faces aren't matching
    CONFIDENCE_THRESHOLD = 0.5
    ```

3.  **Disable Enforce Detection** (in `face_processor.py`):
    *   DeepFace throws an error if no face is found. You can set `enforce_detection=False` to handle empty frames gracefully.

---

## 5. Database Debugging

### 🗄️ Inspect SQLite
1.  Download **DB Browser for SQLite** (free tool).
2.  Open `f:\COLLEGE PROJECT 2\trueface.db`.
3.  Check `stored_faces` table to ensure embeddings are being saved.
4.  Check `detections` table to see history logs.

---

## 6. Common Error Solutions

| Error | Method to Debug | Solution |
|-------|-----------------|----------|
| **Model Unreachable / 503** | Check Terminal | AI Model download failed or server overloaded. Restart app. |
| **"No Face Found"** | Check `temp/` | Ensure image isn't too dark/blurry. Try `retinaface`. |
| **Upload Stuck** | Check Network Tab | File might be too large (>16MB). Increase Flask limit. |
| **ImportError: DLL load failed** | Check Python Ver | Incompatible VC++ redistributable. Install VC++ 2015-2022. |

---

### 🚀 Pro Tip: Isolated Testing

If the full app fails, write a tiny script to test just the AI:

```python
# test_ai.py
from deepface import DeepFace
# Try to detect face in a local image
obj = DeepFace.analyze(img_path = "test.jpg", actions = ['age', 'gender'])
print(obj)
```
Run this to confirm dependencies work before debugging the web app.
