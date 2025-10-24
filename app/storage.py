
import io, uuid
import cv2
import boto3
from .config import settings

class S3Client:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        try:
            self.s3.head_bucket(Bucket=settings.S3_BUCKET)
        except Exception:
            self.s3.create_bucket(Bucket=settings.S3_BUCKET)

    def put_image(self, bgr, prefix: str = "") -> str:
        key = f"{prefix}{uuid.uuid4().hex}.jpg"
        ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ok:
            raise RuntimeError("Failed to encode image")
        self.s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=io.BytesIO(buf.tobytes()).getvalue(), ContentType="image/jpeg")
        return key

    def uri_for(self, key: str) -> str:
        return f"s3://{settings.S3_BUCKET}/{key}"
