#!/usr/bin/env python3
"""M3 Timecode Validation Mock Server"""

from flask import Flask, jsonify, request
import json
import random

app = Flask(__name__)

# Mock 데이터 로드
with open('mock_data/bigquery/hand_summary_mock.json', 'r', encoding='utf-8') as f:
    HANDS = json.load(f)

with open('mock_data/bigquery/video_files_mock.json', 'r', encoding='utf-8') as f:
    VIDEOS = json.load(f)


@app.route('/v1/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "m3-mock"}), 200


@app.route('/v1/validate', methods=['POST'])
def validate_timecode():
    data = request.json
    hand_id = data.get('hand_id')
    timecode = data.get('timecode')

    # Mock 검증 결과
    result = {
        "hand_id": hand_id,
        "timecode": timecode,
        "validated": True,
        "sync_score": random.uniform(75.0, 95.0),
        "video_id": f"VIDEO_{random.randint(1, 10):04d}",
        "confidence": random.uniform(0.8, 0.99)
    }

    return jsonify(result), 200


@app.route('/v1/search', methods=['POST'])
def search_hands():
    data = request.json
    query = data.get('query', '')

    # Mock 검색 결과 (랜덤 5개)
    results = random.sample(HANDS, min(5, len(HANDS)))

    return jsonify({
        "query": query,
        "results": results,
        "total": len(results)
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)
