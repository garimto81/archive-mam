# Week 5 Validator: Mock → Real 전환 검증 ⭐⭐

**역할**: M2 완료 및 Mock → Real 데이터 전환 검증
**중요도**: Critical (Mock 개발 → Real 환경 전환)
**버전**: 1.0.0

---

## 🎯 검증 목표

**Week 5 완료 기준**:
- M2 Video Metadata Service 완료
- M3, M4가 Mock → Real BigQuery 전환
- M5가 Pub/Sub Emulator → Real Pub/Sub 전환
- M6가 Prism Mock → Real API 전환
- 전환 후 통합 테스트 통과

---

## 📋 검증 체크리스트

### L0: Pre-flight Check
```python
def check_prerequisites():
    """Week 4 통과 및 M2 준비 확인"""

    checks = {
        'week_4_passed': read_validation_status('week-4'),
        'm2_progress': get_module_progress('m2'),
        'm1_deployed': is_service_deployed('data-ingestion-service'),
    }

    assert checks['week_4_passed'], "Week 4 검증 미통과"
    assert checks['m2_progress'] >= 80, f"M2 진행률 부족: {checks['m2_progress']}%"
    assert checks['m1_deployed'], "M1 배포 필요 (M3, M4 의존성)"

    return all(checks.values())
```

### L1: M2 완료 검증
```python
def check_m2_completion():
    """M2 Video Metadata Service 완료 검증"""

    # 1. 작업 산출물 확인
    required_files = [
        'm2-video-metadata/app/nas_scanner.py',
        'm2-video-metadata/app/metadata_extractor.py',
        'm2-video-metadata/app/proxy_generator.py',
        'm2-video-metadata/app/api.py',
        'm2-video-metadata/Dockerfile',
        'm2-video-metadata/tests/test_scanner.py',
    ]

    for file in required_files:
        assert os.path.exists(file), f"파일 누락: {file}"

    # 2. Cloud Run 배포 확인
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe',
        'video-metadata-service',
        '--region', 'us-central1',
        '--format', 'value(status.url)'
    ], capture_output=True, text=True)

    service_url = result.stdout.strip()
    assert service_url, "M2 Cloud Run 배포 안 됨"

    # 3. API 엔드포인트 테스트
    import requests

    # Health check
    response = requests.get(f"{service_url}/health")
    assert response.status_code == 200, "M2 Health Check 실패"

    # NAS scan 테스트 (dry-run)
    response = requests.post(f"{service_url}/v1/scan", json={
        "directory_path": "/mnt/nas/wsop/2024/test",
        "dry_run": True
    })
    assert response.status_code == 200, "M2 Scan API 실패"

    # 4. GCS 프록시 파일 생성 확인
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket('gg-poker-ati')

    # proxy/ 폴더에 최소 1개 프록시 파일 확인
    blobs = list(bucket.list_blobs(prefix='proxy/', max_results=10))
    assert len(blobs) > 0, "프록시 파일 생성 안 됨"

    print("✅ M2 Video Metadata Service 완료")
```

