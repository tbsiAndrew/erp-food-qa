# SETUP COMPLETE - Next Steps

## ✅ What Was Done

### 1. Replaced ONNX Model with API Integration
- Created `app/detectors/api_detector.py` - API-based detector
- Updated `app/config.py` - Changed from MODEL_PATH to API_ENDPOINT
- Updated `app/main.py` - Now uses APIDetector instead of ONNXDetector
- API endpoint configured: `https://cp-rsl02.sin02.ds.network:2096/`

### 2. Added Training/Fine-tuning System
- New `/train` endpoint in `app/main.py`
- Database table for training data: `app/sql/0003_training_data.sql`
- Database method `insert_training_data()` in `app/db.py`
- Training images stored in S3 bucket under `training/` prefix
- Training data forwarded to external API for model fine-tuning

### 3. Created Web Interface
- Flask app: `web/app.py`
- Inspection page: `web/templates/index.html` (camera + object detection + status)
- Training page: `web/templates/train.html` (capture images + label + submit)
- Navigation between inspection and training pages

### 4. Fixed Camera View Issue
- Updated processFrame() to properly clear and redraw canvas each frame
- Camera feed now updates continuously
- Bounding boxes drawn in real-time around detected objects
- Status indicator overlay on video

## 🚀 How to Run

### Step 1: Start Docker Services
```powershell
# Make sure Docker Desktop is running first!
docker compose up -d
```
This starts:
- PostgreSQL (port 5433)
- MinIO (ports 9000, 9001)

### Step 2: Run Database Migrations
```powershell
# Run SQL files to create tables
$env:PGPASSWORD='odoo'
psql -h localhost -p 5433 -U odoo -d erp_food_qa -f app/sql/0001_init.sql
psql -h localhost -p 5433 -U odoo -d erp_food_qa -f app/sql/0002_indexes.sql
psql -h localhost -p 5433 -U odoo -d erp_food_qa -f app/sql/0003_training_data.sql
```

### Step 3: Start FastAPI Backend
```powershell
# In terminal 1
cd "d:\_Andrew Files\Development\AmpliFy\erp-food-qa"
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 4: Start Flask Web Interface
```powershell
# In terminal 2 (new terminal)
cd "d:\_Andrew Files\Development\AmpliFy\erp-food-qa\web"
..\.venv\Scripts\activate
python app.py
```

### Step 5: Open Browser
- Inspection: http://127.0.0.1:5000/
- Training: http://127.0.0.1:5000/train

## 📋 Features

### Inspection Interface (http://127.0.0.1:5000/)
- Live camera feed with object detection
- Bounding boxes around detected objects
- Status indicator (PASS/FAIL/LOW CONFIDENCE)
- Click "Inspect" to send to API
- View detailed results in side panel

### Training Interface (http://127.0.0.1:5000/train)
- Capture images from camera
- Label images (good, bad, defect, contaminated, etc.)
- Assign quality grades (A, B, C, D, reject)
- Submit to fine-tune model
- Data stored in database and S3
- Forwarded to external API for training

## 🔧 Configuration

Edit `.env` file to configure:
```
DATABASE_URL=postgresql://odoo:odoo@localhost:5433/erp_food_qa
```

Edit `app/config.py` to change API endpoint or other settings.

## 📝 API Contract

Your external API at `https://cp-rsl02.sin02.ds.network:2096/` should support:

### Prediction Endpoint
**POST** `/predict`
```json
{
  "image": "base64_encoded_jpeg",
  "format": "base64"
}
```
Response:
```json
{
  "class": 0,
  "confidence": 0.95,
  "label": "good"
}
```

### Training Endpoint (Optional)
**POST** `/train`
```json
{
  "image": "base64_encoded_jpeg",
  "label": "good",
  "quality_grade": "A",
  "item_code": "ITEM001",
  "format": "base64"
}
```

## ⚠️ Important Notes

1. **Docker Desktop must be running** for PostgreSQL and MinIO
2. **SSL verification is disabled** for the API (self-signed cert)
3. **Camera permission required** in browser
4. All training data is stored locally even if API fails
5. The system gracefully handles API errors

## 🐛 Troubleshooting

### "Could not connect to endpoint URL"
- Make sure Docker services are running: `docker compose ps`
- Check MinIO is accessible: http://localhost:9001

### "Could not connect to the API"
- Check API endpoint is correct in `app/config.py`
- Verify network connectivity to `https://cp-rsl02.sin02.ds.network:2096/`
- API might be down or require authentication

### "Camera view not updating"
- Clear browser cache and reload
- Check browser console for JavaScript errors
- Make sure OpenCV.js is loaded (may take a few seconds)

### "Import errors"
- Activate virtual environment: `.venv\Scripts\activate`
- All required packages should already be in `requirements.txt`

## 📦 Next Steps

1. **Test the API endpoint** - Make sure it's reachable and responds correctly
2. **Customize labels** - Edit training page to add your specific product labels
3. **Adjust detection threshold** - Tune the contour detection in `index.html` (line 110: `area > 1000`)
4. **Add authentication** - Secure the API calls if needed
5. **Deploy** - Set up production environment with proper SSL certs

---

**All code changes are complete and ready to run!** Just follow the steps above to start the system.
