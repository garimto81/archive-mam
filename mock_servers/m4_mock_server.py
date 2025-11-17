#!/usr/bin/env python3
"""M4 RAG Search Mock Server"""

from flask import Flask, jsonify, request
import json
import random

app = Flask(__name__)

# Mock 데이터 로드
with open('mock_data/embeddings/hand_embeddings_mock.json', 'r', encoding='utf-8') as f:
    EMBEDDINGS = json.load(f)


@app.route('/v1/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "m4-mock"}), 200


@app.route('/v1/search', methods=['POST'])
def rag_search():
    data = request.json
    query = data.get('query', '')

    # Mock RAG 검색 결과
    results = []
    for i in range(5):
        emb = random.choice(EMBEDDINGS)
        results.append({
            "hand_id": emb["hand_id"],
            "relevance_score": random.uniform(0.7, 0.99),
            "snippet": f"Mock result for query: {query}"
        })

    return jsonify({
        "query": query,
        "results": results,
        "model": "textembedding-gecko@003"
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, debug=True)
