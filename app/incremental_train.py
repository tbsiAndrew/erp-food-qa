"""
Incremental YOLO Training - Fine-tune existing model with new data
This script adds new training data to the existing model without starting from scratch
"""
import os
import yaml
import shutil
from pathlib import Path
from ultralytics import YOLO
import argparse

def reorganize_new_data():
    """Move images from good/bad folders to train/val folders"""
    dataset_path = Path('dataset/bread_qa_auto_labeled')
    
    # Source directories (where new images are uploaded)
    good_dir = dataset_path / 'images' / 'good'
    bad_dir = dataset_path / 'images' / 'bad'
    
    # Target directories
    train_img_dir = dataset_path / 'images' / 'train'
    val_img_dir = dataset_path / 'images' / 'val'
    train_label_dir = dataset_path / 'labels' / 'train'
    val_label_dir = dataset_path / 'labels' / 'val'
    
    # Create directories if needed
    train_img_dir.mkdir(parents=True, exist_ok=True)
    val_img_dir.mkdir(parents=True, exist_ok=True)
    train_label_dir.mkdir(parents=True, exist_ok=True)
    val_label_dir.mkdir(parents=True, exist_ok=True)
    
    moved_count = 0
    
    def move_files(src_img_dir, src_label_dir, class_id, class_name):
        nonlocal moved_count
        if not src_img_dir.exists():
            return 0
        
        images = list(src_img_dir.glob('*.jpg')) + list(src_img_dir.glob('*.jpeg')) + list(src_img_dir.glob('*.png'))
        
        for img_path in images:
            # 80% train, 20% val
            import random
            is_train = random.random() < 0.8
            
            target_img_dir = train_img_dir if is_train else val_img_dir
            target_label_dir = train_label_dir if is_train else val_label_dir
            
            # Move image
            new_img_path = target_img_dir / img_path.name
            shutil.move(str(img_path), str(new_img_path))
            
            # Move or create label
            label_path = src_label_dir / f"{img_path.stem}.txt"
            new_label_path = target_label_dir / f"{img_path.stem}.txt"
            
            if label_path.exists():
                shutil.move(str(label_path), str(new_label_path))
            else:
                # Create label with full image bounding box
                with open(new_label_path, 'w') as f:
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            moved_count += 1
        
        return len(images)
    
    # Move good and bad images
    good_label_dir = dataset_path / 'labels' / 'good'
    bad_label_dir = dataset_path / 'labels' / 'bad'
    
    good_count = move_files(good_dir, good_label_dir, 0, 'good')
    bad_count = move_files(bad_dir, bad_label_dir, 1, 'bad')
    
    return moved_count, good_count, bad_count


