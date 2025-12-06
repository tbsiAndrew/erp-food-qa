
from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import cv2, time
from pathlib import Path
import base64
import json
import requests

from .detectors.api_detector import APIDetector
from .detectors.yolo_detector import YOLOQualityDetector
import glob
from .metrics import compute_metrics
from .rules import RuleEngine
from .storage import S3Client
from .db import DB
from .config import settings
from .models import InspectResponse
# SAP integration disabled for local non-Docker setup
# from .integrations.sap_b1 import push_result_to_sap_async
from .integrations.lark import send_lark_notification_async, LarkBaseClient
from .integrations.onedrive import get_onedrive_uploader
from .dashboard import router as dashboard_router
from datetime import datetime

app = FastAPI(title="ERP Food QA")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount storage directory for serving saved images (create if doesn't exist)
storage_path = Path("storage")
storage_path.mkdir(exist_ok=True)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

app.include_router(dashboard_router)

_rules = RuleEngine(settings.RULES_PATH)
_s3 = S3Client()
_db = DB()

def get_model_path(model_version):
    # Find the best.pt for the given model version
    model_dir = Path(f"runs/detect/{model_version}/weights")
    model_path = model_dir / "best.pt"
    if model_path.exists():
        return str(model_path)
    # fallback to base model
    return str(Path("models/yolov8n.pt"))

def get_next_model_version():
    # Find all bread_qa* folders and increment
    detect_dir = Path("runs/detect")
    versions = [d.name for d in detect_dir.iterdir() if d.is_dir() and d.name.startswith("bread_qa") and d.name.replace("bread_qa","").isdigit()]
    nums = [int(v.replace("bread_qa", "")) for v in versions]
    next_num = max(nums) + 1 if nums else 2
    return f"bread_qa{next_num}"


@app.post("/inspect", response_model=InspectResponse)
async def inspect(
    background: BackgroundTasks,
    file: UploadFile,
    lot_no: str | None = Form(None),
    item_code: str | None = Form(None),
    line_id: str | None = Form(None),
    camera_name: str | None = Form(None),
    model_version: str | None = Form("bread_qa")
):
    raw = await file.read()
    bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        return JSONResponse(status_code=400, content={"detail": "Invalid image"})

    # Dynamically load model
    model_path = get_model_path(model_version)
    detector = YOLOQualityDetector(model_path)

    t0 = time.perf_counter()
    dets = detector.predict(bgr)
    inf_ms = (time.perf_counter() - t0) * 1000

    metrics = compute_metrics(bgr)
    decision = _rules.apply(dets=dets, metrics=metrics)

    annotated_image = bgr.copy()
    annotated_image = detector.draw_detections(annotated_image, dets)
    import base64
    _, buffer = cv2.imencode('.jpg', annotated_image)
    annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')

    with _db as db:
        qa_image_id = db.insert_qa_image(camera_id=camera_name or settings.CAMERA_ID, lot_no=lot_no, item_code=item_code, line_id=line_id, s3_uri=None, width=bgr.shape[1], height=bgr.shape[0], exposure_ms=None, meta={"filename": file.filename})
        qa_result_id = db.insert_qa_result(qa_image_id=qa_image_id, model_name=detector.model_name, model_version=model_version, inference_ms=inf_ms, passed=decision["pass"], grade=decision.get("grade"), confidence=decision.get("confidence", 0.0), reason_codes=decision.get("reason_codes", []), metrics=metrics)

    now = datetime.now()
    if settings.LARK_ENABLED and settings.LARK_WEBHOOK_URL:
        lark_data = {
            "pass_": decision["pass"],
            "camera_name": camera_name or settings.CAMERA_ID,
            "date": now.strftime('%Y-%m-%d'),
            "time": now.strftime('%H:%M:%S'),
            "grade": decision.get("grade"),
            "confidence": decision.get("confidence", 0.0),
            "good_confidence": decision.get("good_confidence", 0.0),
            "bad_confidence": decision.get("bad_confidence", 0.0),
            "reason_codes": decision.get("reason_codes", []),
            "detections": dets,
            "item_code": item_code or "N/A",
            "lot_no": lot_no or "N/A",
            "qa_result_id": str(qa_result_id),
            "inference_ms": inf_ms,
        }
        background.add_task(
            send_lark_notification_async,
            lark_data,
            settings.LARK_WEBHOOK_URL,
            annotated_image,
            settings.LARK_APP_ID,
            settings.LARK_APP_SECRET,
            settings.LARK_DRIVE_FOLDER_TOKEN
        )

    return InspectResponse(
        pass_=decision["pass"], 
        camera_name=camera_name or settings.CAMERA_ID,
        date=now.strftime('%Y-%m-%d'),
        time=now.strftime('%H:%M:%S'),
        grade=decision.get("grade"), 
        confidence=float(decision.get("confidence", 0.0)),
        good_confidence=float(decision.get("good_confidence", 0.0)),
        bad_confidence=float(decision.get("bad_confidence", 0.0)),
        good_count=decision.get("good_count", 0),
        bad_count=decision.get("bad_count", 0),
        reason_codes=list(decision.get("reason_codes", [])), 
        metrics=metrics, 
        inference_ms=inf_ms, 
        qa_image_id=qa_image_id, 
        qa_result_id=qa_result_id,
        detections=dets,
        annotated_image=annotated_image_base64,
    )

@app.post("/train")
async def train_model(
    file: UploadFile, 
    label: str = Form(...), 
    item_code: str | None = Form(None),
    auto_retrain: bool = Form(False),
    min_images_before_retrain: int = Form(10),
    model_version: str | None = Form("bread_qa")
):
    """
    Upload training images to fine-tune the quality inspection model.
    
    Args:
        file: Image file for training
        label: Classification label (e.g., 'good', 'bad', 'defect')
        item_code: Optional item/product code
        auto_retrain: If True, automatically trigger incremental training when enough images accumulated
        min_images_before_retrain: Minimum new images before triggering auto-retrain (default: 10)
    """
    import os
    from pathlib import Path
    import uuid
    
    raw = await file.read()
    bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        return JSONResponse(status_code=400, content={"detail": "Invalid image"})
    
    # Store training image in S3
    s3_key = _s3.put_image(bgr, prefix=f"training/{item_code or 'general'}/{label}/")
    
    # Save training data to database (quality_grade now optional/null)
    with _db as db:
        training_id = db.insert_training_data(
            s3_uri=_s3.uri_for(s3_key),
            label=label,
            quality_grade=None,  # No longer required
            item_code=item_code,
            width=bgr.shape[1],
            height=bgr.shape[0],
            meta={"filename": file.filename}
        )
    
    # Save image locally for YOLO training in dataset/bread_qa_auto_labeled structure
    try:
        dataset_base = Path("dataset/bread_qa_auto_labeled")
        
        # Map label to 'good' or 'bad' (YOLO class names)
        yolo_label = "bad" if label.lower() in ["bad", "defect", "contaminated", "discolored", "damaged", "reject"] else "good"
        class_id = 1 if yolo_label == "bad" else 0
        
        # Use 'good' or 'bad' subdirectory in labels and images (staging area)
        label_dir = dataset_base / "labels" / yolo_label
        image_dir = dataset_base / "images" / yolo_label
        
        # Create directories if they don't exist
        label_dir.mkdir(parents=True, exist_ok=True)
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        unique_id = str(uuid.uuid4().hex)
        image_path = image_dir / f"{unique_id}.jpg"
        label_path = label_dir / f"{unique_id}.txt"
        
        # Save image
        cv2.imwrite(str(image_path), bgr)
        
        # Create YOLO label file (full image bounding box)
        # Format: class_id center_x center_y width height (normalized 0-1)
        with open(label_path, 'w') as f:
            f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
        
        # Check if we should trigger auto-retrain
        retrain_triggered = False
        if auto_retrain:
            # Count pending images in good/bad folders
            good_images = list((dataset_base / "images" / "good").glob("*.jpg"))
            bad_images = list((dataset_base / "images" / "bad").glob("*.jpg"))
            pending_count = len(good_images) + len(bad_images)
            
            if pending_count >= min_images_before_retrain:
                # Trigger incremental training in background with new version
                import subprocess
                try:
                    next_version = get_next_model_version()
                    subprocess.Popen([
                        "python", "app/incremental_train.py", 
                        "--epochs", "10",
                        "--batch", "8",
                        "--model_version", next_version
                    ])
                    retrain_triggered = True
                    response_data = {"new_model_version": next_version}
                except Exception as e:
                    print(f"⚠️ Failed to trigger auto-retrain: {e}")
        
        response_data = {
            "status": "success",
            "training_id": training_id,
            "s3_uri": _s3.uri_for(s3_key),
            "local_image": str(image_path),
            "local_label": str(label_path),
            "yolo_class": yolo_label,
            "message": "Image saved to local dataset."
        }
        
        if retrain_triggered:
            response_data["retrain_triggered"] = True
            response_data["message"] += " Incremental training started in background."
        elif auto_retrain:
            good_images = list((dataset_base / "images" / "good").glob("*.jpg"))
            bad_images = list((dataset_base / "images" / "bad").glob("*.jpg"))
            pending_count = len(good_images) + len(bad_images)
            response_data["pending_images"] = pending_count
            response_data["message"] += f" {pending_count}/{min_images_before_retrain} images collected. Will auto-train at {min_images_before_retrain}."
        else:
            response_data["message"] += " Run 'python incremental_train.py' to update the model."
        
        return JSONResponse(content=response_data)
    
    except Exception as e:
        # Even if local save fails, we still have S3 backup
        return JSONResponse(content={
            "status": "partial_success",
            "training_id": training_id,
            "s3_uri": _s3.uri_for(s3_key),
            "message": f"Saved to S3 but local save failed: {str(e)}"
        })


@app.get("/training_items")
async def get_training_items():
    """
    Fetch training items from Lark Base with 'Train to Model' = 'Yes'
    
    Returns:
        {
            "yes": [list of items marked 'Yes']
        }
    """
    try:
        lark_client = LarkBaseClient()
        
        # Fetch only 'Yes' records
        yes_items = lark_client.get_training_records(status="Yes", limit=50)
        
        # Format response with essential fields
        formatted_items = []
        for item in yes_items:
            fields = item.get('fields', {})
            record_id = item.get('record_id')
            formatted_items.append({
                'record_id': record_id,
                'qa_tagging': fields.get('QA Tagging'),
                'train_to_model': fields.get('Train to Model'),
                'train_label': fields.get('Train Label'),
                'qa_decision': fields.get('QA Decision'),
                'item_code': fields.get('Item Code'),
                'attachment': fields.get('Attachment'),  # Image attachment field
                'has_attachment': len(fields.get('Attachment', [])) > 0
            })
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "yes": formatted_items
            },
            "count": len(formatted_items)
        })
        
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": f"Failed to fetch training items: {str(e)}"
        })


