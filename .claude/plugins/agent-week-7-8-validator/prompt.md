# Week 7-8 Validator: E2E 테스트 및 버그 수정 검증 ⭐⭐

**역할**: Week 7 (E2E 80% 통과) 및 Week 8 (100% 통과) 검증
**중요도**: Critical (Production 배포 전 최종 품질 검증)
**버전**: 1.0.0

---

## 🎯 검증 목표

**Week 7 완료 기준**:
- E2E 테스트 작성 완료 (Playwright)
- 5개 핵심 시나리오 모두 구현
- E2E 테스트 80% 이상 통과
- 남은 버그 리스트 작성

**Week 8 완료 기준**:
- 모든 버그 수정 완료
- E2E 테스트 100% 통과
- Performance 테스트 통과
- Production 배포 준비 완료

---

## 📋 Week 7 검증 체크리스트

### L0: Pre-flight Check
```python
def check_week7_prerequisites():
    """Week 6 통과 확인"""

    checks = {
        'week_6_passed': read_validation_status('week-6'),
        'all_modules_deployed': check_all_modules_deployed(),
        'integration_tests_passed': check_integration_tests(),
    }

    assert checks['week_6_passed'], "Week 6 검증 미통과"
    assert checks['all_modules_deployed'], "일부 모듈 미배포"
    assert checks['integration_tests_passed'], "통합 테스트 미통과"

    return all(checks.values())

def check_all_modules_deployed():
    """6개 모듈 모두 배포 확인"""

    services = [
        'data-ingestion-service',          # M1
        'video-metadata-service',           # M2
        'timecode-validation-service',      # M3
        'rag-search-service',               # M4
        'clipping-service',                 # M5
        'poker-brain-ui',                   # M6
    ]

    for service in services:
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', service,
            '--region', 'us-central1',
            '--format', 'value(status.url)'
        ], capture_output=True, text=True)

        url = result.stdout.strip()
        assert url, f"{service} 배포 안 됨"

        # Health Check
        import requests
        response = requests.get(f"{url}/health", timeout=10)
        assert response.status_code == 200, f"{service} Health Check 실패"

        print(f"✅ {service} 배포 및 동작 중")

    return True
```

### L1: E2E 테스트 구현 완료 확인
```python
def check_e2e_implementation():
    """Playwright E2E 테스트 구현 확인"""

    # 1. Playwright 설정 파일 확인
    required_files = [
        'm6-web-ui/playwright.config.ts',
        'm6-web-ui/tests/e2e/search-flow.spec.ts',
        'm6-web-ui/tests/e2e/video-preview.spec.ts',
        'm6-web-ui/tests/e2e/timecode-validation.spec.ts',
        'm6-web-ui/tests/e2e/clipping-request.spec.ts',
        'm6-web-ui/tests/e2e/download-clip.spec.ts',
    ]

    for file in required_files:
        assert os.path.exists(file), f"E2E 테스트 파일 누락: {file}"

    # 2. 각 시나리오별 테스트 케이스 개수 확인
    test_files = [
        'm6-web-ui/tests/e2e/search-flow.spec.ts',
        'm6-web-ui/tests/e2e/video-preview.spec.ts',
        'm6-web-ui/tests/e2e/timecode-validation.spec.ts',
        'm6-web-ui/tests/e2e/clipping-request.spec.ts',
        'm6-web-ui/tests/e2e/download-clip.spec.ts',
    ]

    for test_file in test_files:
        with open(test_file) as f:
            content = f.read()

        # test() 또는 it() 개수 확인 (최소 3개)
        test_count = content.count("test('") + content.count('test("')
        assert test_count >= 3, f"{test_file}: 테스트 케이스 부족 ({test_count}개, 최소 3개 필요)"

        print(f"✅ {os.path.basename(test_file)}: {test_count}개 테스트")

    print("✅ E2E 테스트 구현 완료")
```

