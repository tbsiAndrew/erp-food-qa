
from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import cv2, time
from pathlib import Path

from .detectors.api_detector import APIDetector
from .detectors.yolo_detector import YOLOQualityDetector
from .metrics import compute_metrics
from .rules import RuleEngine
from .storage import S3Client
from .db import DB
from .config import settings
from .models import InspectResponse
# SAP integration disabled for local non-Docker setup
# from .integrations.sap_b1 import push_result_to_sap_async
from .integrations.lark import send_lark_notification_async
from .integrations.onedrive import get_onedrive_uploader
from .dashboard import router as dashboard_router

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

# Use YOLO detector instead of API detector for trained model
try:
    _detector = YOLOQualityDetector()  # Auto-loads trained model
    print(f"✅ Using YOLOQualityDetector with trained model")
except Exception as e:
    print(f"⚠️ Failed to load YOLO detector, falling back to API detector: {e}")
    _detector = APIDetector(api_endpoint=settings.API_ENDPOINT)

_rules = RuleEngine(settings.RULES_PATH)
_s3 = S3Client()
_db = DB()

@app.post("/inspect", response_model=InspectResponse)
async def inspect(background: BackgroundTasks, file: UploadFile, lot_no: str | None = Form(None), item_code: str | None = Form(None), line_id: str | None = Form(None)):
    raw = await file.read()
    bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        return JSONResponse(status_code=400, content={"detail": "Invalid image"})

    t0 = time.perf_counter()
    dets = _detector.predict(bgr)
    inf_ms = (time.perf_counter() - t0) * 1000

    metrics = compute_metrics(bgr)
    decision = _rules.apply(dets=dets, metrics=metrics)

    # Create annotated image with detection boxes
    annotated_image = bgr.copy()
    annotated_image = _detector.draw_detections(annotated_image, dets)
    print(f"🎨 Created annotated image with {len(dets)} detections")

    # Convert annotated image to base64 for frontend display
    import base64
    _, buffer = cv2.imencode('.jpg', annotated_image)
    annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
    print(f"📸 Encoded annotated image to base64")

    with _db as db:
        qa_image_id = db.insert_qa_image(camera_id=settings.CAMERA_ID, lot_no=lot_no, item_code=item_code, line_id=line_id, s3_uri=None, width=bgr.shape[1], height=bgr.shape[0], exposure_ms=None, meta={"filename": file.filename})
        qa_result_id = db.insert_qa_result(qa_image_id=qa_image_id, model_name=_detector.model_name, model_version=_detector.model_version, inference_ms=inf_ms, passed=decision["pass"], grade=decision.get("grade"), confidence=decision.get("confidence", 0.0), reason_codes=decision.get("reason_codes", []), metrics=metrics)
    
    if settings.LARK_ENABLED and settings.LARK_WEBHOOK_URL:

        lark_data = {
            "pass_": decision["pass"],
            "grade": decision.get("grade"),
            "confidence": decision.get("confidence", 0.0),
            "good_confidence": decision.get("good_confidence", 0.0),
            "bad_confidence": decision.get("bad_confidence", 0.0),
            "reason_codes": decision.get("reason_codes", []),
            "detections": dets,
            "item_code": item_code or "N/A",
            "lot_no": lot_no or "N/A",
            "qa_result_id": str(qa_result_id),
            "inference_ms": inf_ms
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
        detections=dets,  # Include raw detections
        annotated_image=annotated_image_base64  # Include base64 encoded annotated image
    )

@app.post("/train")
async def train_model(
    file: UploadFile, 
    label: str = Form(...), 
    item_code: str | None = Form(None),
    auto_retrain: bool = Form(False),
    min_images_before_retrain: int = Form(10)
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
                # Trigger incremental training in background
                import subprocess
                try:
                    # Run incremental training script
                    subprocess.Popen([
                        "python", "incremental_train.py", 
                        "--epochs", "10",
                        "--batch", "8"
                    ])
                    retrain_triggered = True
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
