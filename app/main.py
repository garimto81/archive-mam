"""
FastAPI 애플리케이션 진입점
v4.0.0 - Vertex AI Vector Search + BigQuery
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import settings
from app.models.schemas import HealthResponse
from app.api import hands, videos, search

# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(
    search.router,
    prefix=f"{settings.API_V1_PREFIX}/search",
    tags=["search"]
)

app.include_router(
    hands.router,
    prefix=f"{settings.API_V1_PREFIX}/hands",
    tags=["hands"]
)

app.include_router(
    videos.router,
    prefix=f"{settings.API_V1_PREFIX}/video",
    tags=["videos"]
)


# Health Check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.utcnow()
    )


# Root
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