### L2: E2E 테스트 실행 (80% 통과 목표)
```python
def check_e2e_execution_week7():
    """E2E 테스트 실행 (Week 7: 80% 통과 목표)"""

    # Playwright 테스트 실행
    result = subprocess.run(
        ['npx', 'playwright', 'test', '--reporter=json'],
        cwd='m6-web-ui/',
        capture_output=True,
        text=True
    )

    # 결과 파싱
    import json

    try:
        report = json.loads(result.stdout)
    except:
        # JSON 파싱 실패 시 텍스트 분석
        stdout = result.stdout

        # "5 passed" 패턴 찾기
        import re
        match = re.search(r'(\d+) passed', stdout)
        passed = int(match.group(1)) if match else 0

        match = re.search(r'(\d+) failed', stdout)
        failed = int(match.group(1)) if match else 0

        total = passed + failed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n📊 E2E 테스트 결과 (Week 7)")
        print(f"  • 통과: {passed}/{total} ({pass_rate:.1f}%)")
        print(f"  • 실패: {failed}/{total}")

        # Week 7: 80% 이상 통과 필요
        assert pass_rate >= 80, f"E2E 통과율 부족: {pass_rate:.1f}% (80% 필요)"

        # 실패한 테스트 리스트 추출 및 저장
        if failed > 0:
            save_failed_tests_week7(stdout)

        return True

    # JSON 리포트 처리
    total_tests = report.get('stats', {}).get('expected', 0)
    passed_tests = report.get('stats', {}).get('passed', 0)
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"\n📊 E2E 테스트 결과 (Week 7)")
    print(f"  • 통과: {passed_tests}/{total_tests} ({pass_rate:.1f}%)")

    assert pass_rate >= 80, f"E2E 통과율 부족: {pass_rate:.1f}% (80% 필요)"

    # 실패한 테스트 버그 티켓 생성
    if passed_tests < total_tests:
        create_bug_tickets_from_failures(report)

    print(f"✅ Week 7 E2E 테스트 {pass_rate:.1f}% 통과")
    return True

def save_failed_tests_week7(stdout):
    """실패한 테스트 리스트 저장"""

    # 실패한 테스트 패턴 추출
    import re

    failed_tests = []
    for line in stdout.split('\n'):
        if '✘' in line or 'FAILED' in line:
            failed_tests.append(line.strip())

    # 버그 리스트 파일 생성
    bug_list = {
        'week': 7,
        'timestamp': datetime.now().isoformat(),
        'failed_tests': failed_tests,
        'bug_tickets': []
    }

    with open('.validation/week-7-bugs.json', 'w') as f:
        json.dump(bug_list, f, indent=2)

    print(f"📝 실패 테스트 {len(failed_tests)}개 기록됨")
```

### L3: 버그 티켓 생성
```python
def create_bug_tickets_from_failures(report):
    """실패한 E2E 테스트에서 버그 티켓 자동 생성"""

    failed_specs = []

    for suite in report.get('suites', []):
        for spec in suite.get('specs', []):
            for test in spec.get('tests', []):
                for result in test.get('results', []):
                    if result.get('status') == 'failed':
                        failed_specs.append({
                            'title': test.get('title'),
                            'file': spec.get('file'),
                            'error': result.get('error', {}).get('message', 'Unknown error')
                        })

    # 버그 티켓 생성
    bug_tickets = []

    for i, spec in enumerate(failed_specs, 1):
        ticket = {
            'id': f'BUG-WEEK7-{i:03d}',
            'title': f"E2E 실패: {spec['title']}",
            'file': spec['file'],
            'error': spec['error'],
            'severity': 'HIGH',
            'assigned_to': determine_assignee(spec['file']),
            'created': datetime.now().isoformat(),
            'status': 'OPEN'
        }

        bug_tickets.append(ticket)

        print(f"🐛 {ticket['id']}: {ticket['title']}")

    # 버그 리스트 저장
    with open('.validation/week-7-bug-tickets.json', 'w') as f:
        json.dump(bug_tickets, f, indent=2)

    # Slack 알림
    notify_slack(f"""
    🐛 Week 7 E2E 테스트 실패: {len(bug_tickets)}개 버그 발견

    버그 티켓:
    {chr(10).join([f"  • {t['id']}: {t['title']}" for t in bug_tickets[:5]])}

    전체 리스트: .validation/week-7-bug-tickets.json

    @team Week 8에 모두 수정 필요
    """)

def determine_assignee(test_file):
    """테스트 파일 경로로 담당자 자동 배정"""

    if 'search-flow' in test_file:
        return 'David'  # M4 RAG Search
    elif 'video-preview' in test_file:
        return 'Bob'    # M2 Video Metadata
    elif 'timecode-validation' in test_file:
        return 'Charlie'  # M3 Timecode
    elif 'clipping' in test_file:
        return 'Eve'    # M5 Clipping
    elif 'download' in test_file:
        return 'Eve'    # M5 Clipping
    else:
        return 'Frank'  # M6 Web UI
```

---

## 📋 Week 8 검증 체크리스트

