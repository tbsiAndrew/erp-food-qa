# SMARTBITES - ERP BREAD QUALITY DETECTOR

# Bread Quality Inspection Platform

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**SMARTBITES** is an AI-powered quality inspection system for detecting and grading bread quality in real-time using computer vision and deep learning. This solution integrates with enterprise systems to automate quality assurance workflows in food production environments.

## 🎯 Solution Overview

This system provides automated bread quality inspection through multiple detection approaches:

### **Approach 1: API-Based Detection (Production)**
- Utilizes an external quality inspection API endpoint for predictions
- Sends captured images to a centralized AI service for analysis
- Returns quality grades (good/bad) with confidence scores
- Supports distributed deployment across multiple inspection stations

### **Approach 2: Local YOLO Detection (Training & Offline)**
- Uses YOLOv8 object detection model trained specifically for bread quality
- Performs on-device inference for edge computing scenarios
- Enables offline operation when API connectivity is unavailable
- Supports incremental model training with new inspection data

### **Core Features**
- ✅ Real-time camera feed quality inspection
- ✅ Automated quality grading (good/bad/defect detection)
- ✅ Rule-based decision engine for pass/fail criteria
- ✅ Training data collection and model fine-tuning
- ✅ Local storage and database persistence
- ✅ Web-based dashboard for monitoring and analytics

## 🏗️ System Architecture

```
┌─────────────────┐
│  Camera Feed    │
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│     Flask Web Interface         │
│  (Image Capture & Display)      │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│    FastAPI Backend Server       │
│  ┌──────────────────────────┐  │
│  │  Detection Engine        │  │
│  │  • API Detector          │  │
│  │  • YOLO Detector         │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  Rule Engine             │  │
│  │  (Quality Criteria)      │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  Storage & Database      │  │
│  │  • SQLite/PostgreSQL     │  │
│  │  • Local File Storage    │  │
│  └──────────────────────────┘  │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│   Integration Layer             │
│  • SAP Business One             │
│  • Lark (Feishu) Notifications  │
│  • OneDrive File Upload         │
└─────────────────────────────────┘
```

## 🛠️ Technology Stack

### **Backend Framework**
- **FastAPI** - High-performance async API server
- **Flask** - Web interface and camera streaming
- **Python 3.8+** - Core application language

### **Computer Vision & AI**
- **YOLOv8 (Ultralytics)** - Object detection and quality classification
- **OpenCV** - Image processing and camera capture
- **ONNX Runtime** - Model inference optimization
- **NumPy** - Numerical computing for image arrays
- **PyTorch** - Deep learning framework for model training

### **Data Management**
- **SQLite** - Local database for development
- **PostgreSQL** - Production database (optional)
- **Pydantic** - Data validation and settings management
- **PyYAML** - Configuration file handling

### **Frontend**
- **Jinja2** - HTML templating
- **HTML5/CSS3** - Web interface
- **JavaScript** - Interactive camera controls

### **Integrations**
- **Requests** - HTTP client for API communications
- **Python-multipart** - File upload handling
- **Python-dotenv** - Environment configuration management

## 🔌 Enterprise Integrations

### **1. SAP Business One Integration**
- **Purpose**: Push quality inspection results to ERP system
- **Implementation**: `app/integrations/sap_b1.py`
- **Features**:
  - Automatic login and session management
  - Real-time QA result synchronization
  - Item code, lot number, and grade tracking
  - Image URI reference storage
  - Error handling and retry logic

### **2. Lark (Feishu) Integration**
- **Purpose**: Instant notifications and collaboration
- **Implementation**: `app/integrations/lark.py`
- **Features**:
  - Webhook-based instant notifications
  - Image upload to Lark Drive
  - Bitable (database) integration for structured data
  - Quality alerts with detection images
  - Tenant access token management
  - Configurable notification templates

### **3. OneDrive Integration**
- **Purpose**: Cloud storage for inspection images
- **Implementation**: `app/integrations/onedrive.py`
- **Features**:
  - Automated image upload to OneDrive
  - OAuth 2.0 authentication with token refresh
  - Folder organization by date/batch
  - Token caching for persistent sessions
  - Microsoft Graph API integration
  - Support for personal and business accounts

## 📋 Prerequisites

- Python 3.8 or higher
- Webcam or compatible camera device
- Windows/Linux/macOS operating system
- 4GB+ RAM recommended
- GPU optional (for faster YOLO training)

## 🚀 Getting Started

### **1. Clone the Repository**
```bash
git clone https://github.com/tbsiAndrew/erp-food-qa.git
cd erp-food-qa
```

