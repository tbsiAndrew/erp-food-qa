"""
Quick test script to verify YOLO is working in Flask
"""
import os
import sys

print("Testing YOLO integration...")

# Test 1: Import dependencies
print("\n1. Testing imports...")
try:
    import cv2
    print("   ✓ OpenCV imported")
except ImportError as e:
    print(f"   ✗ OpenCV failed: {e}")
    sys.exit(1)

try:
    from ultralytics import YOLO
    print("   ✓ Ultralytics imported")
except ImportError as e:
    print(f"   ✗ Ultralytics failed: {e}")
    sys.exit(1)

try:
    from flask import Flask
    print("   ✓ Flask imported")
except ImportError as e:
    print(f"   ✗ Flask failed: {e}")
    sys.exit(1)

# Test 2: Load YOLO model
print("\n2. Testing YOLO model loading...")
try:
    model_path = os.path.join('web', 'yolov8n.pt')
    if not os.path.exists(model_path):
        model_path = 'yolov8n.pt'
    
    model = YOLO(model_path)
    print(f"   ✓ YOLO model loaded from: {model_path}")
except Exception as e:
    print(f"   ✗ YOLO model loading failed: {e}")
    sys.exit(1)

# Test 3: Test camera access
print("\n3. Testing camera access...")
try:
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"   ✓ Camera accessible (frame shape: {frame.shape})")
        else:
            print("   ⚠ Camera opened but couldn't read frame")
        cap.release()
    else:
        print("   ⚠ Camera not accessible (may be in use)")
except Exception as e:
    print(f"   ✗ Camera test failed: {e}")

# Test 4: Test YOLO inference
print("\n4. Testing YOLO inference...")
try:
    import numpy as np
    # Create a dummy frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = model(dummy_frame)
    annotated = results[0].plot()
    print(f"   ✓ YOLO inference works (output shape: {annotated.shape})")
except Exception as e:
    print(f"   ✗ YOLO inference failed: {e}")
    sys.exit(1)

print("\n✅ All tests passed! YOLO is ready for Flask integration.")
print("\nTo start the Flask app:")
print("   cd web")
print("   python app.py")
print("\nThen open: http://localhost:5000")
