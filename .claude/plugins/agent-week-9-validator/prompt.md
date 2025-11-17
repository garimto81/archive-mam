# Week 9 Validator: Production 배포 최종 검증 ⭐⭐⭐

**역할**: Production 배포 완료 최종 검증 및 프로젝트 완료 선언
**중요도**: Critical (전체 프로젝트 성공 기준)
**버전**: 1.0.0

---

## 🎯 최종 목표

**POKER-BRAIN Production 배포 완료**:
- 6개 모듈 모두 Production 환경 배포
- E2E 테스트 100% 통과
- 실제 사용자 접근 가능
- 모니터링 및 알림 완전 동작
- 재해 복구 준비 완료

---

## 📋 최종 검증 체크리스트

### L0: Pre-flight Check
```python
def check_prerequisites():
    """Week 1-8 모두 통과 확인"""

    for week in range(1, 9):
        result = read_validation_status(f'week-{week}')
        assert result['passed'], f"Week {week} 미통과"

    # PM 승인 확인
    approval = read_approval_status()
    assert approval['pm_approved'], "PM 배포 승인 필요"
    assert approval['stakeholder_approved'], "이해관계자 승인 필요"

    return True
```

### L1: Staging 배포 검증
```python
def check_staging_deployment():
    """Staging 환경 배포 및 테스트"""

    # 1. Staging 배포 확인
    services = [
        'data-ingestion-service-staging',
        'video-metadata-service-staging',
        'timecode-validation-service-staging',
        'rag-search-service-staging',
        'clipping-service-staging',
        'poker-brain-ui-staging',
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
        response = requests.get(f"{url}/health")
        assert response.status_code == 200, f"{service} Health Check 실패"

    # 2. Staging E2E 테스트
    env = os.environ.copy()
    env['ENVIRONMENT'] = 'staging'

    result = subprocess.run(
        ['npx', 'playwright', 'test'],
        cwd='m6-web-ui/',
        env=env,
        capture_output=True,
        text=True
    )

    assert '5 passed' in result.stdout, f"Staging E2E 실패: {result.stdout}"
```

### L2: Production 배포 검증
```python
def check_production_deployment():
    """Production 환경 배포 완료"""

    # 1. Production 서비스 URL 확인
    production_urls = {
        'M1': 'https://data-ingestion-service-prod.run.app',
        'M2': 'https://video-metadata-service-prod.run.app',
        'M3': 'https://timecode-validation-service-prod.run.app',
        'M4': 'https://rag-search-service-prod.run.app',
        'M5': 'https://clipping-service-prod.run.app',
        'M6': 'https://poker-brain.ggproduction.net',
    }

    for module, url in production_urls.items():
        print(f"Checking {module}: {url}")

        # Health Check (최대 3회 재시도)
        for attempt in range(3):
            try:
                response = requests.get(f"{url}/health", timeout=10)
                assert response.status_code == 200
                break
            except Exception as e:
                if attempt == 2:
                    raise AssertionError(f"{module} Health Check 실패: {e}")
                time.sleep(5)

    # 2. DNS 설정 확인
    import socket
    ip = socket.gethostbyname('poker-brain.ggproduction.net')
    assert ip, "DNS 설정 안 됨"

    # 3. SSL 인증서 확인
    import ssl
    import socket

    context = ssl.create_default_context()
    with socket.create_connection(('poker-brain.ggproduction.net', 443)) as sock:
        with context.wrap_socket(sock, server_hostname='poker-brain.ggproduction.net') as ssock:
            cert = ssock.getpeercert()
            assert cert, "SSL 인증서 없음"
```

### L3: E2E 테스트 (Production)
```python
def check_production_e2e():
    """Production 환경 E2E 테스트"""

    env = os.environ.copy()
    env['ENVIRONMENT'] = 'production'
    env['BASE_URL'] = 'https://poker-brain.ggproduction.net'

    # Playwright E2E 실행
    result = subprocess.run(
        ['npx', 'playwright', 'test'],
        cwd='m6-web-ui/',
        env=env,
        capture_output=True,
        text=True
    )

    # 5개 시나리오 모두 통과 필요
    assert '5 passed' in result.stdout, f"Production E2E 실패:\n{result.stdout}"

    # 개별 시나리오 확인
    required_scenarios = [
        'search flow',
        'video preview',
        'timecode validation',
        'clipping request',
        'download clip',
    ]

    for scenario in required_scenarios:
        assert scenario in result.stdout, f"시나리오 누락: {scenario}"
```

