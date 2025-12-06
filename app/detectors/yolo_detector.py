"""
Real-time YOLO detector for quality inspection
Uses YOLOv8 for fast object detection with custom classes
"""
import cv2
import numpy as np
from ultralytics import YOLO
import os

class YOLOQualityDetector:
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.35):  # VERY LOW threshold due to poor label quality
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model weights
            conf_threshold: Confidence threshold for detections (0.01 needed for poorly trained models)
        """
        # Try to use the LATEST trained bread quality model
        import os

        # Check for models in order: bread_qa11 (latest) -> bread_qa3 -> bread_qa2 -> bread_qa
        for model_name in ['bread_qa', 'bread_qa2', 'bread_qa3', 'bread_q4']:
            trained_model_path = os.path.join('runs', 'detect', model_name, 'weights', 'best.pt')
            if os.path.exists(trained_model_path):
                model_path = trained_model_path
                print(f"✓ Using trained bread quality model: {model_name}")
                print(f"⚠️  WARNING: Model has poor label quality - using conf_threshold={conf_threshold}")
                break
        else:
            # Fall back to pre-trained COCO model for testing
            model_path = 'yolov8n.pt'
            print(f"⚠ Trained model not found, using default YOLOv8n (COCO) for testing")
            print(f"   This will detect common objects but not bread quality")
        
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        
        # Updated class names for bread quality (2 classes)
        self.class_names = {
            0: 'good',
            1: 'bad'
        }
        
        # Model metadata for API compatibility
        self.model_name = "yolo_bread_qa"
        self.model_version = "1.0.0"
        
        print(f"📊 Model initialized with confidence threshold: {conf_threshold}")
    
    def predict(self, bgr):
        """
        Predict method for API compatibility - calls detect()
        
        Args:
            bgr: OpenCV BGR image
            
        Returns:
            List of detections compatible with API detector format
        """
        detections = self.detect(bgr)
        
        # Convert to API format: [{cls, label, conf, box}]
        # Keep bbox and confidence keys for consistency with draw_detections
        api_detections = []
        for det in detections:
            api_detections.append({
                'cls': det['class_id'],
                'label': det['class'],
                'class': det['class'],  # Keep class for draw_detections
                'conf': det['confidence'],
                'confidence': det['confidence'],  # Keep confidence for draw_detections
                'box': det['bbox'],  # [x1, y1, x2, y2]
                'bbox': det['bbox']  # Keep bbox for draw_detections compatibility
            })
        
        return api_detections
    
    def detect(self, frame):
        """
        Detect objects in frame
        
        Args:
            frame: OpenCV BGR image
            
        Returns:
            List of detections with bounding boxes, labels, and confidences
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            print(f"🔍 YOLO detected {len(boxes)} boxes with conf_threshold={self.conf_threshold}")
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                # Get class name
                class_name = self.class_names.get(class_id, f'class_{class_id}')
                
                print(f"  ✓ Detection: {class_name} @ {confidence:.2f} bbox=[{int(x1)},{int(y1)},{int(x2)},{int(y2)}]")
                
                detections.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': confidence,
                    'class': class_name,
                    'class_id': class_id
                })
        
        if len(detections) == 0:
            print(f"⚠️  No detections found. Try lowering confidence threshold or check if model is trained properly.")
        
        return detections
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: OpenCV BGR image
            detections: List of detection dictionaries
            
        Returns:
            Annotated frame
        """
        print(f"🎨 draw_detections called with {len(detections)} detections")
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            class_name = det['class']
            
            print(f"  Drawing: {class_name} @ ({x1},{y1})-({x2},{y2}) conf={confidence:.2f}")
            
            # Color coding
            if class_name == 'good':
                color = (0, 255, 0)  # Green for good bread
            elif class_name == 'bad':
                color = (0, 0, 255)  # Red for bad bread
            else:
                color = (0, 165, 255)  # Orange for unknown
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            
            # Prepare label
            label = f'{class_name} {confidence:.2f}'
            
            # Get text size for background
            (text_width, text_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            
            # Draw label background
            cv2.rectangle(
                frame,
                (x1, y1 - text_height - 10),
                (x1 + text_width + 10, y1),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                frame,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
        
        return frame
