# Image Labeling Guide for Bread Quality Detection

## ⚠️ CRITICAL ISSUE FOUND

Your model training failed because **images were not properly labeled**. The label files contain dummy annotations (`0 0.5 0.5 1.0 1.0`) that cover the entire image, so the model learned nothing.

## 🎯 What You Need to Do

You must **manually draw bounding boxes** around bread in each image using a labeling tool.

---

## 📦 Option 1: Roboflow (RECOMMENDED - Easiest)

### Steps:
1. Go to https://roboflow.com (free account)
2. Create new project: "Bread Quality Detection"
3. Upload your 28 images from MinIO:
   - Good bread: `http://localhost:9001/browser/qa-images/training%2Fgeneral%2Fgood`
   - Bad bread: `http://localhost:9001/browser/qa-images/training%2Fgeneral%2Fbad`

4. **Label each image:**
   - Draw a box around the bread
   - Assign class: `good` or `bad`
   - Repeat for all 28 images (takes ~15-20 minutes)

5. **Export dataset:**
   - Format: `YOLOv8`
   - Download ZIP file

6. **Extract and replace:**
   ```powershell
   # Extract downloaded ZIP
   # Replace: dataset/bread_qa/ with the exported folder
   ```

7. **Retrain:**
   ```powershell
   .venv\Scripts\python.exe train_yolo_bread.py --epochs 100 --batch 8
   ```

---

## 📦 Option 2: LabelImg (Desktop Tool)

### Installation:
```powershell
pip install labelImg
labelImg
```

### Steps:
1. Open LabelImg
2. Click "Open Dir" → select `dataset/bread_qa/images/train`
3. Click "Change Save Dir" → select `dataset/bread_qa/labels/train`
4. Set format to **YOLO** (bottom right)
5. For each image:
   - Press `W` to draw rectangle
   - Draw box around bread
   - Enter class: `good` or `bad`
   - Press `Ctrl+S` to save
   - Press `D` for next image

6. Repeat for validation set: `dataset/bread_qa/images/val`

7. **Verify class mapping:**
   Edit `dataset/bread_qa/bread_qa.yaml`:
   ```yaml
   names:
     0: good
     1: bad
   ```

8. Retrain the model

---

## 📦 Option 3: Label Studio (Web-based, Self-hosted)

### Installation:
```powershell
pip install label-studio
label-studio start
```

### Steps:
1. Open http://localhost:8080
2. Create project "Bread QA"
3. Import images from `dataset/bread_qa/images/`
4. Set labeling interface: Object Detection with Bounding Box
5. Add labels: `good`, `bad`
6. Label all images
7. Export as `YOLO v8` format
8. Replace `dataset/bread_qa/` with exported data
9. Retrain

---

## 🔍 What Proper Labels Look Like

### YOLO label format (`.txt` file):
```
0 0.456 0.523 0.312 0.445
```

- `0` = class ID (0=good, 1=bad)
- `0.456` = x center (normalized 0-1)
- `0.523` = y center (normalized 0-1)
- `0.312` = width (normalized 0-1)
- `0.445` = height (normalized 0-1)

### Example for bread taking up 50% of image:
```
0 0.5 0.5 0.5 0.5
```

### Multiple breads in one image:
```
0 0.3 0.4 0.2 0.3
0 0.7 0.6 0.25 0.35
```

---

## ⚡ Quick Test After Labeling

After you label images and retrain, test with:

```powershell
.venv\Scripts\python.exe test_model_detection.py
```

This will show if the model can now detect bread in training images.

---

## 📊 Current Status

- ❌ **Images**: 28 total (18 good, 10 bad)
- ❌ **Labels**: Invalid (full-image dummy boxes)
- ❌ **Model mAP50**: 0.203 (very poor)
- ❌ **Detections**: 0 (model can't detect anything)

## 📊 After Proper Labeling

- ✅ **Images**: Same 28 images
- ✅ **Labels**: Proper bounding boxes around bread
- ✅ **Model mAP50**: Expected >0.7 (70%+)
- ✅ **Detections**: Should detect bread in camera

---

## 💡 Tips for Good Labels

1. **Draw tight boxes** - box should closely fit around bread
2. **Include partial breads** - if bread is cut off at edge, still label it
3. **Label all breads** - if multiple breads in one image, label each
4. **Consistent criteria** - define what makes bread "good" vs "bad":
   - Good: Golden color, proper texture, no mold
   - Bad: Burnt, moldy, deformed, wrong color
5. **Minimum 50+ images per class** for production quality

---

## 🚀 Next Steps

1. Choose a labeling tool (Roboflow recommended for beginners)
2. Label all 28 images (~20 minutes)
3. Retrain model with properly labeled data
4. Test detection in web app
5. If accuracy still low, add more images (target: 100+ per class)

---

## ❓ Need Help?

Ask me to:
- Set up a specific labeling tool
- Verify your labels are formatted correctly
- Adjust training parameters
- Add data augmentation for better results