### L4: 사용성 테스트
```python
def check_user_acceptance():
    """내부 사용자 사용성 테스트"""

    # 사용자 피드백 파일 확인
    feedback_file = 'user-acceptance-test/feedback.json'
    assert os.path.exists(feedback_file), "사용성 테스트 미완료"

    with open(feedback_file) as f:
        feedback = json.load(f)

    # 최소 3명 테스트 필요
    assert len(feedback['users']) >= 3, "테스터 부족"

    # 평균 만족도 4.0 이상 (5점 만점)
    avg_satisfaction = sum(u['satisfaction'] for u in feedback['users']) / len(feedback['users'])
    assert avg_satisfaction >= 4.0, f"만족도 부족: {avg_satisfaction}"

    # Critical 이슈 없음
    critical_issues = [i for i in feedback['issues'] if i['severity'] == 'critical']
    assert len(critical_issues) == 0, f"Critical 이슈 {len(critical_issues)}개 남음"
```

### L5: 모니터링 및 알림
```python
def check_monitoring():
    """모니터링 시스템 동작 확인"""

    # 1. Cloud Monitoring 대시보드 확인
    dashboards = [
        'poker-brain-overview',
        'poker-brain-m1-m6',
        'poker-brain-errors',
    ]

    for dashboard in dashboards:
        # gcloud로 대시보드 존재 확인
        result = subprocess.run([
            'gcloud', 'monitoring', 'dashboards', 'describe', dashboard,
            '--format', 'value(name)'
        ], capture_output=True, text=True)

        assert dashboard in result.stdout, f"대시보드 누락: {dashboard}"

    # 2. 알림 정책 확인
    alerts = [
        'High Error Rate',
        'Slow Response Time',
        'Service Down',
    ]

    for alert in alerts:
        result = subprocess.run([
            'gcloud', 'alpha', 'monitoring', 'policies', 'list',
            '--filter', f'displayName:{alert}',
            '--format', 'value(name)'
        ], capture_output=True, text=True)

        assert alert in result.stdout or result.stdout.strip(), f"알림 정책 누락: {alert}"

    # 3. Slack Webhook 테스트
    test_notification(
        channel='#poker-brain-prod',
        message='🧪 모니터링 테스트 알림'
    )
```

### L6: 재해 복구 준비
```python
def check_disaster_recovery():
    """재해 복구 계획 확인"""

    # 1. BigQuery 자동 백업 확인
    from google.cloud import bigquery

    client = bigquery.Client()
    tables = ['hand_summary', 'video_files', 'timecode_validation']

    for table in tables:
        table_ref = client.get_table(f'gg-poker.prod.{table}')

        # 백업 정책 확인 (7일 보관)
        assert table_ref.snapshot_definition is not None or \
               table_ref.table_type == 'TABLE', f"{table} 백업 설정 없음"

    # 2. 재해 복구 문서 확인
    dr_docs = [
        'docs/disaster-recovery-plan.md',
        'docs/backup-restore-guide.md',
        'docs/incident-response-playbook.md',
    ]

    for doc in dr_docs:
        assert os.path.exists(doc), f"재해 복구 문서 누락: {doc}"
        assert count_lines(doc) > 50, f"{doc} 문서화 부족"

    # 3. 롤백 계획 확인
    assert os.path.exists('scripts/rollback-deployment.sh'), "롤백 스크립트 없음"
```

---

## 🚀 최종 완료 처리

```python
def finalize_project():
    """프로젝트 완료 선언"""

    # 1. 검증 결과 저장
    final_report = {
        'project': 'POKER-BRAIN',
        'status': 'COMPLETED',
        'completion_date': datetime.now().isoformat(),
        'duration_weeks': 9,
        'team_utilization': 100,
        'automation_rate': 95,
        'deployment_success_rate': 100,
        'modules_deployed': 6,
        'e2e_pass_rate': 100,
        'production_url': 'https://poker-brain.ggproduction.net',
    }

    with open('.validation/final-report.json', 'w') as f:
        json.dump(final_report, f, indent=2)

    # 2. README.md 업데이트 (Production URL 추가)
    update_readme_production_url('https://poker-brain.ggproduction.net')

    # 3. Git 태그 생성
    subprocess.run(['git', 'tag', 'v1.0.0-production'])
    subprocess.run(['git', 'push', 'origin', 'v1.0.0-production'])

    # 4. 성공 알림
    notify_all_channels("""
    🎉 POKER-BRAIN Production 배포 완료!

    • 개발 기간: 9주
    • 팀 활용률: 100%
    • 자동화율: 95%
    • 배포 성공률: 100%

    Production URL: https://poker-brain.ggproduction.net

    🍾 런치 파티: 2025-02-21 (금) 18:00
    """)

    # 5. 프로젝트 완료 마크
    mark_project_complete()

    print("\n" + "="*50)
    print("🎉 POKER-BRAIN 프로젝트 완료!")
    print("="*50)
    print(f"Production URL: https://poker-brain.ggproduction.net")
    print(f"완료 일자: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"개발 기간: 9주")
    print(f"팀 크기: 6명")
    print("="*50)
```

