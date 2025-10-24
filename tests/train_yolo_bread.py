"""
YOLOv8 Training Script for Bread/Food Quality Assurance
Downloads training data from MinIO/S3 and trains a custom YOLOv8 model
"""
import os
import sys
import shutil
import boto3
from pathlib import Path
from dotenv import load_dotenv
from ultralytics import YOLO

# Load environment variables
load_dotenv()

class BreadQualityTrainer:
    def __init__(self):
        """Initialize trainer with S3/MinIO connection"""
        self.s3_endpoint = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
        self.s3_access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
        self.s3_secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')
        self.s3_bucket = os.getenv('S3_BUCKET', 'qa-images')
        self.s3_region = os.getenv('S3_REGION', 'us-east-1')
        
        # Initialize S3 client
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.s3_endpoint,
            aws_access_key_id=self.s3_access_key,
            aws_secret_access_key=self.s3_secret_key,
            region_name=self.s3_region
        )
        
        # Setup paths
        self.dataset_path = Path('dataset/bread_qa')
        self.model_path = 'yolov8n.pt'
        
    def setup_directories(self):
        """Create directory structure for YOLO training"""
        print("📁 Setting up directory structure...")
        
        # Create dataset structure
        dirs = [
            self.dataset_path / 'images' / 'train',
            self.dataset_path / 'images' / 'val',
            self.dataset_path / 'labels' / 'train',
            self.dataset_path / 'labels' / 'val',
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created {dir_path}")
    
    def download_training_data(self):
        """Download images from MinIO/S3 bucket"""
        print("\n📥 Downloading training data from MinIO...")
        
        try:
            # List objects in the training/general/ prefix
            response = self.s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix='training/general/'
            )
            
            if 'Contents' not in response:
                print("⚠️  No objects found in training/general/")
                return 0
            
            downloaded = 0
            for obj in response['Contents']:
                key = obj['Key']
                
                # Skip if it's a directory marker
                if key.endswith('/'):
                    continue
                
                # Determine if it's good or bad based on folder structure
                # Expected: training/general/good/ or training/general/bad/
                parts = key.split('/')
                if len(parts) < 4:
                    print(f"⚠️  Skipping {key} - unexpected structure")
                    continue
                
                category = parts[2]  # 'good' or 'bad'
                filename = parts[-1]
                
                # Only process image files
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    continue
                
                # Download to appropriate directory (80% train, 20% val split)
                split = 'train' if downloaded % 5 != 0 else 'val'
                local_path = self.dataset_path / 'images' / split / filename
                
                # Download file
                self.s3.download_file(self.s3_bucket, key, str(local_path))
                downloaded += 1
                print(f"  ✓ Downloaded {key} -> {split}/{filename}")
                
                # Create label file (for classification, we'll create simple labels)
                # Class 0 = good, Class 1 = bad
                class_id = 0 if category.lower() == 'good' else 1
                label_path = self.dataset_path / 'labels' / split / f"{Path(filename).stem}.txt"
                
                # For classification/detection, create a full-image bounding box
                # Format: class_id x_center y_center width height (normalized 0-1)
                with open(label_path, 'w') as f:
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            print(f"\n✅ Downloaded {downloaded} images")
            return downloaded
            
        except Exception as e:
            print(f"❌ Error downloading data: {e}")
            return 0
    
    def create_dataset_config(self):
        """Create YAML configuration file for YOLO training"""
        print("\n📝 Creating dataset configuration...")
        
        config_path = self.dataset_path / 'bread_qa.yaml'
        
        # Get absolute path for the dataset
        abs_dataset_path = self.dataset_path.absolute()
        
        config_content = f"""# Bread/Food Quality Assurance Dataset
path: {abs_dataset_path}
train: images/train
val: images/val

# Number of classes
nc: 2

# Class names
names:
  0: good
  1: bad
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print(f"  ✓ Created {config_path}")
        return config_path
    
    def train_model(self, config_path, epochs=50, imgsz=640, batch=16):
        """Train YOLOv8 model on bread quality dataset"""
        print(f"\n🚀 Starting YOLOv8 training...")
        print(f"  Model: {self.model_path}")
        print(f"  Config: {config_path}")
        print(f"  Epochs: {epochs}")
        print(f"  Image Size: {imgsz}")
        print(f"  Batch Size: {batch}")
        
        try:
            # Load pretrained YOLOv8 model
            model = YOLO(self.model_path)
            
            # Train the model
            results = model.train(
                data=str(config_path),
                epochs=epochs,
                imgsz=imgsz,
                batch=batch,
                name='bread_qa',
                patience=10,  # Early stopping patience
                save=True,
                plots=True,
                device='cpu',  # Change to 'cuda' or '0' if you have GPU
                verbose=True
            )
            
            print("\n✅ Training complete!")
            print(f"  Best model saved to: runs/detect/bread_qa/weights/best.pt")
            
            return results
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validate_model(self):
        """Validate the trained model"""
        print("\n🔍 Validating trained model...")
        
        best_model_path = Path('runs/detect/bread_qa/weights/best.pt')
        
        if not best_model_path.exists():
            print("❌ Best model not found!")
            return
        
        try:
            model = YOLO(str(best_model_path))
            
            # Run validation
            metrics = model.val(
                data=str(self.dataset_path / 'bread_qa.yaml'),
                verbose=True
            )
            
            print("\n📊 Validation Results:")
            print(f"  mAP50: {metrics.box.map50:.3f}")
            print(f"  mAP50-95: {metrics.box.map:.3f}")
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
    
    def export_model(self):
        """Export trained model to ONNX format"""
        print("\n📦 Exporting model to ONNX...")
        
        best_model_path = Path('runs/detect/bread_qa/weights/best.pt')
        
        if not best_model_path.exists():
            print("❌ Best model not found!")
            return
        
        try:
            model = YOLO(str(best_model_path))
            
            # Export to ONNX
            model.export(format='onnx', imgsz=640)
            
            print("✅ Model exported to ONNX format")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def run_full_pipeline(self, epochs=50, imgsz=640, batch=16):
        """Run complete training pipeline"""
        print("=" * 60)
        print("YOLOv8 Bread Quality Assurance Training Pipeline")
        print("=" * 60)
        
        # Step 1: Setup directories
        self.setup_directories()
        
        # Step 2: Download training data
        num_images = self.download_training_data()
        if num_images == 0:
            print("\n❌ No training data downloaded. Please ensure images are in MinIO:")
            print(f"   Bucket: {self.s3_bucket}")
            print(f"   Path: training/general/good/ and training/general/bad/")
            return
        
        # Step 3: Create dataset config
        config_path = self.create_dataset_config()
        
        # Step 4: Train model
        results = self.train_model(config_path, epochs, imgsz, batch)
        
        if results is None:
            print("\n❌ Training failed!")
            return
        
        # Step 5: Validate model
        self.validate_model()
        
        # Step 6: Export to ONNX (optional)
        export = input("\n📦 Export model to ONNX format? (y/n): ").lower().strip()
        if export == 'y':
            self.export_model()
        
        print("\n" + "=" * 60)
        print("✅ Training pipeline complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Find your trained model at: runs/detect/bread_qa/weights/best.pt")
        print("2. Copy it to your project root or models/ directory")
        print("3. Update your YOLOQualityDetector to use the new model")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train YOLOv8 for bread quality assurance')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--imgsz', type=int, default=640, help='Input image size')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    
    args = parser.parse_args()
    
    trainer = BreadQualityTrainer()
    trainer.run_full_pipeline(
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch
    )


if __name__ == '__main__':
    main()
