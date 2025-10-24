"""
Interactive Image Labeling Tool for Bread Quality Detection
Downloads images from MinIO and creates proper YOLO annotations
"""

import cv2
import numpy as np
from pathlib import Path
import os
from minio import Minio
from minio.error import S3Error

# MinIO configuration
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "qa-images"

# Class mapping
CLASSES = {
    'good': 0,
    'bad': 1
}

class ImageLabeler:
    def __init__(self):
        self.current_image = None
        self.current_image_path = None
        self.image_copy = None
        self.boxes = []
        self.drawing = False
        self.start_point = None
        self.window_name = "Label Bread Images (Press 'h' for help)"
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for drawing bounding boxes"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.image_copy = self.current_image.copy()
                # Draw boxes already saved
                for box in self.boxes:
                    cv2.rectangle(self.image_copy, box[0], box[1], (0, 255, 0), 2)
                # Draw current box being drawn
                cv2.rectangle(self.image_copy, self.start_point, (x, y), (0, 0, 255), 2)
                cv2.imshow(self.window_name, self.image_copy)
                
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                end_point = (x, y)
                # Add box to list
                self.boxes.append((self.start_point, end_point))
                # Draw all boxes
                self.image_copy = self.current_image.copy()
                for box in self.boxes:
                    cv2.rectangle(self.image_copy, box[0], box[1], (0, 255, 0), 2)
                cv2.imshow(self.window_name, self.image_copy)
                print(f"  Box added: {self.start_point} -> {end_point}")
    
    def convert_to_yolo(self, box, img_width, img_height):
        """Convert bounding box to YOLO format (normalized)"""
        x1, y1 = box[0]
        x2, y2 = box[1]
        
        # Ensure coordinates are in correct order
        x_min = min(x1, x2)
        x_max = max(x1, x2)
        y_min = min(y1, y2)
        y_max = max(y1, y2)
        
        # Calculate center, width, height (normalized)
        x_center = ((x_min + x_max) / 2) / img_width
        y_center = ((y_min + y_max) / 2) / img_height
        width = (x_max - x_min) / img_width
        height = (y_max - y_min) / img_height
        
        return x_center, y_center, width, height
    
    def label_image(self, image_path, class_id):
        """Label a single image"""
        print(f"\n{'='*60}")
        print(f"Labeling: {Path(image_path).name}")
        print(f"Class: {'good' if class_id == 0 else 'bad'}")
        print(f"{'='*60}")
        
        self.current_image_path = image_path
        self.current_image = cv2.imread(str(image_path))
        if self.current_image is None:
            print(f"⚠️  Failed to load image: {image_path}")
            return False
        
        self.image_copy = self.current_image.copy()
        self.boxes = []
        
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        cv2.imshow(self.window_name, self.image_copy)
        
        print("\nInstructions:")
        print("  - Click and drag to draw bounding box around bread")
        print("  - You can draw multiple boxes if multiple breads in image")
        print("  - Press 's' to SAVE labels")
        print("  - Press 'c' to CLEAR all boxes and start over")
        print("  - Press 'n' to SKIP this image (no labels)")
        print("  - Press 'q' to QUIT labeling")
        print("  - Press 'h' to show this help again")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('h'):
                # Show help
                print("\n--- HELP ---")
                print("  s = Save labels and continue to next image")
                print("  c = Clear all boxes")
                print("  n = Skip this image (no labels)")
                print("  q = Quit labeling session")
                print("  h = Show this help")
                
            elif key == ord('s'):
                # Save labels
                if len(self.boxes) == 0:
                    print("⚠️  No boxes drawn! Press 'n' to skip or draw a box.")
                    continue
                    
                self.save_labels(class_id)
                cv2.destroyAllWindows()
                return True
                
            elif key == ord('c'):
                # Clear boxes
                self.boxes = []
                self.image_copy = self.current_image.copy()
                cv2.imshow(self.window_name, self.image_copy)
                print("  Cleared all boxes")
                
            elif key == ord('n'):
                # Skip image
                print("  Skipped (no labels saved)")
                cv2.destroyAllWindows()
                return True
                
            elif key == ord('q'):
                # Quit
                cv2.destroyAllWindows()
                return False
        
        return True
    
    def save_labels(self, class_id):
        """Save labels in YOLO format"""
        img_height, img_width = self.current_image.shape[:2]
        
        # Create label file path
        label_path = Path(self.current_image_path).with_suffix('.txt')
        
        # Convert boxes to YOLO format and save
        with open(label_path, 'w') as f:
            for box in self.boxes:
                x_center, y_center, width, height = self.convert_to_yolo(box, img_width, img_height)
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        print(f"✓ Saved {len(self.boxes)} box(es) to: {label_path}")


