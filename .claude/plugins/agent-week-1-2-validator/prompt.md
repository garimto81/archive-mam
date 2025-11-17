# Week 1-2 Validator: API 설계 및 Mock 환경 검증 ⭐

**역할**: Week 1 (API 설계) 및 Week 2 (Mock 환경) 완료 검증
**중요도**: Critical (전체 개발의 기반)
**버전**: 1.0.0

---

## 🎯 검증 목표

**Week 1 완료 기준**:
- 6개 모듈 OpenAPI 스펙 완성 및 동결
- API 계약 일관성 검증
- PM 승인 완료

**Week 2 완료 기준**:
- Mock BigQuery 테이블 생성 (M3용)
- Mock Embeddings 테이블 생성 (M4용)
- Pub/Sub Emulator 설정 (M5용)
- Prism Mock Servers 설정 (M6용)
- Week 3 개발 시작 준비 완료

---

## 📋 Week 1 검증 체크리스트

### L0: Pre-flight Check
```python
def check_week1_prerequisites():
    """Week 1 시작 전 확인"""

    checks = {
        'prd_approved': read_approval_status('prd_final.md'),
        'team_confirmed': check_team_allocation(),
        'timeline_approved': read_approval_status('week-by-week-timeline.md'),
    }

    assert checks['prd_approved'], "PRD 승인 필요"
    assert checks['team_confirmed'], "팀 배정 확인 필요"
    assert checks['timeline_approved'], "타임라인 승인 필요"

    return all(checks.values())
```

### L1: OpenAPI 스펙 완성 검증
```python
def check_openapi_specs():
    """6개 모듈 OpenAPI 스펙 검증"""

    modules = ['m1', 'm2', 'm3', 'm4', 'm5', 'm6']

    for module in modules:
        spec_path = f'modules/{module}-*/openapi.yaml'

        # 파일 존재 확인
        assert os.path.exists(spec_path), f"{module} OpenAPI 스펙 누락"

        # YAML 유효성 검증
        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        # 필수 필드 확인
        assert 'openapi' in spec, f"{module} OpenAPI 버전 누락"
        assert spec['openapi'].startswith('3.0'), f"{module} OpenAPI 3.0 필요"
        assert 'paths' in spec, f"{module} Paths 정의 누락"
        assert len(spec['paths']) > 0, f"{module} 엔드포인트 없음"

        # Health Check 엔드포인트 필수
        assert '/health' in spec['paths'], f"{module} /health 엔드포인트 필요"

        print(f"✅ {module.upper()} OpenAPI 스펙 검증 완료")
```

### L2: API 계약 일관성 검증
```python
def check_api_consistency():
    """6개 모듈 API 일관성 검증"""

    # 1. 인증 방식 일관성
    auth_methods = []
    for module in ['m1', 'm2', 'm3', 'm4', 'm5', 'm6']:
        spec = load_openapi_spec(module)

        if 'security' in spec:
            auth_methods.append((module, spec['security']))

    # 모든 모듈이 동일한 인증 방식 사용해야 함
    if len(auth_methods) > 0:
        first_auth = auth_methods[0][1]
        for module, auth in auth_methods[1:]:
            assert auth == first_auth, f"{module} 인증 방식 불일치"

    # 2. 에러 응답 형식 일관성
    error_schemas = []
    for module in ['m1', 'm2', 'm3', 'm4', 'm5', 'm6']:
        spec = load_openapi_spec(module)

        # 4xx, 5xx 응답 스키마 추출
        for path, methods in spec['paths'].items():
            for method, details in methods.items():
                if 'responses' in details:
                    for status_code, response in details['responses'].items():
                        if status_code.startswith('4') or status_code.startswith('5'):
                            if 'content' in response:
                                schema = response['content'].get('application/json', {}).get('schema', {})
                                error_schemas.append((module, path, status_code, schema))

    # 에러 스키마 일관성 검증 (최소한 error 필드 포함)
    for module, path, status, schema in error_schemas:
        if 'properties' in schema:
            assert 'error' in schema['properties'], \
                f"{module} {path} {status} 에러 응답에 'error' 필드 필요"

    # 3. Naming Convention 일관성
    endpoints = []
    for module in ['m1', 'm2', 'm3', 'm4', 'm5', 'm6']:
        spec = load_openapi_spec(module)
        for path in spec['paths'].keys():
            endpoints.append((module, path))

    # 모든 엔드포인트가 /v1/ 버저닝 사용해야 함
    for module, path in endpoints:
        if path != '/health':  # Health check 제외
            assert path.startswith('/v1/'), \
                f"{module} {path} API 버저닝 필요 (/v1/...)"

    print("✅ API 계약 일관성 검증 완료")
```

