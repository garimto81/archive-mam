"""
환경 변수 설정 관리
Pydantic Settings를 사용하여 타입 안전성 보장
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Application
    app_name: str = "poker-archive-rag-poc"
    app_version: str = "1.3.0"
    environment: Literal["development", "production"] = "development"
    debug: bool = True

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # GCP Configuration
    gcp_project: str
    gcp_region: str = "us-central1"
    gcp_location: str = "us-central1"
    google_application_credentials: str = ""

    # Cloud Storage
    gcs_bucket_ati_metadata: str
    gcs_bucket_proxy_videos: str
    gcs_bucket_clips: str

    # BigQuery
    bq_dataset: str = "poker_archive_dev"
    bq_table_hand_summary: str = "hand_summary"
    bq_table_video_files: str = "video_files"
    bq_table_validation: str = "validation_results"

    # Vertex AI Vector Search
    vertex_index_id: str
    vertex_index_endpoint_id: str
    vertex_embedding_model: str = "text-embedding-004"
    vertex_embedding_dimension: int = 768
    vertex_ai_index_endpoint: str = ""
    vertex_ai_deployed_index_id: str = ""

    # Search Configuration
    search_type: Literal["hybrid", "vector"] = "hybrid"
    search_top_k: int = 5
    search_similarity_threshold: float = 0.7

    # Pub/Sub
    pubsub_topic_new_metadata: str = "poker-metadata-new"
    pubsub_subscription_etl: str = "poker-etl-worker"

    # LLM Configuration (Qwen3-8B)
    llm_provider: Literal["ollama", "huggingface"] = "ollama"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen3:8b"
    llm_timeout: int = 30
    llm_temperature: float = 0.3
    llm_max_tokens: int = 600
    llm_thinking_mode: bool = True

    # RAG Parameters
    rag_context_hands: int = 5
    rag_prompt_template: Literal["korean", "english"] = "korean"

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    enable_structured_logging: bool = True
    log_file_path: str = "logs/app.log"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080,http://localhost:5173"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: str = "*"

    # Feature Flags
    enable_mock_mode: bool = False  # true: mock_data/ 사용
    enable_vision_api: bool = False
    enable_cache: bool = False
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600

    # Development Tools
    reload: bool = True
    openapi_url: str = "/api/docs"
    redoc_url: str = "/api/redoc"

    # Cost Monitoring
    cost_alert_threshold: float = 130.0
    cost_tracking_enabled: bool = True

    # Testing
    test_data_path: str = "mock_data/synthetic_ati"
    test_query_file: str = "test_queries.md"

    class Config:
        env_file = ".env.poc"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_cors_origins(self) -> list[str]:
        """CORS origins를 리스트로 반환"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def get_bq_table_full_name(self, table_name: str) -> str:
        """BigQuery 테이블 전체 이름 반환"""
        return f"{self.gcp_project}.{self.bq_dataset}.{table_name}"

    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment == "production"


# Singleton 인스턴스
settings = Settings()