@app.get("/training_image/{record_id}")
async def get_training_image(record_id: str):
    """
    Download image from Lark Base record by record_id
    
    Args:
        record_id: Lark Base record ID
        
    Returns:
        Image as base64 encoded string
    """
    try:
        lark_client = LarkBaseClient()
        token = lark_client._get_tenant_access_token()
        
        if not token:
            print(f"❌ Failed to get Lark token for {record_id}")
            return JSONResponse(status_code=500, content={
                "status": "error",
                "error": "Failed to authenticate with Lark"
            })
        
        # Fetch the specific record
        url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{lark_client.base_id}/tables/{lark_client.table_id}/records/{record_id}"
        headers = {'Authorization': f'Bearer {token}'}
        
        print(f"🔍 Fetching record: {record_id}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return JSONResponse(status_code=500, content={
                "status": "error",
                "error": f"Failed to fetch record: HTTP {response.status_code}"
            })
        
        data = response.json()
        if data.get('code') != 0:
            print(f"❌ Lark API error: {data}")
            return JSONResponse(status_code=500, content={
                "status": "error",
                "error": "Invalid response from Lark"
            })
        
        fields = data.get('data', {}).get('record', {}).get('fields', {})
        
        # Try different possible field names for attachments
        attachment_field = (
            fields.get('Attachment') or 
            fields.get('attachment') or
            fields.get('Image') or
            fields.get('image') or
            fields.get('Images') or
            []
        )
        
        print(f"📋 Available fields: {list(fields.keys())}")
        print(f"📎 Attachment field: {attachment_field[:200] if attachment_field else 'None'}")
        
        if not attachment_field or len(attachment_field) == 0:
            print(f"❌ No attachment found for {record_id}")
            print(f"   Available fields in record: {list(fields.keys())}")
            print(f"   Please check which field contains images in your Lark Base")
            return JSONResponse(status_code=404, content={
                "status": "error",
                "error": "No image attachment found",
                "available_fields": list(fields.keys())
            })
        
        # Download image
        print(f"📥 Downloading image for {record_id}")
        img = lark_client.download_image_from_attachment(attachment_field)
        
        if img is None:
            print(f"❌ Failed to download image for {record_id}")
            return JSONResponse(status_code=404, content={
                "status": "error",
                "error": "Image download failed"
            })
        
        # Encode as base64
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        print(f"✅ Image fetched successfully for {record_id}")
        return JSONResponse(content={
            "status": "success",
            "image": img_base64,
            "record_id": record_id
        })
        
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": f"Failed to download image: {str(e)}"
        })