### L3: PM 승인 확인
```python
def check_week1_approval():
    """Week 1 PM 승인 확인"""

    # .validation/week-1-approval.json 파일 확인
    approval_file = '.validation/week-1-approval.json'

    if not os.path.exists(approval_file):
        print("⚠️ Week 1 PM 승인 대기 중")
        print("📧 PM에게 리뷰 요청 이메일 발송...")

        send_approval_request(
            to='aiden.kim@ggproduction.net',
            subject='[Week 1] OpenAPI 스펙 리뷰 요청',
            attachments=[
                'modules/*/openapi.yaml',
                'docs/api-review.md'
            ]
        )

        return False

    with open(approval_file) as f:
        approval = json.load(f)

    assert approval['approved'], "PM 승인 필요"
    assert approval['week'] == 1, "Week 1 승인 아님"

    print(f"✅ Week 1 PM 승인 완료 (승인자: {approval['approver']}, 일시: {approval['timestamp']})")
    return True
```

---

## 📋 Week 2 검증 체크리스트

### L0: Week 1 통과 확인
```python
def check_week2_prerequisites():
    """Week 2 시작 전 Week 1 통과 확인"""

    week1_result = read_validation_status('week-1')
    assert week1_result['passed'], "Week 1 미통과"

    # OpenAPI 스펙 동결 확인
    assert is_frozen('modules/*/openapi.yaml'), "OpenAPI 스펙 동결 필요"

    return True
```

### L1: Mock BigQuery 테이블 생성 (M3용)
```python
def check_mock_bigquery_m3():
    """M3용 Mock BigQuery 테이블 검증"""

    from google.cloud import bigquery

    client = bigquery.Client(project='gg-poker')

    # dev.hand_summary_mock 테이블 확인
    table_id = 'gg-poker.dev.hand_summary_mock'

    try:
        table = client.get_table(table_id)
        print(f"✅ {table_id} 테이블 존재")

        # 스키마 확인
        required_fields = [
            'hand_id', 'event_id', 'tournament_day', 'hand_number',
            'video_file_id', 'start_timecode', 'end_timecode',
            'player_count', 'pot_size', 'flop_cards', 'turn_card', 'river_card'
        ]

        schema_fields = [field.name for field in table.schema]
        for field in required_fields:
            assert field in schema_fields, f"{field} 필드 누락"

        # Mock 데이터 확인 (최소 1000개)
        query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
        result = list(client.query(query))[0]

        assert result.cnt >= 1000, f"Mock 데이터 부족: {result.cnt} (최소 1000개 필요)"

        print(f"✅ Mock 데이터: {result.cnt}개")

    except Exception as e:
        raise AssertionError(f"Mock BigQuery 테이블 생성 실패: {e}")

    # dev.video_files_mock 테이블도 동일하게 확인
    table_id = 'gg-poker.dev.video_files_mock'
    table = client.get_table(table_id)

    query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
    result = list(client.query(query))[0]
    assert result.cnt >= 100, f"video_files_mock 데이터 부족: {result.cnt}"

    print("✅ M3 Mock BigQuery 설정 완료")
```

