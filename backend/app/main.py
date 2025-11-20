"""
FastAPI 메인 애플리케이션
"""

import os

# IMPORTANT: Set Google Application Credentials BEFORE importing any GCP services
from app.config import settings
if settings.google_application_credentials:
    # Convert to absolute path if relative
    if not os.path.isabs(settings.google_application_credentials):
        # Relative path is from backend/ directory
        credentials_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),  # app/ -> backend/
                settings.google_application_credentials  # config/gcp-service-account.json
            )
        )
    else:
        credentials_path = settings.google_application_credentials

    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    else:
        # Fallback to original value
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

# Now import FastAPI and other services (after credentials are set)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api import search, hands, rag, autocomplete, sync  # Firestore re-enabled with database param

# Structured Logger 설정
logger = structlog.get_logger()

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="포커 아카이브 RAG 검색 시스템 (Vertex AI + Qwen3-8B)",
    docs_url=settings.openapi_url,
    redoc_url=settings.redoc_url,
    debug=settings.debug,
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods.split(","),
    allow_headers=settings.cors_allow_headers.split(",") if settings.cors_allow_headers != "*" else ["*"],
)


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        gcp_project=settings.gcp_project,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행"""
    logger.info("application_shutdown")


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "services": {
                "gcp_project": settings.gcp_project,
                "llm_provider": settings.llm_provider,
                "llm_model": settings.llm_model,
                "mock_mode": settings.enable_mock_mode,
            },
        }
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "포커 아카이브 RAG 검색 시스템",
        "version": settings.app_version,
        "docs": settings.openapi_url,
    }


# API 라우터 등록
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(hands.router, prefix="/api", tags=["Hands"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(autocomplete.router, prefix="/api", tags=["Autocomplete"])
app.include_router(sync.router, tags=["Sync"])  # Firestore sync re-enabled (testing database param fix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
