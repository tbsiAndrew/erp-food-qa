
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Detection(BaseModel):
    cls: str
    conf: float
    box: List[float]

class Decision(BaseModel):
    pass_: bool
    grade: Optional[str] = None
    confidence: float = 0.0
    reason_codes: List[str] = []

class InspectResponse(BaseModel):
    pass_: bool
    grade: Optional[str] = None
    confidence: float = 0.0
    good_confidence: float = 0.0
    bad_confidence: float = 0.0
    good_count: int = 0
    bad_count: int = 0
    reason_codes: List[str] = []
    metrics: Dict[str, Any]
    inference_ms: float
    qa_image_id: int
    qa_result_id: int
    detections: List[Dict[str, Any]] = []