### **2. Create Virtual Environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Configure Environment**
Create a `.env` file in the project root:
```env
# API Configuration
API_ENDPOINT=https://your-api-endpoint.com/
CAMERA_ID=CAM01

# Storage
LOCAL_STORAGE_PATH=storage/images
DATABASE_PATH=storage/qa_database.db

# Lark Integration (Optional)
LARK_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook
LARK_ENABLED=false
LARK_APP_ID=your_app_id
LARK_APP_SECRET=your_app_secret
LARK_DRIVE_FOLDER_TOKEN=your_folder_token

# OneDrive Integration (Optional)
ONEDRIVE_TENANT_ID=your_tenant_id
ONEDRIVE_CLIENT_ID=your_client_id
ONEDRIVE_CLIENT_SECRET=your_client_secret
ONEDRIVE_FOLDER_PATH=QA_Detection_Results
```

### **5. Run the Application**

#### **Option A: Quick Start (Windows)**
```bash
START_LOCAL.bat
```

#### **Option B: Manual Start**

**Start FastAPI Backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Start Flask Web Interface (in another terminal):**
```bash
python web/app.py
```

### **6. Access the Application**
- **Web Interface**: http://127.0.0.1:5000
- **API Docs**: http://127.0.0.1:8000/docs
- **Training Interface**: http://127.0.0.1:5000/train

## 📸 Usage

### **Quality Inspection**
1. Open the web interface at http://127.0.0.1:5000
2. Select your camera from the dropdown
3. Click "Start Camera" to begin live feed
4. Position bread item in camera view
5. Click "Capture & Inspect" to analyze quality
6. Review results (good/bad classification, confidence score)

### **Model Training**
1. Navigate to http://127.0.0.1:5000/train
2. Capture training images from camera
3. Label each image (good/bad)
4. Submit for incremental model training
5. Training data is stored for future model fine-tuning

### **API Endpoints**
- `POST /inspect` - Analyze uploaded image
- `POST /train` - Submit training data
- `GET /results` - Retrieve inspection history
- `GET /dashboard` - View analytics dashboard

## 📁 Project Structure

```
erp-food-qa/
├── app/                      # FastAPI backend application
│   ├── main.py              # Main API server
│   ├── config.py            # Configuration settings
│   ├── models.py            # Data models
│   ├── db.py                # Database operations
│   ├── storage.py           # File storage handling
│   ├── rules.py             # Rule engine for QA criteria
│   ├── dashboard.py         # Analytics endpoints
│   ├── detectors/           # Detection implementations
│   │   ├── api_detector.py  # External API integration
│   │   ├── yolo_detector.py # YOLO model wrapper
│   │   └── onnx_yolo.py     # ONNX inference engine
│   ├── integrations/        # Enterprise integrations
│   │   ├── sap_b1.py        # SAP Business One
│   │   ├── lark.py          # Lark/Feishu
│   │   └── onedrive.py      # Microsoft OneDrive
│   └── sql/                 # Database migrations
├── web/                     # Flask web interface
│   ├── app.py              # Web server
│   └── templates/           # HTML templates
├── dataset/                 # Training datasets
│   └── bread_qa_auto_labeled/
├── models/                  # Pre-trained models
├── rules/                   # Quality rules configuration
│   └── default.yaml
├── runs/                    # Training run outputs
├── storage/                 # Local file storage
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🎓 Training Your Own Model

### **Collect Training Data**
```bash
# Use web interface at /train to capture and label images
# Or run automated data collection
python app/incremental_train.py
```

### **Start Training**
```bash
# Windows
START_TRAINING.bat

# Linux/Mac
python -m ultralytics train \
  --data dataset/bread_qa_auto_labeled/data.yaml \
  --model yolov8n.pt \
  --epochs 100 \
  --imgsz 640
```

### **Incremental Training**
```bash
# Continue training from existing model
RUN_INCREMENTAL_TRAINING.bat
```

## 🔧 Configuration

### **Quality Rules** (`rules/default.yaml`)
```yaml
pass_criteria:
  min_confidence: 0.7
  allowed_defects: []
  
grade_mapping:
  good: A
  bad: C
  unknown: F
  
notification_threshold: 0.5
```

### **Database Schema**
The system automatically creates tables for:
- `qa_results` - Inspection records
- `training_data` - Labeled images for model improvement
- `erp_events` - Integration event logs

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -m 'Add YourFeature'`)
4. Push to branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Andrew** - *Initial work* - [tbsiAndrew](https://github.com/tbsiAndrew)

## 🙏 Acknowledgments

- Ultralytics for the excellent YOLOv8 framework
- FastAPI for the high-performance API framework
- OpenCV community for computer vision tools
- All contributors and testers

**Built with ❤️ for automated food quality assurance**
