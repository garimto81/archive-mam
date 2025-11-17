"""
Configuration for M2 Video Metadata Service
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Service configuration"""

    # GCP Settings
    PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "gg-poker")
    BIGQUERY_DATASET: str = os.getenv("BIGQUERY_DATASET", "prod")
    BIGQUERY_TABLE: str = os.getenv("BIGQUERY_TABLE", "video_files")
    GCS_BUCKET: str = os.getenv("GCS_BUCKET", "gg-poker-proxy")

    # NAS Settings
    NAS_BASE_PATH: str = os.getenv("NAS_BASE_PATH", "/nas/poker/")

    # FFmpeg Settings
    FFMPEG_TIMEOUT: int = int(os.getenv("FFMPEG_TIMEOUT", "600"))  # 10 minutes
    PROXY_RESOLUTION: str = os.getenv("PROXY_RESOLUTION", "720p")
    PROXY_PRESET: str = os.getenv("PROXY_PRESET", "fast")
    PROXY_CRF: int = int(os.getenv("PROXY_CRF", "23"))

    # Service Settings
    PORT: int = int(os.getenv("PORT", "8002"))
    WORKERS: int = int(os.getenv("WORKERS", "2"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Scan Settings
    SUPPORTED_EXTENSIONS: list = [".mp4", ".mov", ".avi"]
    MAX_CONCURRENT_SCANS: int = int(os.getenv("MAX_CONCURRENT_SCANS", "3"))

    @property
    def bigquery_table_id(self) -> str:
        """Full BigQuery table ID"""
        return f"{self.PROJECT_ID}.{self.BIGQUERY_DATASET}.{self.BIGQUERY_TABLE}"


# Global config instance
config = Config()
