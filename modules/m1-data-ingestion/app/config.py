"""
Configuration for M1 Data Ingestion Service
"""
import os
from typing import Optional


class Config:
    """Application configuration"""

    # GCP Project settings
    PROJECT_ID: str = os.getenv("PROJECT_ID", "gg-poker")
    DATASET: str = os.getenv("DATASET", "prod")
    TABLE: str = os.getenv("TABLE", "hand_summary")
    REGION: str = os.getenv("REGION", "us-central1")

    # GCS settings
    TEMP_LOCATION: str = f"gs://{PROJECT_ID}-dataflow-temp/temp"
    STAGING_LOCATION: str = f"gs://{PROJECT_ID}-dataflow-temp/staging"

    # Flask settings
    PORT: int = int(os.getenv("PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    TESTING: bool = False

    # Dataflow settings
    DATAFLOW_RUNNER: str = os.getenv("DATAFLOW_RUNNER", "DataflowRunner")
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "10"))

    # API settings
    API_VERSION: str = "v1"
    SERVICE_NAME: str = "M1 Data Ingestion Service"

    @classmethod
    def get_bigquery_table_path(cls) -> str:
        """Get full BigQuery table path"""
        return f"{cls.PROJECT_ID}:{cls.DATASET}.{cls.TABLE}"

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = [cls.PROJECT_ID, cls.DATASET, cls.TABLE, cls.REGION]
        return all(required)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATAFLOW_RUNNER = "DirectRunner"  # Local runner for testing


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DATAFLOW_RUNNER = "DataflowRunner"


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATAFLOW_RUNNER = "DirectRunner"
    PROJECT_ID = "test-project"
    DATASET = "test_dataset"
    TABLE = "test_table"


# Configuration mapping
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(env: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")

    return config_map.get(env, DevelopmentConfig)
