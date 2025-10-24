"""
Quick test to see if the trained model can detect bread
"""
from ultralytics import YOLO
import cv2
import os

# Load the latest trained model
model_path = 'runs/detect/bread_qa3/weights/best.pt'
if not os.path.exists(model_path):
    model_path = 'runs/detect/bread_qa/weights/best.pt'

print(f"Loading model: {model_path}")
model = YOLO(model_path)

# Test with one of the training images
test_image = 'dataset/bread_qa/images/val/charles-chen-e83dQJ-BMog-unsplash.jpg'
if not os.path.exists(test_image):
    test_image = 'dataset/bread_qa/images/train/OIP.jpg'

if os.path.exists(test_image):
    print(f"\nTesting with image: {test_image}")
    
    # Run detection with VERY LOW confidence
    results = model(test_image, conf=0.01, verbose=True)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Detection Results:")
    print(f"{'='*60}")
    print(f"Number of detections: {len(results[0].boxes)}")
    
    if len(results[0].boxes) > 0:
        for i, box in enumerate(results[0].boxes):
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls]
            coords = box.xyxy[0].tolist()
            print(f"\nDetection {i+1}:")
            print(f"  Class: {class_name} (ID: {cls})")
            print(f"  Confidence: {conf:.4f}")
            print(f"  Bounding box: {coords}")
    else:
        print("\n⚠️ NO DETECTIONS FOUND!")
        print("This means the model is not detecting bread in the training images.")
        print("Possible issues:")
        print("  1. Training didn't converge properly (mAP50 was only 0.203)")
        print("  2. Images might not have been labeled properly")
        print("  3. Model needs more training data")
    
    # Save annotated image
    annotated = results[0].plot()
    output_path = 'test_detection_output.jpg'
    cv2.imwrite(output_path, annotated)
    print(f"\n✓ Saved annotated image to: {output_path}")
    print("Open this file to see if detection boxes appear.")
else:
    print(f"⚠️ Test image not found: {test_image}")
    print("Please check if training data exists in dataset/bread_qa/")
