from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3
import re
from pathlib import Path
from .config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def _s3_to_key(s3_uri: str | None) -> str | None:
    """Extract key from S3 URI or file:// URI"""
    if not s3_uri:
        return None
    
    # Handle local file:// URIs
    if s3_uri.startswith("file://"):
        return s3_uri.replace("file://", "")
    
    # Handle S3 URIs (for backwards compatibility)
    m = re.match(r"^s3://([^/]+)/(.+)$", s3_uri)
    if not m:
        return None
    bucket, key = m.group(1), m.group(2)
    return key

def _get_image_url(s3_uri: str | None) -> str | None:
    """Convert storage URI to accessible URL"""
    if not s3_uri:
        return None
    
    # For local file storage, convert to relative web path
    if s3_uri.startswith("file://"):
        # Extract relative path from full path
        key = s3_uri.replace("file://", "")
        # Convert to web-accessible path
        # Assuming images are served from /storage/images/
        relative_path = str(Path(key).relative_to(Path(settings.LOCAL_STORAGE_PATH).parent))
        return f"/{relative_path.replace(chr(92), '/')}"  # Replace backslashes with forward slashes
    
    # For S3 URIs (backwards compatibility - would need presigned URL in production)
    return None

def _fetch_recent(limit=50):
    """Fetch recent QA results from SQLite database"""
    db_path = Path(settings.DATABASE_PATH)
    if not db_path.exists():
        return []
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT qr.id as qa_result_id, qr.pass as pass, qr.grade, qr.confidence, qr.reason_codes,
                   qr.inference_ms, qr.metrics, qr.model_name, qr.model_version, qr.qa_image_id,
                   qi.capture_ts, qi.item_code, qi.lot_no, qi.s3_uri, qi.width_px, qi.height_px
            FROM qa_result qr
            JOIN qa_image qi ON qi.id = qr.qa_image_id
            ORDER BY qi.capture_ts DESC
            LIMIT ?
            ''', (limit,)
        )
        rows = cursor.fetchall()
        results = []
        for r in rows:
            row_dict = dict(r)
            row_dict["image_url"] = _get_image_url(row_dict.get("s3_uri"))
            results.append(row_dict)
        return results
    finally:
        conn.close()

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    rows = _fetch_recent(25)
    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})

@router.get("/api/results")
def api_results(limit: int = 50):
    return JSONResponse(_fetch_recent(limit))

@router.get("/health")
def health():
    return {"status": "ok"}