# 🍞 Bread Quality Detection - Labeling Tools

## 🎯 Quick Summary

Your model isn't detecting bread because **images were never properly labeled**. I've created 2 tools to fix this:

---

## 🚀 Quick Start (Choose One)

### Option A: Auto-Label (2 minutes) ⚡
```powershell
.\.venv\Scripts\python.exe auto_label_images.py
```
- Downloads images from MinIO
- Auto-detects objects and creates labels
- Fast but may need refinement

### Option B: Interactive Label (20 minutes) 🎨
```powershell
.\.venv\Scripts\python.exe label_images_interactive.py
```
- Downloads images from MinIO
- Click and drag to draw boxes manually
- Most accurate

---

## 📁 Your Images

Located in MinIO:
- **Good bread**: http://localhost:9001/browser/qa-images/training%2Fgeneral%2Fgood (18 images)
- **Bad bread**: http://localhost:9001/browser/qa-images/training%2Fgeneral%2Fbad (10 images)

**Total**: 28 images to label

---

## 🔧 What These Tools Do

### `auto_label_images.py`
1. Connects to MinIO at localhost:9000
2. Downloads all images from `training/general/good` and `training/general/bad`
3. Runs YOLOv8 on each image
4. Finds largest object and creates bounding box
5. Saves labels in YOLO format
6. Output: `dataset/bread_qa_auto_labeled/`

### `label_images_interactive.py`
1. Connects to MinIO at localhost:9000
2. Downloads all images
3. Opens each image in window
4. You draw boxes with mouse
5. Saves when you press 's'
6. Output: `dataset/bread_qa_labeled/`

---

## 📝 After Labeling

### Train Model:
```powershell
# If you used auto-label:
yolo detect train model=yolov8n.pt data=dataset/bread_qa_auto_labeled/data.yaml epochs=100 batch=8 name=bread_qa_v2

# If you used interactive:
yolo detect train model=yolov8n.pt data=dataset/bread_qa_labeled/data.yaml epochs=100 batch=8 name=bread_qa_v2
```

### Test Detection:
```powershell
.\.venv\Scripts\python.exe test_model_detection.py
```

Expected: Detection boxes appear on bread images!

### Update Web App:
After successful training, detection boxes will appear in http://localhost:5000

---

## 📚 Full Documentation

- **LABELING_QUICKSTART.md** - Step-by-step guide
- **LABELING_GUIDE.md** - Detailed labeling instructions
- **DETECTION_BOX_FIX.md** - Technical explanation of the issue

---

## ⚠️ Current Issue

**Problem**: Labels are dummy placeholders (`0 0.5 0.5 1.0 1.0`)
- These cover 100% of each image
- Model learned nothing
- No detections appear

**Solution**: Use one of the labeling tools above to create proper bounding boxes

---

## 🎯 Expected Timeline

1. **Label images**: 2-20 minutes (depending on tool)
2. **Train model**: 10-15 minutes (100 epochs)
3. **Test & verify**: 2 minutes
4. **See detection boxes**: Immediately after restart! ✅

---

## 💡 Recommendation

For your first attempt, use **auto_label_images.py** (fastest):
```powershell
.\.venv\Scripts\python.exe auto_label_images.py
```

Then train and test. If accuracy is poor, use **label_images_interactive.py** for perfect labels.

---

**Ready to start?** Open `LABELING_QUICKSTART.md` for detailed instructions!