### L2: M3 Mock → Real 전환 검증
```python
def check_m3_transition():
    """M3 Mock → Real BigQuery 전환"""

    # 1. 환경 변수 전환 확인
    m3_env_file = 'm3-timecode-validation/.env'

    with open(m3_env_file) as f:
        env_content = f.read()

    assert 'POKER_ENV=production' in env_content, \
        "M3 환경 변수 미전환 (POKER_ENV=production 필요)"

    # 2. Real BigQuery 테이블 접근 테스트
    from google.cloud import bigquery

    client = bigquery.Client(project='gg-poker')

    # prod.hand_summary 읽기 테스트
    query = """
    SELECT hand_id, event_id, start_timecode
    FROM `gg-poker.prod.hand_summary`
    LIMIT 5
    """

    try:
        results = list(client.query(query))
        assert len(results) > 0, "prod.hand_summary 데이터 없음"

        print(f"✅ M3 Real BigQuery 접근 성공 ({len(results)}개 조회)")

    except Exception as e:
        raise AssertionError(f"M3 Real BigQuery 접근 실패: {e}")

    # 3. M3 API로 Real 데이터 조회 테스트
    import requests

    # M3 Cloud Run URL 가져오기
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe',
        'timecode-validation-service',
        '--region', 'us-central1',
        '--format', 'value(status.url)'
    ], capture_output=True, text=True)

    m3_url = result.stdout.strip()

    # Real 데이터로 timecode 검증 요청
    response = requests.post(f"{m3_url}/v1/timecode/validate", json={
        "hand_id": "wsop2024_me_d1_h001",  # Real hand_id
        "video_file_id": "wsop2024_me_d1_table3",
        "start_timecode": "01:23:45",
        "end_timecode": "01:25:30"
    })

    assert response.status_code == 200, f"M3 Real 데이터 검증 실패: {response.status_code}"

    result_data = response.json()
    assert 'sync_score' in result_data, "sync_score 누락"
    assert result_data['sync_score'] > 0, "sync_score 계산 안 됨"

    print(f"✅ M3 Mock → Real 전환 완료 (sync_score: {result_data['sync_score']})")
```

### L3: M4 Mock → Real 전환 검증
```python
def check_m4_transition():
    """M4 Mock Embeddings → Real Vertex AI 전환"""

    # 1. 환경 변수 전환 확인
    m4_env_file = 'm4-rag-search/.env'

    with open(m4_env_file) as f:
        env_content = f.read()

    assert 'POKER_ENV=production' in env_content, \
        "M4 환경 변수 미전환 (POKER_ENV=production 필요)"

    # 2. Vertex AI 접근 테스트
    import requests

    # M4 Cloud Run URL 가져오기
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe',
        'rag-search-service',
        '--region', 'us-central1',
        '--format', 'value(status.url)'
    ], capture_output=True, text=True)

    m4_url = result.stdout.strip()

    # Real Vertex AI로 검색 요청
    response = requests.post(f"{m4_url}/v1/search", json={
        "query": "2024 WSOP Main Event Day 1 all-in hands",
        "top_k": 5
    })

    assert response.status_code == 200, f"M4 Real 검색 실패: {response.status_code}"

    results = response.json()['results']
    assert len(results) > 0, "검색 결과 없음"

    # Real Embedding 사용 확인 (Mock은 random, Real은 의미 기반)
    first_result = results[0]
    assert 'hand_id' in first_result
    assert 'relevance_score' in first_result
    assert first_result['relevance_score'] > 0.1, \
        "Relevance score 너무 낮음 (Mock일 가능성)"

    print(f"✅ M4 Mock → Real 전환 완료 ({len(results)}개 결과)")
```