class TrainingRequest(BaseModel):
    selected_records: list  # List of {record_id, label, bounding_box}
    model_version: str = "bread_qa"


@app.post("/start_training")
async def start_training(request: TrainingRequest, background: BackgroundTasks):
    """
    Start incremental training with selected images from Lark Base
    Saves labels to 'Train Label' field and updates 'Train to Model' to 'Trained'
    
    Args:
        selected_records: List of records with labels and bounding boxes
        model_version: Model version to train
        
    Returns:
        Training progress updates
    """
    try:
        from .incremental_train import incremental_train
        import uuid
        from datetime import datetime
        
        lark_client = LarkBaseClient()
        
        # Create temporary training folder with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_training_folder = Path(f"dataset/fine_tuning_{timestamp}")
        
        # Create folder structure
        temp_images_dir = temp_training_folder / "images" / "train"
        temp_labels_dir = temp_training_folder / "labels" / "train"
        temp_images_dir.mkdir(parents=True, exist_ok=True)
        temp_labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Process selected records
        training_data = []
        
        for record_data in request.selected_records:
            record_id = record_data.get('record_id')
            label = record_data.get('label')  # 'good' or 'bad'
            bbox = record_data.get('bounding_box')  # {x, y, width, height} normalized
            yolo_label_str = record_data.get('yolo_label', '')  # YOLO format: "class_id x y w h"
            
            # Download image
            token = lark_client._get_tenant_access_token()
            url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{lark_client.base_id}/tables/{lark_client.table_id}/records/{record_id}"
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"⚠️ Failed to fetch record {record_id}")
                continue
                
            data = response.json()
            fields = data.get('data', {}).get('record', {}).get('fields', {})
            
            # Try multiple possible attachment field names
            attachment_field = None
            for field_name in ['Attachment', 'attachment', 'Image', 'image', 'Images', 'images', 'Photo', 'photo', 'File', 'file', '附件', '图片']:
                if field_name in fields and fields[field_name]:
                    attachment_field = fields[field_name]
                    print(f"📎 Found attachment in field: {field_name}")
                    break
            
            if not attachment_field:
                print(f"⚠️ No attachment found in record {record_id}")
                print(f"   Available fields: {list(fields.keys())}")
                continue
            
            # Check if there's an existing Train Label in Lark Base
            existing_train_label = fields.get('Train Label', '')
            
            img = lark_client.download_image_from_attachment(attachment_field)
            if img is None:
                print(f"⚠️ Failed to download image for {record_id}")
                continue
            
            # Map label to YOLO class name
            class_name = "bad" if label.lower() in ["bad", "defect"] else "good"
            class_id = 1 if class_name == "bad" else 0
            
            # Generate unique filename using record_id for traceability
            image_filename = f"{record_id}.jpg"
            label_filename = f"{record_id}.txt"
            
            image_path = temp_images_dir / image_filename
            label_path = temp_labels_dir / label_filename
            
            # Save image
            cv2.imwrite(str(image_path), img)
            print(f"💾 Saved image: {image_path}")
            
            # Save YOLO label - Priority: yolo_label_str > existing_train_label > bbox > default
            if yolo_label_str:
                # Use the YOLO format label directly from frontend (newly drawn)
                label_line = yolo_label_str
                print(f"📝 Using frontend YOLO label: {label_line}")
            elif existing_train_label and existing_train_label.strip():
                # Use existing Train Label from Lark Base (previously saved)
                label_line = existing_train_label.strip()
                print(f"📋 Using existing Train Label: {label_line}")
            elif bbox:
                # Construct from bounding box
                center_x = bbox.get('x', 0.5)
                center_y = bbox.get('y', 0.5)
                width = bbox.get('width', 1.0)
                height = bbox.get('height', 1.0)
                label_line = f"{class_id} {center_x} {center_y} {width} {height}"
                print(f"📐 Using bbox: {label_line}")
            else:
                # Full image bounding box
                label_line = f"{class_id} 0.5 0.5 1.0 1.0"
                print(f"📦 Using full image bbox: {label_line}")
            
            # Write label file
            with open(label_path, 'w') as f:
                f.write(f"{label_line}\n")
            print(f"💾 Saved label: {label_path}")
            
            # Update 'Train Label' field in Lark Base with YOLO format (only if new label was drawn)
            if yolo_label_str:
                lark_client.update_record_field(record_id, "Train Label", label_line)
                print(f"💾 Saved Train Label to Lark Base: {label_line}")
            
            training_data.append({
                'record_id': record_id,
                'label': class_name,
                'class_id': class_id,
                'image_path': str(image_path),
                'label_path': str(label_path),
                'bbox': bbox
            })
        
        if len(training_data) == 0:
            return JSONResponse(status_code=400, content={
                "status": "error",
                "message": "No valid training data. Could not download images from Lark Base."
            })
        
        # Create data.yaml for YOLO training
        data_yaml_path = temp_training_folder / "data.yaml"
        with open(data_yaml_path, 'w') as f:
            f.write(f"""# Training configuration
path: {temp_training_folder.absolute()}
train: images/train
val: images/train  # Using same for validation (small dataset)

# Classes
names:
  0: good
  1: bad
""")
        
        # Start training in background
        def train_and_update():
            try:
                # Run incremental training with the temp folder
                next_version = get_next_model_version()
                print(f"🚀 Starting training with dataset folder: {temp_training_folder}")
                
                results = incremental_train(
                    epochs=10,
                    batch=8,
                    patience=5,
                    model_version=next_version,
                    dataset_folder=str(temp_training_folder)  # Pass the temp folder path
                )
                
                if results:
                    print(f"✅ Training completed successfully: {next_version}")
                    print(f"📝 Updating Lark Base records to 'Trained'...")
                    
                    # Update all trained records to 'Trained'
                    for item in training_data:
                        success = lark_client.update_record_field(
                            item['record_id'],
                            "Train to Model",
                            "Trained"
                        )
                        if success:
                            print(f"✅ Updated {item['record_id']} to 'Trained'")
                        else:
                            print(f"⚠️ Failed to update {item['record_id']}")
                    
                    print(f"✅ All records updated in Lark Base")
                    print(f"✅ Training data saved in: {temp_training_folder}")
                else:
                    print("❌ Training failed - no results returned")
                    
            except Exception as e:
                print(f"❌ Training error: {e}")
                import traceback
                traceback.print_exc()
        
        background.add_task(train_and_update)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Training started with {len(training_data)} images",
            "training_folder": str(temp_training_folder),
            "training_data": training_data
        })
        
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": f"Failed to start training: {str(e)}"
        })
