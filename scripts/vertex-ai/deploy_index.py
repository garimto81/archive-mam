#!/usr/bin/env python3
"""
Vertex AI Vector Search 인덱스 엔드포인트 배포 스크립트
v4.0.0
"""

import os
import sys
import time
from pathlib import Path
from google.cloud import aiplatform


# 프로젝트 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "gg-poker-prod")
REGION = os.getenv("GCP_REGION", "us-central1")
DEPLOYED_INDEX_ID = "poker_hands_deployed"

# VPC 설정 (선택사항 - Public endpoint 사용 시 주석 처리)
VPC_NETWORK = os.getenv("VPC_NETWORK", None)  # "projects/{PROJECT_NUMBER}/global/networks/{NETWORK_NAME}"


def create_index_endpoint():
    """인덱스 엔드포인트 생성"""

    print(f"\n=== 인덱스 엔드포인트 생성 ===")
    print(f"프로젝트: {PROJECT_ID}")
    print(f"리전: {REGION}")

    # Vertex AI SDK 초기화
    aiplatform.init(
        project=PROJECT_ID,
        location=REGION
    )

    # 엔드포인트 생성 (Public endpoint)
    endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
        display_name="poker-hands-endpoint",
        description="Poker hands vector search endpoint",
        public_endpoint_enabled=True  # Public endpoint (VPC 없이)
    )

    print(f"\n✅ 엔드포인트 생성 완료!")
    print(f"Endpoint ID: {endpoint.name}")
    print(f"Resource Name: {endpoint.resource_name}")

    # 엔드포인트 ID 저장
    endpoint_id_file = Path(__file__).parent / "endpoint_id.txt"
    with open(endpoint_id_file, "w") as f:
        f.write(endpoint.name)

    print(f"Endpoint ID 저장: {endpoint_id_file}")

    return endpoint


def deploy_index(endpoint):
    """인덱스를 엔드포인트에 배포"""

    print(f"\n=== 인덱스 배포 ===")

    # 인덱스 ID 로드
    index_id_file = Path(__file__).parent / "index_id.txt"
    if not index_id_file.exists():
        raise FileNotFoundError(
            f"Index ID 파일을 찾을 수 없습니다: {index_id_file}\n"
            f"먼저 'python scripts/vertex-ai/create_index.py'를 실행하세요."
        )

    with open(index_id_file, "r") as f:
        index_name = f.read().strip()

    print(f"Index: {index_name}")
    print(f"Endpoint: {endpoint.name}")
    print(f"Deployed Index ID: {DEPLOYED_INDEX_ID}")

    # 인덱스 로드
    index = aiplatform.MatchingEngineIndex(index_name=index_name)

    # 인덱스 배포 (자동 스케일링)
    print(f"\n배포 중... (10-15분 소요)")

    endpoint = endpoint.deploy_index(
        index=index,
        deployed_index_id=DEPLOYED_INDEX_ID,
        display_name="poker-hands-deployed-index",
        machine_type="e2-standard-2",  # 최소 머신 타입
        min_replica_count=1,
        max_replica_count=2,  # Auto-scaling
        enable_access_logging=True
    )

    print(f"\n✅ 인덱스 배포 완료!")
    print(f"Deployed Index ID: {DEPLOYED_INDEX_ID}")

    return endpoint


def main():
    """메인 함수"""
    try:
        # 1. 엔드포인트 생성
        endpoint = create_index_endpoint()

        # 2. 인덱스 배포
        endpoint = deploy_index(endpoint)

        # 3. 환경변수 출력
        print(f"\n{'='*60}")
        print(f"배포 완료! 다음 환경변수를 .env 파일에 추가하세요:")
        print(f"\nVERTEX_AI_INDEX_ENDPOINT={endpoint.resource_name}")
        print(f"VERTEX_AI_DEPLOYED_INDEX_ID={DEPLOYED_INDEX_ID}")
        print(f"{'='*60}\n")

        print(f"다음 단계: 임베딩 업로드")
        print(f"python scripts/vertex-ai/upload_embeddings.py")

    except Exception as e:
        print(f"\n❌ 배포 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
