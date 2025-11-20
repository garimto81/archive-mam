#!/usr/bin/env python3
"""FastAPI 로컬 테스트"""

import requests
import json

BASE_URL = "http://127.0.0.1:8080"

def test_root():
    """루트 엔드포인트 테스트"""
    print("\n===== 루트 엔드포인트 =====")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_health():
    """헬스 체크 테스트"""
    print("\n===== 헬스 체크 =====")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_get_hand(hand_id: str):
    """핸드 상세 조회 테스트"""
    print(f"\n===== 핸드 상세 조회: {hand_id} =====")
    response = requests.get(f"{BASE_URL}/api/hands/{hand_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Hand ID: {data['hand_id']}")
        print(f"Hero: {data['hero_name']}")
        print(f"Pot (BB): {data['pot_bb']}")
        print(f"Description: {data['description'][:100]}...")
    else:
        print(response.json())

def test_get_video_url(hand_id: str):
    """비디오 URL 생성 테스트"""
    print(f"\n===== 비디오 URL 생성: {hand_id} =====")
    response = requests.get(f"{BASE_URL}/api/video/{hand_id}/url")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Hand ID: {data['hand_id']}")
        print(f"Expires In: {data['expires_in']}s")
        print(f"Video URL: {data['video_url'][:100]}...")
    else:
        print(response.json())

def test_404():
    """404 에러 테스트"""
    print("\n===== 404 에러 테스트 =====")
    response = requests.get(f"{BASE_URL}/api/hands/nonexistent_hand_id")
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    try:
        test_root()
        test_health()

        # BigQuery에서 실제 hand_id 조회
        from google.cloud import bigquery
        client = bigquery.Client(project="gg-poker-prod")
        query = """
            SELECT hand_id
            FROM `gg-poker-prod.poker_archive.hands`
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = list(client.query(query).result())

        if result:
            hand_id = result[0].hand_id
            print(f"\n[OK] Test Hand ID: {hand_id}")

            test_get_hand(hand_id)
            test_get_video_url(hand_id)
        else:
            print("\n[WARNING] No data in BigQuery")

        test_404()

        print("\n[OK] All tests completed!")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