### L2: Mock Embeddings 테이블 생성 (M4용)
```python
def check_mock_embeddings_m4():
    """M4용 Mock Embeddings 테이블 검증"""

    from google.cloud import bigquery

    client = bigquery.Client(project='gg-poker')

    # dev.hand_embeddings_mock 테이블 확인
    table_id = 'gg-poker.dev.hand_embeddings_mock'

    try:
        table = client.get_table(table_id)

        # 스키마 확인
        schema_fields = [field.name for field in table.schema]
        assert 'hand_id' in schema_fields
        assert 'embedding' in schema_fields, "embedding 필드 필요"

        # Embedding 차원 확인 (768차원)
        query = f"""
        SELECT hand_id, embedding
        FROM `{table_id}`
        LIMIT 1
        """
        result = list(client.query(query))[0]

        embedding = result.embedding
        assert len(embedding) == 768, f"Embedding 차원 불일치: {len(embedding)} (768 필요)"

        # Mock 데이터 개수 확인
        query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
        result = list(client.query(query))[0]
        assert result.cnt >= 1000, f"Mock Embeddings 부족: {result.cnt}"

        print(f"✅ M4 Mock Embeddings 설정 완료 ({result.cnt}개)")

    except Exception as e:
        raise AssertionError(f"Mock Embeddings 테이블 생성 실패: {e}")
```

### L3: Pub/Sub Emulator 설정 (M5용)
```python
def check_pubsub_emulator_m5():
    """M5용 Pub/Sub Emulator 검증"""

    # Pub/Sub Emulator 실행 확인
    import socket

    # localhost:8085 포트 확인
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8085))

    if result != 0:
        print("🚫 Pub/Sub Emulator 미실행")
        print("💡 시작 명령: gcloud beta emulators pubsub start --host-port=localhost:8085")
        raise AssertionError("Pub/Sub Emulator 실행 필요")

    sock.close()

    # Topic 생성 확인
    from google.cloud import pubsub_v1

    os.environ['PUBSUB_EMULATOR_HOST'] = 'localhost:8085'

    publisher = pubsub_v1.PublisherClient()
    project_id = 'gg-poker'

    # clipping-requests topic 확인
    topic_path = publisher.topic_path(project_id, 'clipping-requests')

    try:
        publisher.get_topic(request={"topic": topic_path})
        print(f"✅ Topic 존재: clipping-requests")
    except:
        # Topic 생성
        publisher.create_topic(request={"name": topic_path})
        print(f"✅ Topic 생성: clipping-requests")

    print("✅ M5 Pub/Sub Emulator 설정 완료")
```

### L4: Prism Mock Servers 설정 (M6용)
```python
def check_prism_mock_servers_m6():
    """M6용 Prism Mock Servers 검증"""

    import requests

    # M3, M4, M5 Mock Servers 확인
    mock_servers = {
        'M3': 'http://localhost:8003',
        'M4': 'http://localhost:8004',
        'M5': 'http://localhost:8005',
    }

    for module, url in mock_servers.items():
        try:
            # Health check
            response = requests.get(f"{url}/health", timeout=5)
            assert response.status_code == 200, f"{module} Health Check 실패"

            print(f"✅ {module} Mock Server 실행 중: {url}")

        except requests.exceptions.ConnectionError:
            print(f"🚫 {module} Mock Server 미실행")
            print(f"💡 시작 명령: prism mock modules/{module.lower()}-*/openapi.yaml --port {url.split(':')[-1]}")
            raise AssertionError(f"{module} Mock Server 실행 필요")

    print("✅ M6 Prism Mock Servers 설정 완료")
```

### L5: Week 3 개발 준비 완료
```python
def check_week3_readiness():
    """Week 3 개발 시작 준비 확인"""

    # 1. 모든 개발자 환경 설정 완료 확인
    team_members = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank']

    for member in team_members:
        checklist_file = f'.validation/week-2-setup-{member.lower()}.json'

        if not os.path.exists(checklist_file):
            print(f"⚠️ {member} 환경 설정 미완료")
            return False

        with open(checklist_file) as f:
            setup = json.load(f)

        assert setup['completed'], f"{member} 환경 설정 미완료"

        print(f"✅ {member} 환경 설정 완료")

    # 2. Mock 데이터 검증 스크립트 실행
    result = subprocess.run(
        ['python', 'scripts/validate_mock_data.py'],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Mock 데이터 검증 실패:\n{result.stderr}"

    print("✅ Week 3 개발 시작 준비 완료")
    return True
```

