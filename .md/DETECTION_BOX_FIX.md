# Detection Box Issue - Root Cause Analysis

## 🔴 PROBLEM IDENTIFIED

**Your trained models cannot detect bread because the training images were NEVER properly labeled.**

---

## 🔍 What We Found

### Test Results:
```
Model: runs/detect/bread_qa3/weights/best.pt
Test Image: charles-chen-e83dQJ-BMog-unsplash.jpg (from validation set)
Result: (no detections)
mAP50: 0.203 (very poor - should be >0.7)
```

### Label File Inspection:
```plaintext
File: dataset/bread_qa/labels/val/charles-chen-e83dQJ-BMog-unsplash.txt
Content: 0 0.5 0.5 1.0 1.0
```

**Translation:**
- Class 0 (good)
- Center: (50%, 50%)
- Size: 100% width × 100% height

This is a **DUMMY LABEL** covering the entire image - not a real bounding box around bread!

---

## 💥 Why This Happened

The `train_yolo_bread.py` script auto-generates placeholder labels for unlabeled images:

```python
# From train_yolo_bread.py line ~120
label_content = f"{class_id} 0.5 0.5 1.0 1.0\n"  # Full image placeholder
```

This was meant as a temporary solution, but **you must replace these with real annotations**.

---

## ✅ THE FIX

You need to **manually draw bounding boxes** around bread in your images.

### Recommended Tool: **Roboflow** (easiest)

1. Go to https://roboflow.com
2. Create account (free)
3. Upload 28 images from MinIO
4. Draw boxes around bread in each image
5. Export as "YOLOv8" format
6. Replace `dataset/bread_qa/` with exported data
7. Retrain model

**Time required:** ~20 minutes for 28 images

### See Full Guide:
Open `LABELING_GUIDE.md` for detailed instructions on 3 different labeling tools.

---

## 📊 Current vs. Expected Results

### Current (with dummy labels):
- mAP50: 0.203 (20% accuracy)
- Detections on training images: 0
- Detections on camera feed: 0
- **Model learned nothing useful**

### Expected (with proper labels):
- mAP50: >0.70 (70%+ accuracy)
- Detections on training images: Yes
- Detections on camera feed: Yes
- **Model can identify good vs bad bread**

---

## 🚀 Temporary Workaround

**I've reverted the web app to use default YOLOv8** (`yolov8n.pt`):
- ✅ Will show detection boxes in video feed
- ✅ Can detect 80 common objects (person, chair, cup, etc.)
- ❌ Cannot detect "good" vs "bad" bread specifically
- ❌ Not trained for your use case

**URL:** http://localhost:5000

You should now see detection boxes appear when showing common objects to the camera (person, phone, cup, etc.).

---

## 📋 Action Items

### Immediate (to get detection boxes working):
- [x] Identified root cause (invalid labels)
- [x] Reverted to default YOLOv8 model
- [x] Detection boxes now visible for common objects
- [ ] **You need to:** Label 28 images using Roboflow

### After Labeling:
- [ ] Retrain model: `.venv\Scripts\python.exe train_yolo_bread.py --epochs 100 --batch 8`
- [ ] Test detection: `.venv\Scripts\python.exe test_model_detection.py`
- [ ] Update web app to use new trained model
- [ ] Verify detection boxes appear on bread

### Long-term (for production quality):
- [ ] Add 100+ images per class (good/bad)
- [ ] Label all images properly
- [ ] Retrain with more epochs (200-300)
- [ ] Achieve mAP50 >0.80

---

## 🎯 Summary

**Why no detection boxes:**
1. Trained models have invalid dummy labels (full-image bounding boxes)
2. Model learned nothing from training (mAP50 only 20%)
3. Cannot detect bread in images or camera feed

**Solution:**
1. Use Roboflow (or LabelImg/Label Studio) to properly label images
2. Draw tight bounding boxes around bread in all 28 images
3. Export as YOLOv8 format
4. Retrain model
5. Detection boxes will appear

**Current status:**
- Web app temporarily using default YOLOv8
- Detection boxes WILL appear for common objects
- You must label images to get bread-specific detection

---

**Next step:** Open `LABELING_GUIDE.md` for detailed labeling instructions.