### L4: M5 Pub/Sub Emulator → Real 전환 검증
```python
def check_m5_transition():
    """M5 Pub/Sub Emulator → Real Pub/Sub 전환"""

    # 1. 환경 변수 확인 (PUBSUB_EMULATOR_HOST 제거됨)
    m5_env_file = 'm5-clipping/.env'

    with open(m5_env_file) as f:
        env_content = f.read()

    assert 'POKER_ENV=production' in env_content, \
        "M5 환경 변수 미전환"
    assert 'PUBSUB_EMULATOR_HOST' not in env_content, \
        "Pub/Sub Emulator 설정 제거 필요"

    # 2. Real Pub/Sub Topic 확인
    from google.cloud import pubsub_v1

    publisher = pubsub_v1.PublisherClient()
    project_id = 'gg-poker'

    topic_path = publisher.topic_path(project_id, 'clipping-requests')

    try:
        topic = publisher.get_topic(request={"topic": topic_path})
        print(f"✅ Real Pub/Sub Topic 존재: {topic.name}")

    except Exception as e:
        raise AssertionError(f"Real Pub/Sub Topic 접근 실패: {e}")

    # 3. M5 API로 Real Pub/Sub 메시지 발행 테스트
    import requests

    # M5 Cloud Run URL 가져오기
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe',
        'clipping-service',
        '--region', 'us-central1',
        '--format', 'value(status.url)'
    ], capture_output=True, text=True)

    m5_url = result.stdout.strip()

    # Clipping 요청 (Real Pub/Sub 사용)
    response = requests.post(f"{m5_url}/v1/clip", json={
        "hand_id": "wsop2024_me_d1_h001",
        "video_file_id": "wsop2024_me_d1_table3",
        "start_timecode": "01:23:45",
        "end_timecode": "01:25:30",
        "output_format": "mp4"
    })

    assert response.status_code == 202, f"M5 Clipping 요청 실패: {response.status_code}"

    request_id = response.json()['request_id']
    assert request_id, "request_id 누락"

    # Pub/Sub 메시지 발행 확인 (Subscription으로 확인)
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, 'clipping-requests-sub')

    # 메시지 풀 (최대 5초 대기)
    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": 1},
        timeout=5
    )

    assert len(response.received_messages) > 0, "Pub/Sub 메시지 발행 안 됨"

    print(f"✅ M5 Emulator → Real Pub/Sub 전환 완료")
```

### L5: M6 Prism Mock → Real API 전환 검증
```python
def check_m6_transition():
    """M6 Prism Mock → Real API 전환"""

    # 1. 환경 변수 전환 확인
    m6_env_file = 'm6-web-ui/.env.local'

    with open(m6_env_file) as f:
        env_content = f.read()

    assert 'NEXT_PUBLIC_ENV=production' in env_content, \
        "M6 환경 변수 미전환"

    # Real API URLs 확인
    required_vars = [
        'M3_API_URL',  # Real M3 URL
        'M4_API_URL',  # Real M4 URL
        'M5_API_URL',  # Real M5 URL
    ]

    for var in required_vars:
        assert var in env_content, f"{var} 환경 변수 누락"
        # localhost가 아닌지 확인
        value = env_content.split(f'{var}=')[1].split('\n')[0]
        assert 'localhost' not in value, f"{var}이 여전히 localhost"

    # 2. Next.js API Routes로 Real API 호출 테스트
    # (로컬 개발 서버 실행 필요)
    import requests

    # Next.js dev 서버 시작 (포트 3000)
    import subprocess
    import time

    proc = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd='m6-web-ui/',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(10)  # 서버 시작 대기

    try:
        # M6 BFF로 검색 요청 (Real M4 호출)
        response = requests.post('http://localhost:3000/api/search', json={
            "query": "2024 WSOP Main Event",
            "top_k": 5
        })

        assert response.status_code == 200, f"M6 검색 API 실패: {response.status_code}"

        results = response.json()['results']
        assert len(results) > 0, "검색 결과 없음"

        print(f"✅ M6 Mock → Real API 전환 완료 ({len(results)}개 결과)")

    finally:
        proc.kill()
```

