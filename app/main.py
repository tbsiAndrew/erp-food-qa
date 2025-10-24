
from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import cv2, time

from .detectors.api_detector import APIDetector
from .detectors.yolo_detector import YOLOQualityDetector
from .metrics import compute_metrics
from .rules import RuleEngine
from .storage import S3Client
from .db import DB
from .config import settings
from .integrations.sap_b1 import push_result_to_sap_async
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

app.mount("/static", StaticFiles(directory="app/static"), name="static")
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

class InspectResponse(BaseModel):
    pass_: bool
    grade: str | None
    confidence: float
    reason_codes: list[str]
    metrics: dict
    inference_ms: float
    qa_image_id: int
    qa_result_id: int
    detections: list[dict] = []  # Add detections to response

@app.post("/inspect", response_model=InspectResponse)
async def inspect(background: BackgroundTasks, file: UploadFile, lot_no: str | None = Form(None), item_code: str | None = Form(None), line_id: str | None = Form(None), save_image: bool = Form(False)):
    raw = await file.read()
    bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        return JSONResponse(status_code=400, content={"detail": "Invalid image"})

    t0 = time.perf_counter()
    dets = _detector.predict(bgr)
    inf_ms = (time.perf_counter() - t0) * 1000

    metrics = compute_metrics(bgr)
    decision = _rules.apply(dets=dets, metrics=metrics)

    # Only save image if save_image is True
    if save_image:
        s3_key = _s3.put_image(bgr, prefix=f"{item_code or 'NA'}/{lot_no or 'NA'}/")
        s3_uri = _s3.uri_for(s3_key)
    else:
        s3_key = None
        s3_uri = None

    with _db as db:
        qa_image_id = db.insert_qa_image(camera_id=settings.CAMERA_ID, lot_no=lot_no, item_code=item_code, line_id=line_id, s3_uri=s3_uri, width=bgr.shape[1], height=bgr.shape[0], exposure_ms=None, meta={"filename": file.filename, "saved": save_image})
        qa_result_id = db.insert_qa_result(qa_image_id=qa_image_id, model_name=_detector.model_name, model_version=_detector.model_version, inference_ms=inf_ms, passed=decision["pass"], grade=decision.get("grade"), confidence=decision.get("confidence", 0.0), reason_codes=decision.get("reason_codes", []), metrics=metrics)
        
        # Only create ERP event if image was saved
        if save_image:
            db.insert_erp_event_pending(qa_result_id, target="SAPB1.ServiceLayer")

    # Only push to SAP if image was saved
    if save_image:
        background.add_task(push_result_to_sap_async, qa_result_id)

    return InspectResponse(
        pass_=decision["pass"], 
        grade=decision.get("grade"), 
        confidence=float(decision.get("confidence", 0.0)), 
        reason_codes=list(decision.get("reason_codes", [])), 
        metrics=metrics, 
        inference_ms=inf_ms, 
        qa_image_id=qa_image_id, 
        qa_result_id=qa_result_id,
        detections=dets  # Include raw detections
    )

@app.post("/train")
async def train_model(file: UploadFile, label: str = Form(...), quality_grade: str = Form(...), item_code: str | None = Form(None)):
    """
    Upload training images to fine-tune the quality inspection model.
    
    Args:
        file: Image file for training
        label: Classification label (e.g., 'good', 'bad', 'defect')
        quality_grade: Quality grade (e.g., 'A', 'B', 'C', 'reject')
        item_code: Optional item/product code
    """
    raw = await file.read()
    bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        return JSONResponse(status_code=400, content={"detail": "Invalid image"})
    
    # Store training image in S3
    s3_key = _s3.put_image(bgr, prefix=f"training/{item_code or 'general'}/{label}/")
    
    # Save training data to database
    with _db as db:
        training_id = db.insert_training_data(
            s3_uri=_s3.uri_for(s3_key),
            label=label,
            quality_grade=quality_grade,
            item_code=item_code,
            width=bgr.shape[1],
            height=bgr.shape[0],
            meta={"filename": file.filename}
        )
    
    # Send training data to external API
    try:
        _, buffer = cv2.imencode('.jpg', bgr)
        import base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        payload = {
            "image": img_base64,
            "label": label,
            "quality_grade": quality_grade,
            "item_code": item_code or "general",
            "format": "base64"
        }
        
        import requests
        response = requests.post(
            f"{settings.API_ENDPOINT.rstrip('/')}/train",
            json=payload,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            api_result = response.json()
            return JSONResponse(content={
                "status": "success",
                "training_id": training_id,
                "s3_uri": _s3.uri_for(s3_key),
                "api_response": api_result
            })
        else:
            return JSONResponse(content={
                "status": "partial_success",
                "training_id": training_id,
                "s3_uri": _s3.uri_for(s3_key),
                "message": "Stored locally but API training failed"
            })
    
    except Exception as e:
        return JSONResponse(content={
            "status": "partial_success",
            "training_id": training_id,
            "s3_uri": _s3.uri_for(s3_key),
            "message": f"Stored locally but API error: {str(e)}"
        })