---

## 🔄 자동 재시도 로직

```python
def validate_with_retry_week1_2(max_attempts=3):
    """Week 1-2 검증 (재시도 포함)"""

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"\n🔍 Week 1-2 검증 시도 {attempt}/{max_attempts}...")

            # Week 1 검증
            print("\n📅 Week 1 검증...")
            check_week1_prerequisites()
            check_openapi_specs()
            check_api_consistency()

            if not check_week1_approval():
                # PM 승인 대기
                print("⏳ PM 승인 대기 중... (24시간)")
                time.sleep(24 * 3600)  # 24시간 대기
                continue

            print("✅ Week 1 검증 통과")
            save_validation_result('week-1', passed=True)

            # Week 2 검증
            print("\n📅 Week 2 검증...")
            check_week2_prerequisites()
            check_mock_bigquery_m3()
            check_mock_embeddings_m4()
            check_pubsub_emulator_m5()
            check_prism_mock_servers_m6()
            check_week3_readiness()

            print("✅ Week 2 검증 통과")
            save_validation_result('week-2', passed=True)

            # 성공 알림
            notify_slack("""
            ✅ Week 1-2 검증 통과!

            • Week 1: OpenAPI 스펙 완성 및 PM 승인
            • Week 2: Mock 환경 구축 완료

            🎯 Week 3 개발 시작 준비 완료
            👥 6명 개발자 동시 개발 가능

            다음: Week 3 (6개 모듈 병렬 개발 시작)
            """)

            return True

        except AssertionError as e:
            print(f"❌ 검증 실패: {e}")

            if attempt < max_attempts:
                # 자동 수정 시도
                fix_result = auto_fix_week1_2(e)

                if fix_result:
                    print(f"🔧 자동 수정: {fix_result}")
                else:
                    print("🚫 자동 수정 불가")

                wait_time = 5 * attempt
                print(f"⏳ {wait_time}분 대기 후 재시도...")
                time.sleep(wait_time * 60)

            else:
                # 3회 실패 → PM 에스컬레이션
                escalate_to_pm(
                    subject="Week 1-2 검증 실패 - 개입 필요",
                    error=str(e),
                    severity='HIGH'
                )
                save_validation_result('week-1-2', passed=False, error=str(e))
                return False

    return False

def auto_fix_week1_2(error):
    """Week 1-2 자동 수정"""

    error_str = str(error)

    if "Mock BigQuery" in error_str:
        # Mock 테이블 재생성
        subprocess.run(['python', 'scripts/generate_mock_data_m3.py'])
        return "Mock BigQuery 테이블 재생성"

    elif "Mock Embeddings" in error_str:
        subprocess.run(['python', 'scripts/generate_mock_data_m4.py'])
        return "Mock Embeddings 재생성"

    elif "Pub/Sub Emulator" in error_str:
        # Emulator 재시작
        subprocess.run(['pkill', '-f', 'pubsub-emulator'])
        subprocess.Popen(['gcloud', 'beta', 'emulators', 'pubsub', 'start', '--host-port=localhost:8085'])
        time.sleep(10)
        return "Pub/Sub Emulator 재시작"

    elif "Prism Mock Server" in error_str:
        # Prism 서버 재시작
        subprocess.run(['pkill', '-f', 'prism'])
        start_prism_servers()
        return "Prism Mock Servers 재시작"

    return None
```

---

**에이전트 버전**: 1.0.0
**검증 대상**: Week 1 (API 설계) + Week 2 (Mock 환경)
**중요도**: Critical (전체 개발의 기반)
**자동 재시도**: 최대 3회
**에스컬레이션**: PM 승인 대기 또는 실패 시
