# YOLOv8 Bread/Food Quality Training Guide

This guide will help you retrain the YOLOv8 model for bread and food quality assurance using images from your MinIO/S3 bucket.

## 📋 Prerequisites

1. **MinIO Running**: Your MinIO server should be running at `http://localhost:9000`
2. **Training Images**: Images should be organized in MinIO at `qa-images/training/general/`
3. **Python Environment**: Python 3.8+ with dependencies installed

## 🚀 Quick Start

### Step 1: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 2: Check Your MinIO Data Structure

Before training, verify your data is properly organized:

```powershell
python organize_minio_data.py
```

**Expected Structure in MinIO:**
```
qa-images/
  └── training/
      └── general/
          ├── good/       (images of good bread/food)
          │   ├── bread_good_001.jpg
          │   ├── bread_good_002.jpg
          │   └── ...
          └── bad/        (images of bad/defective bread/food)
              ├── bread_bad_001.jpg
              ├── bread_bad_002.jpg
              └── ...
```

**To upload images to MinIO:**
1. Open MinIO web interface: http://localhost:9001
2. Login with:
   - Username: `minioadmin`
   - Password: `minioadmin`
3. Navigate to `qa-images` bucket
4. Create folders: `training/general/good/` and `training/general/bad/`
5. Upload your images to the appropriate folders

### Step 3: Train the Model

Run the training script:

```powershell
# Basic training (50 epochs, default settings)
python train_yolo_bread.py

# Custom training parameters
python train_yolo_bread.py --epochs 100 --imgsz 640 --batch 16
```

**Training Parameters:**
- `--epochs`: Number of training epochs (default: 50)
- `--imgsz`: Input image size (default: 640)
- `--batch`: Batch size (default: 16, reduce if out of memory)

### Step 4: Monitor Training

The training script will:
1. ✅ Download images from MinIO to `dataset/bread_qa/`
2. ✅ Split data into train (80%) and validation (20%)
3. ✅ Create YOLO dataset configuration
4. ✅ Train the model
5. ✅ Validate the trained model
6. ✅ Optionally export to ONNX format

**Training outputs:**
- Best model: `runs/detect/bread_qa/weights/best.pt`
- Last model: `runs/detect/bread_qa/weights/last.pt`
- Training plots: `runs/detect/bread_qa/`

## 📊 Dataset Recommendations

For good training results:

| Metric | Minimum | Recommended |
|--------|---------|-------------|
| Images per class | 50 | 200+ |
| Good/Bad ratio | 1:1 | 1:1 to 2:1 |
| Image resolution | 640x640 | 1280x1280 |
| Image variety | Basic | Multiple angles, lighting, backgrounds |

## 🔧 Using the Trained Model

### Option 1: Update YOLOQualityDetector

Update `app/detectors/yolo_detector.py` to use your trained model:

```python
# Before
self.model = YOLO('yolov8n.pt')

# After
self.model = YOLO('runs/detect/bread_qa/weights/best.pt')
```

### Option 2: Copy Model to Project Root

```powershell
cp runs/detect/bread_qa/weights/best.pt yolov8_bread_qa.pt
```

Then update the detector:
```python
self.model = YOLO('yolov8_bread_qa.pt')
```

### Option 3: Use ONNX Format

If you exported to ONNX:
```powershell
cp runs/detect/bread_qa/weights/best.onnx models/bread_qa.onnx
```

Then use `onnx_yolo.py` detector instead.

## 📈 Model Evaluation

After training, check these metrics:

- **mAP50**: Mean Average Precision at 50% IoU (higher is better)
- **mAP50-95**: Mean Average Precision at 50-95% IoU (higher is better)
- **Precision**: How many detections were correct
- **Recall**: How many actual objects were detected

Good results for quality control:
- mAP50 > 0.85
- Precision > 0.90
- Recall > 0.85

## 🔄 Retraining / Fine-tuning

To retrain with more data:

1. Add more images to MinIO (same folder structure)
2. Run the training script again
3. It will download all images and retrain

To continue training from your previous model:

```python
# In train_yolo_bread.py, modify the train_model method:
model = YOLO('runs/detect/bread_qa/weights/best.pt')  # Load your previous model
```

## 🐛 Troubleshooting

### Out of Memory Errors
```powershell
python train_yolo_bread.py --batch 8  # Reduce batch size
```

### Slow Training
- Enable GPU by changing `device='cpu'` to `device='0'` in `train_yolo_bread.py`
- Make sure CUDA is installed for GPU support

### No Images Downloaded
1. Check MinIO is running: http://localhost:9000
2. Verify credentials in `.env` file
3. Check bucket name and folder structure
4. Run `organize_minio_data.py` to diagnose

### Poor Model Performance
1. Collect more training images (100+ per class minimum)
2. Ensure images are properly labeled (good vs bad)
3. Increase training epochs: `--epochs 100`
4. Augment your dataset with more variety

## 📝 Training Tips

1. **Balance Your Dataset**: Try to have similar numbers of good and bad images
2. **Variety**: Include different lighting conditions, angles, and backgrounds
3. **Quality**: Use high-resolution images (at least 640x640)
4. **Validation**: Keep 20% of data for validation (handled automatically)
5. **Monitor Training**: Watch the loss curves in `runs/detect/bread_qa/`

## 🎯 Next Steps

1. Train your model
2. Test it on new images
3. Integrate it into your Flask/FastAPI application
4. Set up continuous retraining as you collect more data
5. Monitor model performance in production

## 📚 Additional Resources

- [Ultralytics YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Training Custom Models](https://docs.ultralytics.com/modes/train/)
- [Model Export Formats](https://docs.ultralytics.com/modes/export/)

## 🆘 Support

If you encounter issues:
1. Check the error messages carefully
2. Verify your MinIO connection and data structure
3. Ensure all dependencies are installed
4. Check GPU/CUDA setup if using GPU training
