# ERP Food QA - API-based Quality Inspection

This system has been updated to use an external API endpoint for quality inspection instead of local ONNX models.

## Changes Made

### 1. Replaced ONNX Model with API Integration
- Created `app/detectors/api_detector.py` to handle API-based predictions
- Configured to use: `https://cp-rsl02.sin02.ds.network:2096/`
- Updated `app/main.py` to use `APIDetector` instead of `ONNXDetector`

### 2. Added Training/Fine-tuning Endpoint
- New `/train` endpoint to submit training images
- Stores training data in S3 and database
- Forwards training data to external API for model fine-tuning

### 3. Web Interface for Training
- New training page at `http://127.0.0.1:5000/train`
- Capture images from camera for training
- Specify classification labels and quality grades
- Submit data for model fine-tuning

## Setup Instructions

### 1. Start Docker Services (PostgreSQL + MinIO)
```bash
docker compose up -d
```

### 2. Run Database Migrations
```bash
# Connect to PostgreSQL and run SQL files in order
psql -h localhost -p 5433 -U odoo -d erp_food_qa -f app/sql/0001_init.sql
psql -h localhost -p 5433 -U odoo -d erp_food_qa -f app/sql/0002_indexes.sql
psql -h localhost -p 5433 -U odoo -d erp_food_qa -f app/sql/0003_training_data.sql
```

### 3. Start FastAPI Backend
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Start Flask Web Interface
```bash
# In a new terminal, navigate to web directory
cd web
python app.py
```

### 5. Access the Application
- **Inspection Interface**: http://127.0.0.1:5000/
- **Training Interface**: http://127.0.0.1:5000/train
- **API Documentation**: http://127.0.0.1:8000/docs

## API Endpoints

### Inspection
**POST** `/inspect`
- Upload image for quality inspection
- Returns: pass/fail, confidence, grade, metrics

### Training
**POST** `/train`
- Upload training images with labels
- Parameters:
  - `file`: Image file
  - `label`: Classification (good, bad, defect, etc.)
  - `quality_grade`: Grade (A, B, C, D, reject)
  - `item_code`: Optional product code

## External API Integration

The system expects the external API (`https://cp-rsl02.sin02.ds.network:2096/`) to have:

### Prediction Endpoint
**POST** `/predict`
```json
{
  "image": "base64_encoded_image",
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

### Training Endpoint
**POST** `/train`
```json
{
  "image": "base64_encoded_image",
  "label": "good",
  "quality_grade": "A",
  "item_code": "ITEM001",
  "format": "base64"
}
```

## Configuration

Edit `app/config.py` to change:
- `API_ENDPOINT`: External API URL
- `S3_ENDPOINT`: MinIO/S3 storage
- `DATABASE_URL`: PostgreSQL connection
- Other settings

## Training Workflow

1. Open training page: http://127.0.0.1:5000/train
2. Capture images from camera or upload files
3. Select appropriate label and quality grade
4. Submit to train the model
5. Training data is:
   - Stored in S3 bucket
   - Saved to database
   - Sent to external API for fine-tuning

## Notes

- SSL verification is disabled for the external API (self-signed cert)
- Training images are stored in S3 under `training/{item_code}/{label}/`
- All inspection and training data is logged in the database
- The system gracefully handles API failures with default responses