### L6: 통합 테스트
```python
def check_integration_after_transition():
    """Mock → Real 전환 후 통합 테스트"""

    # E2E 시나리오: 검색 → timecode 검증 → 클리핑 요청
    import requests

    # 1. M4로 검색
    m4_url = get_service_url('rag-search-service')

    search_response = requests.post(f"{m4_url}/v1/search", json={
        "query": "2024 WSOP Main Event Day 1 all-in",
        "top_k": 1
    })

    assert search_response.status_code == 200
    hand = search_response.json()['results'][0]

    # 2. M3로 timecode 검증
    m3_url = get_service_url('timecode-validation-service')

    validate_response = requests.post(f"{m3_url}/v1/timecode/validate", json={
        "hand_id": hand['hand_id'],
        "video_file_id": hand['video_file_id'],
        "start_timecode": hand['start_timecode'],
        "end_timecode": hand['end_timecode']
    })

    assert validate_response.status_code == 200
    sync_score = validate_response.json()['sync_score']
    assert sync_score > 50, f"sync_score 너무 낮음: {sync_score}"

    # 3. M5로 클리핑 요청
    m5_url = get_service_url('clipping-service')

    clip_response = requests.post(f"{m5_url}/v1/clip", json={
        "hand_id": hand['hand_id'],
        "video_file_id": hand['video_file_id'],
        "start_timecode": hand['start_timecode'],
        "end_timecode": hand['end_timecode'],
        "output_format": "mp4"
    })

    assert clip_response.status_code == 202
    request_id = clip_response.json()['request_id']

    print(f"✅ 통합 테스트 통과 (hand_id: {hand['hand_id']}, request_id: {request_id})")
```

---

## 🔄 자동 재시도 로직

```python
def validate_with_retry(max_attempts=3):
    """Week 5 검증 (재시도 포함)"""

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"\n🔍 Week 5 (Mock → Real 전환) 검증 시도 {attempt}/{max_attempts}...")

            # 순차 검증
            check_prerequisites()
            check_m2_completion()
            check_m3_transition()
            check_m4_transition()
            check_m5_transition()
            check_m6_transition()
            check_integration_after_transition()

            # 모두 통과
            print("✅ Week 5 검증 통과!")
            save_validation_result('week-5', passed=True)

            notify_slack("""
            ✅ Week 5 검증 통과!

            • M2 Video Metadata: 완료
            • M3, M4: Mock → Real BigQuery 전환 성공
            • M5: Emulator → Real Pub/Sub 전환 성공
            • M6: Prism Mock → Real API 전환 성공
            • 통합 테스트: 통과

            🎯 다음: Week 6 (M3, M4, M5, M6 완료)
            """)

            return True

        except AssertionError as e:
            print(f"❌ 검증 실패: {e}")

            if attempt < max_attempts:
                # 자동 수정 시도
                fix_result = auto_fix_week5(e)

                if fix_result:
                    print(f"🔧 자동 수정: {fix_result}")
                    wait_time = 10 * attempt
                    print(f"⏳ {wait_time}분 대기 후 재시도...")
                    time.sleep(wait_time * 60)
                else:
                    print("🚫 자동 수정 불가")
                    break

            else:
                # 3회 실패 → PM 에스컬레이션
                escalate_to_pm(
                    subject="Week 5 (Mock → Real 전환) 검증 실패",
                    error=str(e),
                    severity='HIGH'
                )
                save_validation_result('week-5', passed=False, error=str(e))
                return False

    return False

def auto_fix_week5(error):
    """Week 5 자동 수정"""

    error_str = str(error)

    if "환경 변수 미전환" in error_str:
        # 자동으로 .env 파일 수정
        for module in ['m3', 'm4', 'm5', 'm6']:
            update_env_file(module, 'POKER_ENV', 'production')

        return "환경 변수 자동 전환 (POKER_ENV=production)"

    elif "Real BigQuery 접근 실패" in error_str:
        # BigQuery 권한 확인 및 재설정
        grant_bigquery_access()
        return "BigQuery 권한 재설정"

    elif "Pub/Sub Topic 접근 실패" in error_str:
        # Real Topic 생성
        create_pubsub_topic('clipping-requests')
        return "Pub/Sub Topic 생성"

    elif "M2 배포 안 됨" in error_str:
        # M2 자동 배포
        deploy_module('m2')
        return "M2 자동 배포"

    return None
```

---

**에이전트 버전**: 1.0.0
**검증 대상**: M2 완료 + Mock → Real 전환 (M3, M4, M5, M6)
**중요도**: Critical (Real 환경 전환)
**자동 재시도**: 최대 3회
**에스컬레이션**: PM (전환 실패 시)
