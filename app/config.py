from pydantic_settings import BaseSettings  # ✅ new import
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    CAMERA_ID: str = "CAM01"
    API_ENDPOINT: str = Field("https://cp-rsl02.sin02.ds.network:2096/")
    RULES_PATH: str = "rules/default.yaml"
    
    # Local storage (replaces MinIO/S3 for non-Docker setup)
    LOCAL_STORAGE_PATH: str = Field("storage/images", env="LOCAL_STORAGE_PATH")
    
    # Local SQLite database (replaces PostgreSQL for non-Docker setup)
    DATABASE_PATH: str = Field("storage/qa_database.db", env="DATABASE_PATH")
    
    # Legacy DATABASE_URL for backwards compatibility (not used in local mode)
    DATABASE_URL: str = Field("sqlite:///storage/qa_database.db", env="DATABASE_URL")
    
    # Lark (Feishu) - optional
    LARK_WEBHOOK_URL: str = Field("", env="LARK_WEBHOOK_URL")
    LARK_ENABLED: bool = Field(False, env="LARK_ENABLED")
    LARK_APP_ID: str = Field("", env="LARK_APP_ID")
    LARK_APP_SECRET: str = Field("", env="LARK_APP_SECRET")
    LARK_DRIVE_FOLDER_TOKEN: str = Field("", env="LARK_DRIVE_FOLDER_TOKEN")
    ANYCROSS_CREATE_FILE_URL: str = Field("", env="ANYCROSS_CREATE_FILE_URL")
    LARK_BASE_ID: str = Field("", env="LARK_BASE_ID")
    LARK_TABLE_ID: str = Field("", env="LARK_TABLE_ID")
    LARK_FIELD_ID: str = Field("", env="LARK_FIELD_ID")
    ANYCROSS_ACCESS_TOKEN: str = Field("none", env="ANYCROSS_ACCESS_TOKEN")
    
    class Config:
        env_file = ".env"

settings = Settings()
