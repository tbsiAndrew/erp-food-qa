# Quick Start: Real-Time YOLO Detection

## 🚀 Test Real-Time Detection Now!

### Step 1: Install YOLO
```bash
# Make sure you're in your project directory
cd "d:\_Andrew Files\Development\AmpliFy\erp-food-qa"

# Activate virtual environment
.venv\Scripts\activate

# Install YOLOv8
pip install ultralytics
```

### Step 2: Run Demo
```bash
python demo_yolo_realtime.py
```

This will:
- Open your webcam
- Show real-time object detection with bounding boxes
- Display FPS counter
- Press 'Q' to quit

### Step 3: See It Working!
You'll see bounding boxes with labels like:
- `person 0.92`
- `bottle 0.85`
- `phone 0.78`

## 📌 Important Notes

### Current Demo Limitations:
- Uses pre-trained YOLO (detects common objects, not food defects)
- To detect **mold, defects, contamination**, you need a custom-trained model

### For Production Food QA:
You have 2 options:

**Option A: Train Custom Model** (Best quality, runs locally)
1. Collect 200-500 images of good/defective food items
2. Label them with classes: good, mold, defect, discolored, etc.
3. Train YOLOv8 model
4. Deploy in your app

**Option B: Use Your API** (Current setup, works but slower)
1. Keep using `https://cp-rsl02.sin02.ds.network:2096/`
2. Send frames every 2 seconds
3. Display results with bounding boxes

## 🎯 Recommendation

**For best results**, I recommend:
1. **Now**: Use the demo to verify YOLO works on your machine
2. **Short-term**: Integrate YOLO into your Flask app for smooth UI
3. **Long-term**: Train a custom model specifically for food defects

## ❓ Questions?

- **Q: Will this detect food defects?**  
  A: Not yet - the demo uses a general object detector. For food defects, you need custom training.

- **Q: Can I use this in my web app?**  
  A: Yes! I can integrate YOLO into your Flask app to show detections in the browser.

- **Q: How do I train for mold/defects?**  
  A: You need labeled training data. I can help set this up.

## ✅ Next Steps

1. Run the demo script
2. Let me know if it works
3. I'll integrate YOLO into your Flask web interface
4. Add real-time bounding boxes to your camera view

---

**Try the demo now and let me know how it performs on your machine!** 🚀
