"""
Auto-Label Images Using Pre-trained YOLO
Creates initial bounding boxes around detected objects,
which you can then refine manually if needed.
"""

from ultralytics import YOLO
from pathlib import Path
from minio import Minio
from minio.error import S3Error
import cv2

# MinIO configuration
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "qa-images"


def download_and_auto_label():
    """Download images from MinIO and auto-label them"""
    print("\n" + "="*60)
    print("Auto-Labeling Images from MinIO")
    print("="*60)
    
    # Initialize YOLO model (pretrained on COCO dataset)
    print("\n📥 Loading YOLOv8 model...")
    model = YOLO('yolov8n.pt')
    
    # Connect to MinIO
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        print("✓ Connected to MinIO")
    except Exception as e:
        print(f"❌ Failed to connect to MinIO: {e}")
        return
    
    # Create output directory
    output_dir = Path("dataset/bread_qa_auto_labeled")
    
    labeled_count = {'good': 0, 'bad': 0}
    
    for class_name in ['good', 'bad']:
        print(f"\n{'='*60}")
        print(f"Processing {class_name.upper()} bread images...")
        print(f"{'='*60}")
        
        class_id = 0 if class_name == 'good' else 1
        
        # Create directories
        img_dir = output_dir / 'images' / class_name
        label_dir = output_dir / 'labels' / class_name
        img_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        
        # List objects in MinIO
        prefix = f"training/general/{class_name}/"
        objects = client.list_objects(BUCKET_NAME, prefix=prefix, recursive=True)
        
        for obj in objects:
            if obj.object_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                filename = Path(obj.object_name).name
                local_img_path = img_dir / filename
                
                # Download image
                try:
                    client.fget_object(BUCKET_NAME, obj.object_name, str(local_img_path))
                    
                    # Run YOLO detection
                    results = model(str(local_img_path), conf=0.3, verbose=False)
                    
                    # Get image dimensions
                    img = cv2.imread(str(local_img_path))
                    img_height, img_width = img.shape[:2]
                    
                    # Create label file
                    label_path = label_dir / f"{local_img_path.stem}.txt"
                    
                    detections = results[0].boxes
                    if len(detections) > 0:
                        # Use the largest detected object as the bread
                        largest_idx = 0
                        largest_area = 0
                        
                        for i, box in enumerate(detections):
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            area = (x2 - x1) * (y2 - y1)
                            if area > largest_area:
                                largest_area = area
                                largest_idx = i
                        
                        # Get the largest detection
                        box = detections[largest_idx]
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        # Convert to YOLO format
                        x_center = ((x1 + x2) / 2) / img_width
                        y_center = ((y1 + y2) / 2) / img_height
                        width = (x2 - x1) / img_width
                        height = (y2 - y1) / img_height
                        
                        # Write label
                        with open(label_path, 'w') as f:
                            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                        
                        print(f"  ✓ {filename}: Detected object ({width*100:.1f}% × {height*100:.1f}%)")
                        labeled_count[class_name] += 1
                    else:
                        # No detection - create full-image box as fallback
                        with open(label_path, 'w') as f:
                            f.write(f"{class_id} 0.5 0.5 0.9 0.9\n")
                        print(f"  ⚠️ {filename}: No detection, using 90% coverage box")
                        labeled_count[class_name] += 1
                        
                except Exception as e:
                    print(f"  ❌ {filename}: Error - {e}")
    
    # Create dataset YAML
    yaml_path = output_dir / "data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(f"""# Auto-labeled Bread Quality Dataset
path: {output_dir.absolute()}
train: images/good
val: images/bad

# Classes
names:
  0: good
  1: bad
""")
    
    print("\n" + "="*60)
    print("✅ Auto-labeling complete!")
    print("="*60)
    print(f"Good images labeled: {labeled_count['good']}")
    print(f"Bad images labeled: {labeled_count['bad']}")
    print(f"\nDataset saved to: {output_dir.absolute()}")
    print(f"Config file: {yaml_path}")
    
    print("\n⚠️  IMPORTANT:")
    print("These are auto-generated labels based on object detection.")
    print("They may not be perfect! Review them before training.")
    print("\nTo review and fix labels, use: label_images_interactive.py")
    
    print("\n📋 To train with this dataset:")
    print(f"  yolo detect train model=yolov8n.pt data={yaml_path} epochs=100 imgsz=640 batch=8 name=bread_qa_auto")
    
    return output_dir


if __name__ == "__main__":
    try:
        download_and_auto_label()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