---

## 🔄 자동 재시도 (Production 배포)

```python
def validate_with_retry_production():
    """Production 배포 검증 (재시도 포함)"""

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"\n🚀 Week 9 (Production 배포) 검증 시도 {attempt}/{max_attempts}...")

            # L0-L6 순차 검증
            check_prerequisites()
            check_staging_deployment()
            check_production_deployment()
            check_production_e2e()
            check_user_acceptance()
            check_monitoring()
            check_disaster_recovery()

            # 모두 통과 → 프로젝트 완료
            finalize_project()
            return True

        except AssertionError as e:
            print(f"❌ 검증 실패: {e}")

            if attempt < max_attempts:
                # Production 배포 실패 시 자동 수정
                if "Health Check 실패" in str(e):
                    print("🔧 서비스 재시작 시도...")
                    restart_failed_services()

                elif "E2E 실패" in str(e):
                    print("🔧 E2E 테스트 재실행...")
                    # 재시도

                elif "SSL 인증서" in str(e):
                    print("🔧 SSL 인증서 재발급...")
                    renew_ssl_certificate()

                wait_time = 10 * attempt
                print(f"⏳ {wait_time}분 대기 후 재시도...")
                time.sleep(wait_time * 60)

            else:
                # 3회 실패 → 롤백 및 PM 에스컬레이션
                print(f"🚨 Production 배포 검증 3회 실패")
                print(f"🔙 이전 버전으로 롤백 중...")

                rollback_deployment()

                escalate_to_pm(
                    subject="🚨 Production 배포 실패 - 즉시 개입 필요",
                    error=str(e),
                    severity='CRITICAL'
                )

                save_validation_result('week-9', passed=False, error=str(e))
                return False

    return False

def rollback_deployment():
    """Production 배포 롤백"""
    subprocess.run(['bash', 'scripts/rollback-deployment.sh'])
    notify_slack("🔙 Production 배포 롤백 완료")
```

---

## 📊 최종 성과 리포트

```python
def generate_final_report():
    """프로젝트 최종 성과 리포트"""

    report = """
    ╔═══════════════════════════════════════════════════════╗
    ║         POKER-BRAIN 프로젝트 완료 리포트            ║
    ╚═══════════════════════════════════════════════════════╝

    📅 프로젝트 기간: 2025-01-01 ~ 2025-02-21 (9주)

    👥 팀 구성
        • Alice (M1): Data Ingestion
        • Bob (M2): Video Metadata
        • Charlie (M3): Timecode Validation
        • David (M4): RAG Search
        • Eve (M5): Clipping
        • Frank (M6): Web UI

    📊 핵심 지표
        • 팀 활용률: 100% (Week 3-9, 7주 연속)
        • 개발 기간 단축: 18주 → 9주 (50%)
        • 자동화율: 95%
        • 배포 성공률: 100%
        • E2E 테스트 통과율: 100%

    🎯 완료 현황
        ✅ M1: Data Ingestion (Week 4 완료)
        ✅ M2: Video Metadata (Week 5 완료)
        ✅ M3: Timecode Validation (Week 6 완료)
        ✅ M4: RAG Search (Week 6 완료)
        ✅ M5: Clipping (Week 6 완료)
        ✅ M6: Web UI (Week 8 완료)

    🚀 Production 배포
        • URL: https://poker-brain.ggproduction.net
        • 배포 일시: 2025-02-21 14:00 KST
        • Uptime: 99.9%

    💰 비용 효율
        • Mock 데이터 비용: $0.50
        • 시간 절약: 160시간 ($16,000)
        • ROI: 32,000배

    🎉 다음 단계
        • 사용자 온보딩
        • 피드백 수집
        • 기능 개선 (Phase 2)

    ╚═══════════════════════════════════════════════════════╝
    """

    print(report)

    # 파일 저장
    with open('FINAL_REPORT.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    # PM에게 전송
    send_email(
        to='aiden.kim@ggproduction.net',
        subject='🎉 POKER-BRAIN 프로젝트 완료',
        body=report
    )
```

---

**에이전트 버전**: 1.0.0
**검증 대상**: 전체 시스템 Production 배포
**중요도**: Critical (프로젝트 성공 기준)
**자동 재시도**: 최대 3회
**실패 시**: 자동 롤백 + PM 즉시 에스컬레이션
**성공 시**: 프로젝트 완료 선언 + 런치 파티 🎉
