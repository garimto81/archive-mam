# Mock 환경 사용 가이드

## 개요

Week 3-6 병렬 개발을 위한 로컬 Mock 환경입니다.

## Mock 데이터

### 1. BigQuery Mock (M3용)
- `mock_data/bigquery/hand_summary_mock.json` (100 hands)
- `mock_data/bigquery/video_files_mock.json` (10 videos)

### 2. Embeddings Mock (M4용)
- `mock_data/embeddings/hand_embeddings_mock.json` (100 embeddings, 768-dim)

### 3. Pub/Sub Mock (M5용)
- Python `unittest.mock` 사용
- `mock_data/pubsub/config.json` 참조

## Mock API 서버 실행 (M6용)

### Terminal 1: M3 Mock Server
```bash
python mock_servers/m3_mock_server.py
# → http://localhost:8003
```

### Terminal 2: M4 Mock Server
```bash
python mock_servers/m4_mock_server.py
# → http://localhost:8004
```

### Terminal 3: M5 Mock Server
```bash
python mock_servers/m5_mock_server.py
# → http://localhost:8005
```

## 환경 변수 (개발 시)

### M3 (Charlie)
```bash
export POKER_ENV=development
export BIGQUERY_MOCK_DATA=mock_data/bigquery/hand_summary_mock.json
```

### M4 (David)
```bash
export POKER_ENV=development
export EMBEDDINGS_MOCK_DATA=mock_data/embeddings/hand_embeddings_mock.json
```

### M5 (Eve)
```bash
export POKER_ENV=development
export PUBSUB_EMULATOR_HOST=localhost:8085  # 또는 Python mock 사용
```

### M6 (Frank)
```bash
export M3_API_URL=http://localhost:8003
export M4_API_URL=http://localhost:8004
export M5_API_URL=http://localhost:8005
```

## Mock → Real 전환 (Week 5)

Week 5부터는 환경 변수를 `production`으로 변경:

```bash
export POKER_ENV=production
```

이후 M3-M6는 자동으로 실제 GCP 서비스에 연결됩니다.

## 테스트

```bash
# M3 Health Check
curl http://localhost:8003/v1/health

# M4 Health Check
curl http://localhost:8004/v1/health

# M5 Health Check
curl http://localhost:8005/v1/health
```