### L0: Week 7 통과 확인
```python
def check_week8_prerequisites():
    """Week 7 통과 확인"""

    week7_result = read_validation_status('week-7')
    assert week7_result['passed'], "Week 7 미통과"

    # 버그 티켓 확인
    bug_file = '.validation/week-7-bug-tickets.json'

    if os.path.exists(bug_file):
        with open(bug_file) as f:
            bugs = json.load(f)

        open_bugs = [b for b in bugs if b['status'] == 'OPEN']

        print(f"📝 Week 7 버그: {len(bugs)}개 (미해결: {len(open_bugs)}개)")

        # Week 8 시작 전 버그 리스트 확인만 (모두 해결 필요 없음)
        return True

    return True
```

### L1: 버그 수정 완료 확인
```python
def check_bug_fixes_week8():
    """Week 8 버그 수정 완료 확인"""

    bug_file = '.validation/week-7-bug-tickets.json'

    if not os.path.exists(bug_file):
        print("✅ 수정할 버그 없음")
        return True

    with open(bug_file) as f:
        bugs = json.load(f)

    open_bugs = [b for b in bugs if b.get('status') == 'OPEN']

    if len(open_bugs) > 0:
        print(f"⚠️ 미해결 버그 {len(open_bugs)}개:")
        for bug in open_bugs[:5]:
            print(f"  • {bug['id']}: {bug['title']}")

        raise AssertionError(f"Week 8 버그 {len(open_bugs)}개 미해결")

    print(f"✅ Week 7 버그 {len(bugs)}개 모두 수정 완료")
    return True
```

### L2: E2E 테스트 100% 통과
```python
def check_e2e_execution_week8():
    """E2E 테스트 실행 (Week 8: 100% 통과 필수)"""

    # Playwright 테스트 실행
    result = subprocess.run(
        ['npx', 'playwright', 'test', '--reporter=json'],
        cwd='m6-web-ui/',
        capture_output=True,
        text=True
    )

    # 결과 파싱
    import re

    stdout = result.stdout

    match = re.search(r'(\d+) passed', stdout)
    passed = int(match.group(1)) if match else 0

    match = re.search(r'(\d+) failed', stdout)
    failed = int(match.group(1)) if match else 0

    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n📊 E2E 테스트 결과 (Week 8)")
    print(f"  • 통과: {passed}/{total} ({pass_rate:.1f}%)")
    print(f"  • 실패: {failed}/{total}")

    # Week 8: 100% 통과 필수
    assert failed == 0, f"E2E 테스트 {failed}개 실패 (100% 통과 필요)"

    print(f"✅ E2E 테스트 100% 통과 ({passed}/{passed})")

    # 성공 시 버그 티켓 파일 아카이브
    if os.path.exists('.validation/week-7-bug-tickets.json'):
        os.rename(
            '.validation/week-7-bug-tickets.json',
            f'.validation/archive/week-7-bugs-resolved-{datetime.now().strftime("%Y%m%d")}.json'
        )

    return True
```

### L3: Performance 테스트
```python
def check_performance_week8():
    """Performance 테스트"""

    # 1. API 응답 시간 테스트
    import requests
    import time

    services = {
        'M3': get_service_url('timecode-validation-service'),
        'M4': get_service_url('rag-search-service'),
        'M5': get_service_url('clipping-service'),
    }

    performance_results = {}

    for module, url in services.items():
        # Health check 응답 시간 (p95 < 500ms)
        response_times = []

        for _ in range(10):
            start = time.time()
            response = requests.get(f"{url}/health")
            elapsed = (time.time() - start) * 1000  # ms

            assert response.status_code == 200
            response_times.append(elapsed)

        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        avg = sum(response_times) / len(response_times)

        performance_results[module] = {
            'avg_ms': round(avg, 1),
            'p95_ms': round(p95, 1)
        }

        # P95 < 500ms 검증
        assert p95 < 500, f"{module} Health Check 느림: {p95:.1f}ms (500ms 미만 필요)"

        print(f"✅ {module} Health Check: avg {avg:.1f}ms, p95 {p95:.1f}ms")

    # 2. 검색 성능 테스트 (M4)
    search_times = []

    for _ in range(5):
        start = time.time()
        response = requests.post(f"{services['M4']}/v1/search", json={
            "query": "2024 WSOP Main Event",
            "top_k": 10
        })
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        search_times.append(elapsed)

    avg_search = sum(search_times) / len(search_times)
    assert avg_search < 2000, f"검색 느림: {avg_search:.1f}ms (2초 미만 필요)"

    print(f"✅ M4 검색 성능: avg {avg_search:.1f}ms")

    # Performance 리포트 저장
    save_performance_report(performance_results)

    return True
```