def download_images_from_minio():
    """Download images from MinIO to local dataset folder"""
    print("\n" + "="*60)
    print("Downloading images from MinIO...")
    print("="*60)
    
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        # Create dataset directories
        base_dir = Path("dataset/bread_qa_labeled")
        for class_name in ['good', 'bad']:
            (base_dir / class_name).mkdir(parents=True, exist_ok=True)
        
        downloaded = {'good': 0, 'bad': 0}
        
        for class_name in ['good', 'bad']:
            prefix = f"training/general/{class_name}/"
            objects = client.list_objects(BUCKET_NAME, prefix=prefix, recursive=True)
            
            for obj in objects:
                if obj.object_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filename = Path(obj.object_name).name
                    local_path = base_dir / class_name / filename
                    
                    # Download only if not exists
                    if not local_path.exists():
                        client.fget_object(BUCKET_NAME, obj.object_name, str(local_path))
                        print(f"  ✓ {class_name}/{filename}")
                        downloaded[class_name] += 1
                    else:
                        print(f"  - {class_name}/{filename} (already exists)")
        
        print(f"\n✓ Downloaded: {downloaded['good']} good, {downloaded['bad']} bad images")
        print(f"✓ Saved to: {base_dir.absolute()}")
        return base_dir
        
    except S3Error as e:
        print(f"⚠️  MinIO error: {e}")
        return None


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  Bread Quality Image Labeling Tool                          ║
║  Interactive YOLO Annotation for Good/Bad Bread Detection   ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Download images from MinIO
    dataset_dir = download_images_from_minio()
    if dataset_dir is None:
        print("❌ Failed to download images from MinIO")
        return
    
    # Step 2: Get list of images to label
    good_images = list((dataset_dir / 'good').glob('*.jpg')) + list((dataset_dir / 'good').glob('*.png'))
    bad_images = list((dataset_dir / 'bad').glob('*.jpg')) + list((dataset_dir / 'bad').glob('*.png'))
    
    total_images = len(good_images) + len(bad_images)
    print(f"\n📊 Total images to label: {total_images}")
    print(f"   - Good bread: {len(good_images)}")
    print(f"   - Bad bread: {len(bad_images)}")
    
    if total_images == 0:
        print("❌ No images found!")
        return
    
    # Step 3: Label images
    labeler = ImageLabeler()
    labeled_count = 0
    
    print("\n🎯 Starting labeling session...")
    print("=" * 60)
    
    # Label good bread images
    print(f"\n📦 Labeling GOOD bread images ({len(good_images)} total)")
    for i, img_path in enumerate(good_images, 1):
        print(f"\n[{i}/{len(good_images)}] GOOD bread:")
        if not labeler.label_image(img_path, class_id=0):
            print("\n⚠️  Labeling session ended by user")
            break
        labeled_count += 1
    
    # Label bad bread images
    if labeled_count == len(good_images):
        print(f"\n📦 Labeling BAD bread images ({len(bad_images)} total)")
        for i, img_path in enumerate(bad_images, 1):
            print(f"\n[{i}/{len(bad_images)}] BAD bread:")
            if not labeler.label_image(img_path, class_id=1):
                print("\n⚠️  Labeling session ended by user")
                break
            labeled_count += 1
    
    # Step 4: Create YAML config
    print("\n" + "="*60)
    print(f"✅ Labeling complete! Labeled {labeled_count}/{total_images} images")
    print("="*60)
    
    # Create dataset YAML config
    yaml_path = dataset_dir / "data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(f"""# Bread Quality Detection Dataset
path: {dataset_dir.absolute()}
train: good
val: bad

# Classes
names:
  0: good
  1: bad
""")
    
    print(f"\n✓ Created dataset config: {yaml_path}")
    print("\n📋 Next steps:")
    print("1. Train model with this command:")
    print(f"   .venv\\Scripts\\python.exe -m ultralytics.models.yolo.detect.train \\")
    print(f"     model=yolov8n.pt \\")
    print(f"     data={yaml_path} \\")
    print(f"     epochs=100 \\")
    print(f"     imgsz=640 \\")
    print(f"     batch=8 \\")
    print(f"     name=bread_qa_labeled")
    print("\n2. Or use the training script:")
    print("   .venv\\Scripts\\python.exe train_yolo_bread.py --epochs 100")
    print("   (but update it to use the labeled dataset)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
