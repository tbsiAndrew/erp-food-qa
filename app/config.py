from pydantic_settings import BaseSettings  # ✅ new import
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    CAMERA_ID: str = "CAM01"
    API_ENDPOINT: str = Field("https://cp-rsl02.sin02.ds.network:2096/")
    RULES_PATH: str = "rules/default.yaml"
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    # S3 variables
    S3_ENDPOINT: str = Field("http://localhost:9000")
    S3_ACCESS_KEY: str = Field("minioadmin")
    S3_SECRET_KEY: str = Field("minioadmin")
    S3_BUCKET: str = Field("qa-images")
    S3_REGION: str = Field("us-east-1")
    # MinIO variables
    MINIO_ENDPOINT: str = Field("http://localhost:9000")
    MINIO_ACCESS_KEY: str = Field("minioadmin")
    MINIO_SECRET_KEY: str = Field("minioadmin")
    MINIO_BUCKET: str = Field("qa-images")
    # SAP
    SAP_BASE_URL: str = Field("http://sap-service-layer:50000/b1s/v1")
    SAP_DB: str = Field("SBODEMO")
    SAP_USER: str = Field("manager")
    SAP_PWD: str = Field("manager")
    class Config:
        env_file = ".env"

settings = Settings()