def incremental_train(epochs=10, batch=8, patience=5, model_version='bread_qa', dataset_folder=None):
    """
    Fine-tune existing model with new data
    
    Args:
        epochs: Number of epochs for fine-tuning (default: 10, since we're updating existing model)
        batch: Batch size
        patience: Early stopping patience
    """
    print("=" * 60)
    print("🔄 Incremental YOLO Training - Fine-tuning existing model")
    print("=" * 60)
    
    if dataset_folder:
        # Use provided temp folder (from backend)
        dataset_path = Path(dataset_folder)
        print(f"\n📁 Using custom dataset folder: {dataset_path}")
        data_yaml = dataset_path / 'data.yaml'
        train_img_dir = dataset_path / 'images' / 'train'
        val_img_dir = train_img_dir  # Use train for val if no val split
        train_label_dir = dataset_path / 'labels' / 'train'
        val_label_dir = train_label_dir
        # Count images
        train_images = list(train_img_dir.glob('*.*'))
        val_images = list(val_img_dir.glob('*.*'))
        total_images = len(train_images) + len(val_images)
        print(f"\n📊 Current dataset size:")
        print(f"   Train: {len(train_images)}")
        print(f"   Val: {len(val_images)}")
        print(f"   Total: {total_images}")
        if total_images == 0:
            print("\n❌ No training data available in temp folder")
            return None
    else:
        # Legacy: reorganize from bread_qa_auto_labeled
        print("\n📁 Reorganizing new training data...")
        moved, good, bad = reorganize_new_data()
        if moved == 0:
            print("❌ No new training data found in good/bad folders")
            print("   Upload images via the web interface first")
            return None
        print(f"✅ Moved {moved} images to train/val folders")
        print(f"   - Good: {good}")
        print(f"   - Bad: {bad}")
        dataset_path = Path('dataset/bread_qa_auto_labeled')
        data_yaml = dataset_path / 'data.yaml'
    
    # Find the current best model
    # Use previous bread_qa version if exists, else base model
    detect_dir = Path('runs/detect')
    bread_versions = [d.name for d in detect_dir.iterdir() if d.is_dir() and d.name.startswith('bread_qa') and d.name.replace('bread_qa','').isdigit()]
    nums = [int(v.replace('bread_qa', '')) for v in bread_versions]
    prev_version = f"bread_qa{max(nums)}" if nums else 'bread_qa'
    trained_model_path = Path(f'runs/detect/{prev_version}/weights/best.pt')
    base_model_path = Path('models/yolov8n.pt')
    if trained_model_path.exists():
        model_path = trained_model_path
        print(f"\n✅ Found previous trained model: {model_path}")
        print(f"   → Will fine-tune this model with new data")
    else:
        model_path = base_model_path
        print(f"\n⚠️  No existing trained model found")
        print(f"   → Starting from base model: {model_path}")
    
    # Verify dataset config exists
    if not data_yaml.exists():
        print(f"\n❌ Dataset config not found: {data_yaml}")
        print("   Creating new config...")
        config = {
            'path': str(dataset_path.absolute()),
            'train': str((dataset_path / 'images/train').absolute()),
            'val': str((dataset_path / 'images/val').absolute()),
            'names': {
                0: 'good',
                1: 'bad'
            }
        }
        with open(data_yaml, 'w') as f:
            yaml.dump(config, f)
        print("✅ Created data.yaml")
    
    # Count current dataset size
    train_images = list((dataset_path / 'images' / 'train').glob('*.*'))
    val_images = list((dataset_path / 'images' / 'val').glob('*.*'))
    total_images = len(train_images) + len(val_images)
    
    print(f"\n📊 Current dataset size:")
    print(f"   Train: {len(train_images)}")
    print(f"   Val: {len(val_images)}")
    print(f"   Total: {total_images}")
    
    if total_images == 0:
        print("\n❌ No training data available")
        return None
    
    # Load model and fine-tune
    print(f"\n🚀 Starting incremental training...")
    print(f"   Epochs: {epochs}")
    print(f"   Batch: {batch}")
    print(f"   Patience: {patience}")
    
    try:
        model = YOLO(str(model_path))
        
        # Fine-tune with RESUME capability
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=640,
            batch=batch,
            name=model_version,
            exist_ok=True,  # Allow overwriting existing run
            patience=patience,
            save=True,
            plots=True,
            device='cpu',  # Change to '0' for CUDA GPU
            verbose=True,
            # Lower learning rate for fine-tuning
            lr0=0.001,  # Initial learning rate (lower than default 0.01)
            lrf=0.01,   # Final learning rate fraction
            # Keep augmentation but reduce intensity
            augment=True,
            mixup=0.05,
            mosaic=0.3,
            degrees=10.0,
            scale=0.2,
            flipud=0.2,
            fliplr=0.5,
        )
        print(f"\n✅ Incremental training complete!")
        print(f"   Updated model saved to: runs/detect/{model_version}/weights/best.pt")
        return results
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='Incremental YOLO training - fine-tune existing model')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs (default: 10 for fine-tuning)')
    parser.add_argument('--batch', type=int, default=8, help='Batch size')
    parser.add_argument('--patience', type=int, default=5, help='Early stopping patience')
    parser.add_argument('--model_version', type=str, default='bread_qa', help='Model version/folder name for saving trained weights')
    parser.add_argument('--dataset_folder', type=str, default=None, help='Custom dataset folder (temp folder from backend)')
    args = parser.parse_args()
    results = incremental_train(
        epochs=args.epochs,
        batch=args.batch,
        patience=args.patience,
        model_version=args.model_version,
        dataset_folder=args.dataset_folder
    )
    
    if results:
        print("\n" + "=" * 60)
        print("✅ Model updated successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart your FastAPI server to load the updated model")
        print("2. Test the updated model with new images")
        print("3. Continue uploading more training data to improve accuracy")
    else:
        print("\n❌ Training failed - check errors above")


if __name__ == '__main__':
    main()
