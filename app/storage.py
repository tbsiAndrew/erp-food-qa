
import uuid
import cv2
from pathlib import Path
from .config import settings

class LocalStorageClient:
    """Local filesystem storage - replaces MinIO/S3 for running without Docker"""
    def __init__(self):
        self.storage_dir = Path(settings.LOCAL_STORAGE_PATH)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def put_image(self, bgr, prefix: str = "") -> str:
        """Save image to local filesystem and return relative path as key"""
        key = f"{prefix}{uuid.uuid4().hex}.jpg"
        file_path = self.storage_dir / key
        
        # Create subdirectories if prefix contains paths
        file_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"📁 Saving image to: {file_path}")
        
        ok = cv2.imwrite(str(file_path), bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ok:
            raise RuntimeError(f"Failed to encode image to {file_path}")
        
        print(f"✅ Image saved successfully: {file_path} (size: {file_path.stat().st_size} bytes)")
        return key

    def uri_for(self, key: str) -> str:
        """Return local file URI"""
        full_path = self.storage_dir / key
        return f"file://{full_path.absolute()}"

# Alias for backwards compatibility
S3Client = LocalStorageClient
