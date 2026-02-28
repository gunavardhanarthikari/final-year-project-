"""
Test script to verify TrueFace AI installation
Run this after setup to ensure everything is working correctly
"""
import sys
import os

def test_imports():
    """Test if all required packages are installed"""
    print("Testing package imports...")
    
    required_packages = [
        ('flask', 'Flask'),
        ('flask_cors', 'Flask-CORS'),
        ('flask_sqlalchemy', 'Flask-SQLAlchemy'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('cv2', 'OpenCV'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
        ('deepface', 'DeepFace'),
        ('mtcnn', 'MTCNN'),
    ]
    
    failed = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ✗ {name} - {str(e)}")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        print("Please run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All packages imported successfully!")
        return True


def test_directories():
    """Test if all required directories exist"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'backend',
        'backend/database',
        'backend/models',
        'backend/utils',
        'backend/uploads',
        'backend/temp',
        'frontend',
        'frontend/css',
        'frontend/js',
        'face_database',
        'face_database/images',
        'face_database/embeddings',
    ]
    
    missing = []
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✓ {directory}")
        else:
            print(f"  ✗ {directory} - Missing")
            missing.append(directory)
            # Create missing directory
            os.makedirs(directory, exist_ok=True)
            print(f"    → Created {directory}")
    
    if missing:
        print(f"\n⚠️  Created missing directories: {', '.join(missing)}")
    else:
        print("\n✅ All directories exist!")
    
    return True


def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        from backend.database import db, StoredFace, UploadedFile, Detection
        print("  ✓ Database models imported")
        
        if os.path.exists('trueface.db'):
            print("  ✓ Database file exists")
        else:
            print("  ⚠️  Database file not found")
            print("    Run: python backend/init_db.py")
        
        print("\n✅ Database test completed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Database test failed: {str(e)}")
        return False


def test_ai_models():
    """Test AI model initialization"""
    print("\nTesting AI models...")
    print("  ℹ️  Note: First run will download models (~200MB)")
    print("  This may take several minutes...")
    
    try:
        from backend.models import FaceProcessor
        from backend.config import config
        
        print("  ✓ FaceProcessor imported")
        
        # Note: We don't initialize here as it downloads models
        print("  ℹ️  Models will be downloaded on first use")
        print("\n✅ AI models test completed!")
        return True
        
    except Exception as e:
        print(f"  ✗ AI models test failed: {str(e)}")
        return False


def test_configuration():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        from backend.config import Config
        
        print(f"  ✓ Config loaded")
        print(f"  ✓ Detection backend: {Config.DETECTION_BACKEND}")
        print(f"  ✓ Recognition model: {Config.RECOGNITION_MODEL}")
        print(f"  ✓ Confidence threshold: {Config.CONFIDENCE_THRESHOLD}")
        
        print("\n✅ Configuration test completed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("TrueFace AI - Installation Test")
    print("="*60)
    print()
    
    tests = [
        test_imports,
        test_directories,
        test_configuration,
        test_database,
        test_ai_models,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            results.append(False)
        print()
    
    print("="*60)
    print("Test Summary")
    print("="*60)
    
    if all(results):
        print("✅ All tests passed!")
        print("\nYou can now run the application:")
        print("  python backend/app.py")
        print("\nThen open: http://localhost:5000")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        print("\nCommon fixes:")
        print("  1. Run: pip install -r requirements.txt")
        print("  2. Run: python backend/init_db.py")
        print("  3. Check Python version (3.8+ required)")
    
    print("="*60)


if __name__ == '__main__':
    main()
