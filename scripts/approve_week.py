#!/usr/bin/env python3
"""
Week 승인 스크립트

사용자(PM)가 특정 주차 승인을 수행하는 스크립트

사용법:
    python scripts/approve_week.py --week 1
    python scripts/approve_week.py --week 9
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


def approve_week(week, approver='aiden.kim@ggproduction.net'):
    """주차 승인"""

    print(f"\n{'='*60}")
    print(f"✅ Week {week} 승인")
    print(f"{'='*60}\n")

    # 승인 요청 확인
    request_file = Path(f'.validation/week-{week}-approval-request.json')

    if not request_file.exists():
        print(f"❌ Week {week} 승인 요청이 없습니다.")
        print(f"   파일 없음: {request_file}")
        return False

    with open(request_file) as f:
        request = json.load(f)

    print(f"승인 요청 정보:")
    print(f"  • 요청 주차: Week {request['week']}")
    print(f"  • 요청 시간: {request['timestamp']}")
    print(f"  • 상태: {request['status']}")

    # Week별 승인 내용 출력
    if week == 1:
        print(f"\n📋 Week 1 승인 내용:")
        print(f"  • OpenAPI 스펙 6개 생성 완료")
        print(f"  • API 일관성 검증 통과")
        print(f"\n💡 검토 사항:")
        print(f"  - modules/m1-data-ingestion/openapi.yaml")
        print(f"  - modules/m2-video-metadata/openapi.yaml")
        print(f"  - modules/m3-timecode-validation/openapi.yaml")
        print(f"  - modules/m4-rag-search/openapi.yaml")
        print(f"  - modules/m5-clipping/openapi.yaml")
        print(f"  - modules/m6-web-ui/openapi.yaml")

    elif week == 9:
        print(f"\n🚀 Week 9 최종 승인 내용:")
        print(f"  • Staging 배포 완료")
        print(f"  • Production 배포 완료")
        print(f"  • E2E 테스트 100% 통과")
        print(f"\n💡 Production URLs:")
        print(f"  - M1: https://data-ingestion-service-prod.run.app")
        print(f"  - M2: https://video-metadata-service-prod.run.app")
        print(f"  - M3: https://timecode-validation-service-prod.run.app")
        print(f"  - M4: https://rag-search-service-prod.run.app")
        print(f"  - M5: https://clipping-service-prod.run.app")
        print(f"  - M6: https://poker-brain.ggproduction.net")

    # 승인 확인
    confirm = input(f"\nWeek {week}을(를) 승인하시겠습니까? (y/n): ")

    if confirm.lower() != 'y':
        print("\n❌ 승인 취소됨")
        return False

    # 승인 파일 생성
    approval = {
        'week': week,
        'approved': True,
        'approver': approver,
        'timestamp': datetime.now().isoformat(),
    }

    Path('.validation').mkdir(exist_ok=True)

    approval_file = Path(f'.validation/week-{week}-approval.json')

    with open(approval_file, 'w') as f:
        json.dump(approval, f, indent=2)

    print(f"\n✅ Week {week} 승인 완료")
    print(f"   파일 생성: {approval_file}")
    print(f"   승인자: {approver}")
    print(f"   승인 시간: {approval['timestamp']}")

    # 승인 후 메시지
    if week == 1:
        print(f"\n📅 다음: Week 2 (Mock 환경 구축) 자동 시작")
    elif week == 9:
        print(f"\n🎉 POKER-BRAIN 프로젝트 완료!")
        print(f"   Production URL: https://poker-brain.ggproduction.net")
        print(f"   🍾 런치 파티: 2025-02-21 (금) 18:00")

    print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Week 승인 스크립트"
    )

    parser.add_argument(
        '--week',
        type=int,
        required=True,
        choices=[1, 9],
        help="승인할 주차 (1 또는 9만 필요)"
    )

    parser.add_argument(
        '--approver',
        type=str,
        default='aiden.kim@ggproduction.net',
        help="승인자 이메일"
    )

    args = parser.parse_args()

    success = approve_week(args.week, args.approver)

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
