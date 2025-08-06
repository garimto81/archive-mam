#!/usr/bin/env python
"""
간단한 백엔드 테스트 서버 (Redis/Celery 없이)
테스트 목적으로만 사용
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from datetime import datetime
import json
import os

app = FastAPI(title="Poker MAM Test API", version="1.0.0-test")

# 테스트 데이터
test_data = {
    "videos": [
        {
            "id": 1,
            "filename": "sample_poker_video.mp4",
            "file_path": "videos/sample_poker_video.mp4",
            "upload_date": "2024-01-20T10:00:00",
            "status": "completed",
            "task_id": "test-task-1"
        }
    ],
    "hands": []
}

# 분석 결과 파일에서 핸드 데이터 로드
if os.path.exists("analysis_results/poker_hands_analysis.json"):
    with open("analysis_results/poker_hands_analysis.json", "r") as f:
        hands_data = json.load(f)
        # 처음 50개만 로드
        for i, hand in enumerate(hands_data[:50]):
            test_data["hands"].append({
                "id": i + 1,
                "video_id": 1,
                "video_filename": "sample_poker_video.mp4",
                "start_time_s": hand.get("start_time_s", 0),
                "end_time_s": hand.get("end_time_s", 0),
                "pot_size_history": hand.get("pot_size_history", []),
                "participating_players": hand.get("participating_players", []),
                "analysis_date": "2024-01-20T10:00:00"
            })

@app.get("/")
async def root():
    return {"message": "Welcome to Poker MAM Test API", "version": "1.0.0-test"}

@app.get("/stats")
async def get_stats():
    return {
        "total_videos": len(test_data["videos"]),
        "total_hands": len(test_data["hands"]),
        "videos_by_status": {
            "pending": 0,
            "processing": 0,
            "completed": 1,
            "failed": 0
        },
        "average_hands_per_video": len(test_data["hands"]) / len(test_data["videos"]) if test_data["videos"] else 0
    }

@app.get("/videos/")
async def get_videos():
    return test_data["videos"]

@app.get("/videos/{video_id}")
async def get_video(video_id: int):
    for video in test_data["videos"]:
        if video["id"] == video_id:
            return video
    raise HTTPException(status_code=404, detail="Video not found")

@app.get("/hands/")
async def get_hands(skip: int = 0, limit: int = 100, video_id: int = None):
    hands = test_data["hands"]
    if video_id:
        hands = [h for h in hands if h.get("video_id") == video_id]
    return hands[skip:skip + limit]

@app.get("/hands/{hand_id}")
async def get_hand(hand_id: int):
    for hand in test_data["hands"]:
        if hand["id"] == hand_id:
            return hand
    raise HTTPException(status_code=404, detail="Hand not found")

@app.post("/hands/search")
async def search_hands(filters: dict):
    results = test_data["hands"]
    
    # 간단한 필터링
    if filters.get("min_pot_size"):
        results = [h for h in results if any(
            p.get("pot", 0) >= filters["min_pot_size"] 
            for p in h.get("pot_size_history", [])
        )]
    
    if filters.get("player_name"):
        results = [h for h in results if filters["player_name"] in h.get("participating_players", [])]
    
    return results

@app.post("/videos/upload")
async def upload_video():
    # 테스트 응답
    return {
        "id": 2,
        "filename": "test_upload.mp4",
        "file_path": "uploads/test_upload.mp4",
        "upload_date": datetime.now().isoformat(),
        "status": "pending",
        "task_id": "test-task-2"
    }

@app.post("/clips/generate")
async def generate_clip(data: dict):
    # 테스트 응답
    return {
        "task_id": "clip-task-1",
        "hand_id": data.get("hand_id"),
        "output_filename": f"hand_{data.get('hand_id')}_clip.mp4"
    }

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Poker MAM 테스트 서버 시작")
    print("="*50)
    print("\n이 서버는 Redis/Celery 없이 동작하는 간단한 테스트 서버입니다.")
    print("실제 영상 분석 기능은 동작하지 않습니다.\n")
    print("API 문서: http://localhost:8000/docs")
    print("프론트엔드와 연동: http://localhost:3000")
    print("\n종료하려면 Ctrl+C를 누르세요.\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)