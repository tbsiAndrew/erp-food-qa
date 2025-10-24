# Quick Start: Label Your Bread Images

I've created **2 labeling tools** for you. Choose based on your preference:

---

## ✅ Option 1: Auto-Label (Fastest - 2 minutes)

Uses pretrained YOLO to automatically detect objects and create bounding boxes.

### Run:
```powershell
cd "d:\_Andrew Files\Development\AmpliFy\erp-food-qa"
.\.venv\Scripts\python.exe auto_label_images.py
```

### What it does:
1. Downloads all images from MinIO (`good` and `bad` folders)
2. Runs YOLOv8 detection on each image
3. Uses the **largest detected object** as the bread bounding box
4. Creates YOLO label files automatically
5. Saves to `dataset/bread_qa_auto_labeled/`

### Pros:
- ✅ Very fast (2-3 minutes total)
- ✅ No manual work required
- ✅ Creates valid YOLO format labels

### Cons:
- ⚠️ May not be perfectly accurate
- ⚠️ Detects largest object (might be wrong if bread is small in image)
- ⚠️ Recommended to review labels before training

---

## ✅ Option 2: Interactive Labeling (Most Accurate - 20 minutes)

Draw bounding boxes manually with mouse for perfect annotations.

### Run:
```powershell
cd "d:\_Andrew Files\Development\AmpliFy\erp-food-qa"
.\.venv\Scripts\python.exe label_images_interactive.py
```

### What it does:
1. Downloads all images from MinIO
2. Opens each image in a window
3. You **click and drag** to draw boxes around bread
4. Press 's' to save and move to next image
5. Saves to `dataset/bread_qa_labeled/`

### Controls:
- **Mouse drag**: Draw bounding box
- **'s'**: Save labels and next image
- **'c'**: Clear all boxes (start over)
- **'n'**: Skip image (no labels)
- **'q'**: Quit session
- **'h'**: Show help

### Pros:
- ✅ Perfect accuracy
- ✅ Full control over annotations
- ✅ Can draw multiple boxes per image

### Cons:
- ⏱️ Takes ~20 minutes for 28 images
- 🖱️ Requires manual mouse work

---

## 🎯 Recommended Workflow

### For Quick Testing (Use Auto-Label):
```powershell
# 1. Auto-label images
.\.venv\Scripts\python.exe auto_label_images.py

# 2. Train model immediately
yolo detect train model=yolov8n.pt data=dataset/bread_qa_auto_labeled/data.yaml epochs=100 imgsz=640 batch=8 name=bread_qa_v2
```

### For Production Quality (Use Interactive):
```powershell
# 1. Label images manually
.\.venv\Scripts\python.exe label_images_interactive.py

# 2. Train model with perfect labels
yolo detect train model=yolov8n.pt data=dataset/bread_qa_labeled/data.yaml epochs=100 imgsz=640 batch=8 name=bread_qa_v2
```

---

## 📊 What Proper Labels Look Like

### YOLO Label Format (`.txt` file):
```
class_id x_center y_center width height
```

All values except `class_id` are **normalized** (0.0 to 1.0).

### Example - Bread in center taking up 60% of image:
```
0 0.5 0.5 0.6 0.6
```
- `0` = class 0 (good bread)
- `0.5 0.5` = center of image
- `0.6 0.6` = 60% width, 60% height

### Example - Multiple breads:
```
0 0.3 0.4 0.25 0.3
0 0.7 0.6 0.2 0.25
```

### Bad Label (what you have now):
```
0 0.5 0.5 1.0 1.0
```
This is 100% coverage - a dummy placeholder that teaches the model nothing!

---

## 🚀 After Labeling

### 1. Verify Labels Were Created
```powershell
# Check auto-labeled dataset
dir dataset\bread_qa_auto_labeled\labels\good
dir dataset\bread_qa_auto_labeled\labels\bad

# Or interactive-labeled dataset
dir dataset\bread_qa_labeled\good\*.txt
dir dataset\bread_qa_labeled\bad\*.txt
```

You should see `.txt` files matching each image.

### 2. Train Model
```powershell
# Using auto-labeled data
yolo detect train model=yolov8n.pt data=dataset/bread_qa_auto_labeled/data.yaml epochs=100 imgsz=640 batch=8 name=bread_qa_v2

# Or using interactive-labeled data
yolo detect train model=yolov8n.pt data=dataset/bread_qa_labeled/data.yaml epochs=100 imgsz=640 batch=8 name=bread_qa_v2
```

### 3. Test Detection
```powershell
# Test if model can now detect bread
.\.venv\Scripts\python.exe test_model_detection.py
```

Expected output:
```
Detection Results:
Number of detections: 1 or more
  Class: good (ID: 0)
  Confidence: 0.75+
```

### 4. Update Web App

Once model is trained and working, update `web/app.py` to use the new model:

```python
# Look for: bread_qa_v2 (latest trained model)
model_path = 'runs/detect/bread_qa_v2/weights/best.pt'
```

### 5. Restart Servers
```powershell
taskkill /F /IM python.exe
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
cd web ; ..\.venv\Scripts\python.exe app.py
```

---

## 📈 Expected Results

### Before (Dummy Labels):
- mAP50: 0.203 (20%)
- Detections: 0
- Detection boxes: None

### After (Proper Labels):
- mAP50: >0.70 (70%+)
- Detections: 1+ per image
- Detection boxes: Visible on bread!

---

## 💡 Tips

1. **Start with auto-label** for quick testing
2. If accuracy is poor, use **interactive labeling** for better results
3. **Draw tight boxes** - box should closely fit around bread
4. **Label all breads** in image if multiple visible
5. Add more images (100+ per class) for production quality

---

## ❓ Troubleshooting

### "No module named 'minio'"
```powershell
.\.venv\Scripts\pip.exe install minio
```

### "Cannot connect to MinIO"
Check MinIO is running:
```powershell
# Open in browser
start http://localhost:9001
```

### "No images found"
Check images exist in MinIO:
- http://localhost:9001/browser/qa-images/training%2Fgeneral%2Fgood
- http://localhost:9001/browser/qa-images/training%2Fgeneral%2Fbad

---

## 🎯 Next Steps

1. **Choose labeling method** (auto or interactive)
2. **Run the labeling script**
3. **Train model** with properly labeled data
4. **Test detection** with test_model_detection.py
5. **Update web app** to use new model
6. **See detection boxes** appear! 🎉
