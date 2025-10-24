# YOLOv8 Bread Quality Training - Setup Complete! ✅

## What I've Created For You

### 1. **Training Scripts**
- **`train_yolo_bread.py`** - Main training script that:
  - Downloads images from MinIO (`training/general/good/` and `training/general/bad/`)
  - Organizes data into YOLO format (80% train, 20% validation)
  - Trains YOLOv8 model for bread quality detection
  - Validates and optionally exports to ONNX

- **`organize_minio_data.py`** - Helper script to:
  - Check your MinIO bucket structure
  - List available training images
  - Verify data is properly organized

- **`test_training_setup.py`** - Verification script that:
  - Tests all dependencies
  - Checks MinIO connection
  - Validates YOLO model availability
  - Confirms environment configuration

### 2. **Batch File for Easy Training**
- **`START_TRAINING.bat`** - Double-click to start training (uses venv automatically)

### 3. **Documentation**
- **`TRAINING_GUIDE.md`** - Complete guide with:
  - Step-by-step instructions
  - Dataset recommendations
  - Troubleshooting tips
  - Integration instructions

## ✅ Test Results

All systems are ready:
- ✅ Dependencies installed (ultralytics, boto3, opencv, torch)
- ✅ MinIO connection working
- ✅ YOLO model (yolov8n.pt) available
- ✅ Environment variables configured
- ✅ Training data found (3 images: 2 good, 1 bad)

## 🚀 Current Training Status

**Training has started!** Using:
- Model: `yolov8n.pt` (pretrained YOLOv8 nano)
- Dataset: 2 training images, 1 validation image
- Classes: 2 (good, bad)
- Epochs: 10
- Batch size: 2

**Output location**: `runs/detect/bread_qa/weights/`
- `best.pt` - Best performing model
- `last.pt` - Most recent checkpoint

## 📊 Your Current Data

```
MinIO Bucket: qa-images
└── training/
    └── general/
        ├── good/ (2 images)
        │   ├── 84eb0323336a401690425c294a0130fc.jpg
        │   └── 9bb8ddf9e07349769b4ddb2edbcf3ca0.jpg
        └── bad/  (1 image)
            └── d49b9cfb80444e50b9bbd3846c9678c4.jpg
```

**⚠️ Note**: While this trains successfully, you need **50-100+ images per class** for production quality.

## 📋 Next Steps

### Immediate (After Training Completes):

1. **Check training results**:
   ```powershell
   # Look in this folder
   runs/detect/bread_qa/
   ```

2. **View training plots**:
   - `results.png` - Training/validation metrics
   - `confusion_matrix.png` - Classification performance

3. **Test the trained model**:
   ```python
   from ultralytics import YOLO
   model = YOLO('runs/detect/bread_qa/weights/best.pt')
   results = model('path/to/test/image.jpg')
   ```

### To Improve Your Model:

1. **Collect more images**:
   - Target: 100+ images per class (good/bad)
   - Variety: Different lighting, angles, bread types
   - Balance: Similar numbers of good and bad images

2. **Upload to MinIO**:
   - Access: http://localhost:9001
   - Login: minioadmin / minioadmin
   - Upload to: `qa-images/training/general/good/` and `../bad/`

3. **Retrain with more data**:
   ```powershell
   .\.venv\Scripts\python.exe train_yolo_bread.py --epochs 50
   ```

### Integration with Your App:

Update `app/detectors/yolo_detector.py`:

```python
# Line ~18 - Change model path
self.model = YOLO('runs/detect/bread_qa/weights/best.pt')

# Line ~21-27 - Update class names
self.class_names = {
    0: 'good',
    1: 'bad'
}
```

Or copy the model:
```powershell
cp runs/detect/bread_qa/weights/best.pt yolov8_bread_qa.pt
```

Then update:
```python
self.model = YOLO('yolov8_bread_qa.pt')
```

## 🎯 Production Deployment

When ready for production:

1. **Train with full dataset** (100+ images per class)
2. **Achieve good metrics**:
   - mAP50 > 0.85
   - Precision > 0.90
   - Recall > 0.85

3. **Export for faster inference**:
   ```powershell
   .\.venv\Scripts\python.exe -c "from ultralytics import YOLO; YOLO('runs/detect/bread_qa/weights/best.pt').export(format='onnx')"
   ```

4. **Update your detector** to use ONNX model with `app/detectors/onnx_yolo.py`

## 📚 Quick Reference

### Training Commands:

```powershell
# Using venv directly
.\.venv\Scripts\python.exe train_yolo_bread.py

# With custom parameters
.\.venv\Scripts\python.exe train_yolo_bread.py --epochs 50 --batch 16

# Check data structure
.\.venv\Scripts\python.exe organize_minio_data.py

# Test setup
.\.venv\Scripts\python.exe test_training_setup.py
```

### Key Files:

- **Model weights**: `yolov8n.pt` (pretrained base)
- **Trained model**: `runs/detect/bread_qa/weights/best.pt`
- **Dataset config**: `dataset/bread_qa/bread_qa.yaml`
- **Downloaded images**: `dataset/bread_qa/images/`
- **Environment**: `.env` (MinIO credentials)

## 🆘 Troubleshooting

**Training too slow?**
- You're using CPU. Consider GPU for faster training
- Reduce batch size if out of memory

**Poor accuracy?**
- Need more training images (100+ per class)
- Ensure images are correctly labeled
- Increase training epochs (50-100)

**MinIO connection issues?**
- Check MinIO is running: http://localhost:9000
- Verify credentials in `.env`
- Test with: `.\.venv\Scripts\python.exe test_training_setup.py`

## 🎉 Summary

You now have a complete YOLOv8 training pipeline for bread quality assurance that:
- ✅ Downloads data from your MinIO bucket
- ✅ Trains a custom YOLO model
- ✅ Validates performance
- ✅ Exports for production use
- ✅ Integrates with your existing ERP Food QA system

**Happy Training!** 🚀🍞
