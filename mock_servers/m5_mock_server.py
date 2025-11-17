#!/usr/bin/env python3
"""M5 Clipping Mock Server"""

from flask import Flask, jsonify, request
import uuid
import random

app = Flask(__name__)

CLIP_REQUESTS = {}


@app.route('/v1/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "m5-mock"}), 200


@app.route('/v1/clip', methods=['POST'])
def create_clip():
    data = request.json

    request_id = str(uuid.uuid4())

    CLIP_REQUESTS[request_id] = {
        "request_id": request_id,
        "video_id": data.get("video_id"),
        "start_time": data.get("start_time"),
        "end_time": data.get("end_time"),
        "status": "processing"
    }

    return jsonify({"request_id": request_id}), 202


@app.route('/v1/clip/<request_id>/status', methods=['GET'])
def get_clip_status(request_id):
    if request_id not in CLIP_REQUESTS:
        return jsonify({"error": "Request not found"}), 404

    # Mock: 랜덤하게 완료 처리
    if random.random() > 0.5:
        CLIP_REQUESTS[request_id]["status"] = "completed"
        CLIP_REQUESTS[request_id]["download_url"] = f"https://storage.googleapis.com/mock-clips/{request_id}.mp4"

    return jsonify(CLIP_REQUESTS[request_id]), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8005, debug=True)
