"""
Quick Demo: Real-Time YOLO Quality Inspection
Shows webcam feed with object detection and bounding boxes

Usage:
    pip install ultralytics opencv-python
    python demo_yolo_realtime.py
    
Press 'q' to quit
"""

from ultralytics import YOLO
import cv2
import time

def main():
    print("🔍 Loading YOLO model...")
    # Use YOLOv8 nano (fastest, smallest)
    # Will auto-download on first run
    model = YOLO('yolov8n.pt')
    
    print("📹 Opening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open webcam")
        return
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # FPS calculation
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    print("✅ Starting real-time detection... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run YOLO detection
        results = model(frame, conf=0.25, verbose=False)
        
        # Draw bounding boxes and labels
        annotated_frame = results[0].plot()
        
        # Calculate FPS
        frame_count += 1
        if frame_count % 30 == 0:
            end_time = time.time()
            fps = 30 / (end_time - start_time)
            start_time = time.time()
        
        # Draw FPS on frame
        cv2.putText(
            annotated_frame,
            f'FPS: {fps:.1f}',
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        
        # Show frame
        cv2.imshow('QA Real-Time Inspection (Press Q to quit)', annotated_frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("👋 Demo completed!")

if __name__ == '__main__':
    main()
