from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import psycopg2, psycopg2.extras
import re
import boto3, os
from .config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

s3 = boto3.client(
    "s3",
    endpoint_url=getattr(settings, "S3_ENDPOINT", os.getenv("S3_ENDPOINT", "http://localhost:9000")),
    aws_access_key_id=getattr(settings, "S3_ACCESS_KEY", os.getenv("S3_ACCESS_KEY", "minioadmin")),
    aws_secret_access_key=getattr(settings, "S3_SECRET_KEY", os.getenv("S3_SECRET_KEY", "minioadmin")),
    region_name=getattr(settings, "S3_REGION", os.getenv("S3_REGION", "us-east-1")),
)
BUCKET = getattr(settings, "S3_BUCKET", os.getenv("S3_BUCKET", "qa-images"))

def _s3_to_key(s3_uri: str | None) -> str | None:
    if not s3_uri:
        return None
    m = re.match(r"^s3://([^/]+)/(.+)$", s3_uri)
    if not m:
        return None
    bucket, key = m.group(1), m.group(2)
    return key

def _presign(s3_uri: str | None, expires=3600) -> str | None:
    key = _s3_to_key(s3_uri)
    if not key:
        return None
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=expires,
        )
    except Exception:
        return None

def _fetch_recent(limit=50):
    conn = psycopg2.connect(settings.DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''
                SELECT qr.id as qa_result_id, qr.pass as pass, qr.grade, qr.confidence, qr.reason_codes,
                       qr.inference_ms, qr.metrics, qr.model_name, qr.model_version, qr.qa_image_id,
                       qi.capture_ts, qi.item_code, qi.lot_no, qi.s3_uri, qi.width_px, qi.height_px
                FROM qa_result qr
                JOIN qa_image qi ON qi.id = qr.qa_image_id
                ORDER BY qi.capture_ts DESC
                LIMIT %s
                ''', (limit,)
            )
            rows = cur.fetchall()
            for r in rows:
                r["image_url"] = _presign(r.get("s3_uri"))
            return rows
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