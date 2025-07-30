#!/usr/bin/env python
"""
API 엔드포인트 통합 테스트
"""
import pytest
import httpx
import asyncio
import json
import os
from pathlib import Path

# 테스트 서버 URL
BASE_URL = "http://localhost:8000"

class TestPokerMAMAPI:
    """Poker MAM API 통합 테스트"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """HTTP 클라이언트 설정"""
        return httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    def test_root_endpoint(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome" in data["message"]
    
    def test_stats_endpoint(self, client):
        """통계 엔드포인트 테스트"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        
        # 필수 필드 확인
        required_fields = ["total_videos", "total_hands", "videos_by_status", "average_hands_per_video"]
        for field in required_fields:
            assert field in data
        
        # 데이터 타입 확인
        assert isinstance(data["total_videos"], int)
        assert isinstance(data["total_hands"], int)
        assert isinstance(data["videos_by_status"], dict)
        assert isinstance(data["average_hands_per_video"], (int, float))
    
    def test_videos_list_endpoint(self, client):
        """영상 목록 엔드포인트 테스트"""
        response = client.get("/videos/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_hands_list_endpoint(self, client):
        """핸드 목록 엔드포인트 테스트"""
        response = client.get("/hands/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_hands_search_endpoint(self, client):
        """핸드 검색 엔드포인트 테스트"""
        search_filters = {
            "min_pot_size": 1000,
            "max_pot_size": 5000
        }
        response = client.post("/hands/search", json=search_filters)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_video_not_found(self, client):
        """존재하지 않는 영상 조회 테스트"""
        response = client.get("/videos/99999")
        assert response.status_code == 404
    
    def test_hand_not_found(self, client):
        """존재하지 않는 핸드 조회 테스트"""
        response = client.get("/hands/99999")
        assert response.status_code == 404
    
    def test_invalid_search_filters(self, client):
        """잘못된 검색 필터 테스트"""
        invalid_filters = {
            "min_pot_size": "invalid_string"
        }
        # 422 Unprocessable Entity 또는 다른 적절한 오류 코드 예상
        response = client.post("/hands/search", json=invalid_filters)
        # 서버가 어떻게 처리하는지에 따라 상태 코드가 다를 수 있음
        assert response.status_code in [400, 422, 500]


def run_load_test():
    """간단한 로드 테스트"""
    import time
    import concurrent.futures
    
    def make_request():
        try:
            with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
                response = client.get("/stats")
                return response.status_code == 200
        except:
            return False
    
    print("로드 테스트 시작 (100개 동시 요청)...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    success_count = sum(results)
    
    print(f"로드 테스트 완료:")
    print(f"- 총 요청: 100개")
    print(f"- 성공: {success_count}개")
    print(f"- 실패: {100 - success_count}개")
    print(f"- 소요 시간: {end_time - start_time:.2f}초")
    print(f"- 평균 응답 시간: {(end_time - start_time) / 100:.3f}초/요청")


if __name__ == "__main__":
    print("Poker MAM API 테스트 시작...")
    print("=" * 50)
    
    # 기본 연결 테스트
    try:
        with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
            response = client.get("/")
            if response.status_code == 200:
                print("✅ 서버 연결 성공")
            else:
                print(f"❌ 서버 연결 실패: {response.status_code}")
                exit(1)
    except Exception as e:
        print(f"❌ 서버에 연결할 수 없습니다: {e}")
        print("테스트 서버가 실행 중인지 확인하세요 (run_test_server.bat)")
        exit(1)
    
    # pytest 실행
    print("\n단위 테스트 실행...")
    pytest.main([__file__, "-v"])
    
    # 로드 테스트 실행
    print("\n" + "=" * 50)
    run_load_test()