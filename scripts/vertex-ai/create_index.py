#!/usr/bin/env python3
"""
Vertex AI Vector Search 인덱스 생성 스크립트
v4.0.0 - textembedding-gecko@003 (768차원)
"""

import os
import sys
import json
import time
from pathlib import Path
from google.cloud import aiplatform


# 프로젝트 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "gg-poker-prod")
REGION = os.getenv("GCP_REGION", "us-central1")
INDEX_CONFIG_PATH = Path(__file__).parent / "index_config.json"


def create_vector_search_index():
    """Vertex AI Vector Search 인덱스 생성"""

    print(f"\n=== Vertex AI Vector Search 인덱스 생성 ===")
    print(f"프로젝트: {PROJECT_ID}")
    print(f"리전: {REGION}")

    # Vertex AI SDK 초기화
    aiplatform.init(
        project=PROJECT_ID,
        location=REGION
    )

    # 인덱스 구성 로드
    with open(INDEX_CONFIG_PATH, "r") as f:
        index_config = json.load(f)

    print(f"\n인덱스 구성:")
    print(f"- Display Name: {index_config['displayName']}")
    print(f"- Dimensions: {index_config['metadata']['config']['dimensions']}")
    print(f"- Distance: {index_config['metadata']['config']['distanceMeasureType']}")
    print(f"- Update Method: {index_config['indexUpdateMethod']}")

    # 인덱스 생성 (비동기)
    print(f"\n인덱스 생성 중...")

    index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
        display_name=index_config['displayName'],
        dimensions=index_config['metadata']['config']['dimensions'],
        approximate_neighbors_count=index_config['metadata']['config']['approximateNeighborsCount'],
        distance_measure_type=index_config['metadata']['config']['distanceMeasureType'],
        leaf_node_embedding_count=index_config['metadata']['config']['algorithmConfig']['treeAhConfig']['leafNodeEmbeddingCount'],
        leaf_nodes_to_search_percent=index_config['metadata']['config']['algorithmConfig']['treeAhConfig']['leafNodesToSearchPercent'],
        description=index_config['description'],
        shard_size=index_config['metadata']['config']['shardSize'],
        index_update_method=index_config['indexUpdateMethod']
    )

    print(f"\n✅ 인덱스 생성 완료!")
    print(f"Index ID: {index.name}")
    print(f"Resource Name: {index.resource_name}")

    # 인덱스 ID 저장
    index_id_file = Path(__file__).parent / "index_id.txt"
    with open(index_id_file, "w") as f:
        f.write(index.name)

    print(f"\nIndex ID 저장: {index_id_file}")

    return index


def main():
    """메인 함수"""
    try:
        # 인덱스 생성
        index = create_vector_search_index()

        print(f"\n{'='*60}")
        print(f"다음 단계: 인덱스 엔드포인트 생성 및 배포")
        print(f"python scripts/vertex-ai/deploy_index.py")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ 인덱스 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
