"""
Quick test to verify local setup is working
Run this after installing dependencies
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required packages can be imported"""
    print("🧪 Testing imports...")
    try:
        import fastapi
        import uvicorn
        import cv2
        import numpy
        import yaml
        import requests
        from pydantic_settings import BaseSettings
        print("  ✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("  Run: pip install -r requirements.txt")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    try:
        from app.config import settings
        print(f"  ✅ Configuration loaded")
        print(f"     - Database: {settings.DATABASE_PATH}")
        print(f"     - Storage: {settings.LOCAL_STORAGE_PATH}")
        print(f"     - Camera ID: {settings.CAMERA_ID}")
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n🧪 Testing database...")
    try:
        from app.db import DB
        db = DB()
        print("  ✅ Database initialized successfully")
        print(f"     - Path: {db.db_path}")
        print(f"     - Exists: {db.db_path.exists()}")
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_storage():
    """Test storage setup"""
    print("\n🧪 Testing storage...")
    try:
        from app.storage import LocalStorageClient
        from app.config import settings
        storage = LocalStorageClient()
        print("  ✅ Storage initialized successfully")
        print(f"     - Path: {storage.storage_dir}")
        print(f"     - Exists: {storage.storage_dir.exists()}")
        return True
    except Exception as e:
        print(f"  ❌ Storage error: {e}")
        return False

def test_model():
    """Test YOLO model loading"""
    print("\n🧪 Testing model...")
    try:
        from app.detectors.yolo_detector import YOLOQualityDetector
        detector = YOLOQualityDetector()
        print(f"  ✅ Model loaded successfully")
        print(f"     - Name: {detector.model_name}")
        print(f"     - Version: {detector.model_version}")
        return True
    except FileNotFoundError as e:
        print(f"  ⚠️  Model not found: {e}")
        print("     Run RUN_INCREMENTAL_TRAINING.bat to train a model first")
        return True  # Not a critical error
    except Exception as e:
        print(f"  ❌ Model error: {e}")
        return False

def main():
    print("=" * 60)
    print("  ERP Food QA - Local Setup Test")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Database", test_database()))
    results.append(("Storage", test_storage()))
    results.append(("Model", test_model()))
    
    print("\n" + "=" * 60)
    print("  Test Results")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8} | {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to start the application.")
        print("\nRun: START_LOCAL.bat")
        print("Or:  python -m uvicorn app.main:app --reload")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