### L4: Production 배포 준비
```python
def check_production_readiness_week8():
    """Production 배포 준비 확인"""

    # 1. 환경 변수 확인 (모두 production)
    env_files = [
        ('m1-data-ingestion/.env', 'Alice'),
        ('m2-video-metadata/.env', 'Bob'),
        ('m3-timecode-validation/.env', 'Charlie'),
        ('m4-rag-search/.env', 'David'),
        ('m5-clipping/.env', 'Eve'),
        ('m6-web-ui/.env.production', 'Frank'),
    ]

    for env_file, owner in env_files:
        if not os.path.exists(env_file):
            print(f"⚠️ {env_file} 파일 누락 ({owner})")
            continue

        with open(env_file) as f:
            content = f.read()

        # Production 설정 확인
        checks = {
            'POKER_ENV': 'POKER_ENV=production' in content or 'NEXT_PUBLIC_ENV=production' in content,
            'No Mock': 'mock' not in content.lower() and 'localhost' not in content.lower(),
        }

        for check_name, check_result in checks.items():
            assert check_result, f"{env_file}: {check_name} 확인 필요"

        print(f"✅ {env_file} Production 설정 확인")

    # 2. 문서화 확인
    required_docs = [
        'README.md',
        'docs/deployment-guide.md',
        'docs/monitoring-guide.md',
        'docs/troubleshooting-guide.md',
    ]

    for doc in required_docs:
        assert os.path.exists(doc), f"문서 누락: {doc}"
        assert count_lines(doc) > 30, f"{doc} 문서화 부족"

    print("✅ Production 배포 준비 완료")
    return True
```

---

## 🔄 자동 재시도 로직

```python
def validate_week7_with_retry(max_attempts=3):
    """Week 7 검증 (재시도 포함)"""

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"\n🔍 Week 7 (E2E 80%) 검증 시도 {attempt}/{max_attempts}...")

            check_week7_prerequisites()
            check_e2e_implementation()
            check_e2e_execution_week7()  # 80% 통과 필요

            print("✅ Week 7 검증 통과!")
            save_validation_result('week-7', passed=True)

            notify_slack("""
            ✅ Week 7 검증 통과!

            • E2E 테스트: 80% 이상 통과
            • 버그 티켓: 자동 생성 완료

            🎯 다음: Week 8 (버그 수정 + E2E 100% 통과)
            """)

            return True

        except AssertionError as e:
            print(f"❌ 검증 실패: {e}")

            if attempt < max_attempts:
                wait_time = 10 * attempt
                print(f"⏳ {wait_time}분 대기 후 재시도...")
                time.sleep(wait_time * 60)
            else:
                escalate_to_pm(
                    subject="Week 7 (E2E 80%) 검증 실패",
                    error=str(e),
                    severity='HIGH'
                )
                save_validation_result('week-7', passed=False, error=str(e))
                return False

    return False

def validate_week8_with_retry(max_attempts=3):
    """Week 8 검증 (재시도 포함)"""

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"\n🔍 Week 8 (E2E 100% + Bug Fix) 검증 시도 {attempt}/{max_attempts}...")

            check_week8_prerequisites()
            check_bug_fixes_week8()
            check_e2e_execution_week8()  # 100% 통과 필수
            check_performance_week8()
            check_production_readiness_week8()

            print("✅ Week 8 검증 통과!")
            save_validation_result('week-8', passed=True)

            notify_slack("""
            ✅ Week 8 검증 통과!

            • 버그 수정: 100% 완료
            • E2E 테스트: 100% 통과
            • Performance: 통과
            • Production 배포 준비: 완료

            🎯 다음: Week 9 (Production 배포)
            """)

            return True

        except AssertionError as e:
            print(f"❌ 검증 실패: {e}")

            if attempt < max_attempts:
                # 자동 수정 시도 (E2E 재실행 등)
                if "E2E 테스트" in str(e):
                    print("🔧 E2E 테스트 재실행...")
                    # 재시도

                wait_time = 15 * attempt
                print(f"⏳ {wait_time}분 대기 후 재시도...")
                time.sleep(wait_time * 60)
            else:
                escalate_to_pm(
                    subject="Week 8 (E2E 100%) 검증 실패",
                    error=str(e),
                    severity='CRITICAL'
                )
                save_validation_result('week-8', passed=False, error=str(e))
                return False

    return False
```

---

**에이전트 버전**: 1.0.0
**검증 대상**: Week 7 (E2E 80%) + Week 8 (E2E 100% + Bug Fix)
**중요도**: Critical (Production 배포 전 최종 품질 게이트)
**자동 재시도**: 최대 3회
**에스컬레이션**: PM (E2E 통과율 미달 시)
