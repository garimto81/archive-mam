#!/usr/bin/env python3
"""
Weekly Validator Runner

주차별 검증 에이전트를 실행하는 스크립트.
GitHub Actions 또는 로컬에서 실행 가능.

사용법:
    python scripts/run_weekly_validator.py --week 1-2 --max-attempts 3
    python scripts/run_weekly_validator.py --week 4
    python scripts/run_weekly_validator.py --week all
"""

import argparse
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_validator_module(week):
    """주차별 검증 모듈 로드"""

    validators = {
        '1-2': 'validators.week_1_2_validator',
        '4': 'validators.week_4_validator',
        '5': 'validators.week_5_validator',
        '7-8': 'validators.week_7_8_validator',
        '9': 'validators.week_9_validator',
    }

    if week not in validators:
        raise ValueError(f"Unknown week: {week}")

    module_name = validators[week]

    try:
        import importlib
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        print(f"❌ Failed to import validator module: {module_name}")
        print(f"   Error: {e}")
        return None


def run_validation(week, max_attempts=3):
    """주차별 검증 실행"""

    print(f"\n{'='*60}")
    print(f"🔍 Week {week} 검증 시작")
    print(f"{'='*60}\n")

    # 검증 모듈 로드
    validator = load_validator_module(week)

    if validator is None:
        print(f"❌ Week {week} 검증 모듈을 찾을 수 없습니다.")
        return False

    # 검증 함수 실행
    if hasattr(validator, 'validate_with_retry'):
        # 재시도 로직 포함 검증
        result = validator.validate_with_retry(max_attempts=max_attempts)
    elif hasattr(validator, 'validate'):
        # 기본 검증
        result = validator.validate()
    else:
        print(f"❌ Week {week} 검증 함수가 없습니다.")
        return False

    # 결과 저장
    save_validation_result(week, result)

    return result


def save_validation_result(week, passed, error=None):
    """검증 결과 JSON 파일로 저장"""

    result = {
        'week': week,
        'passed': passed,
        'timestamp': datetime.now().isoformat(),
        'error': error,
    }

    # .validation 디렉토리 생성
    validation_dir = Path('.validation')
    validation_dir.mkdir(exist_ok=True)

    # 결과 파일 저장
    result_file = validation_dir / f'week-{week}-result.json'

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n📄 검증 결과 저장: {result_file}")

    return result_file


def run_all_weeks(max_attempts=3):
    """전체 주차 순차 검증 (Week 1-9)"""

    print("\n" + "="*60)
    print("🚀 POKER-BRAIN 전체 자동화 워크플로우 시작")
    print("="*60 + "\n")

    weeks = ['1-2', '4', '5', '7-8', '9']
    results = {}

    for week in weeks:
        print(f"\n📅 Week {week} 검증 중...")

        # 검증 실행
        success = run_validation(week, max_attempts)
        results[week] = success

        if not success:
            print(f"\n❌ Week {week} 검증 실패 - 워크플로우 중단")
            break

        print(f"\n✅ Week {week} 검증 통과")

    # 최종 요약
    print("\n" + "="*60)
    print("📊 검증 결과 요약")
    print("="*60)

    for week, success in results.items():
        status = "✅ 통과" if success else "❌ 실패"
        print(f"  Week {week}: {status}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)

    print(f"\n전체: {passed}/{total} 주차 통과 ({passed/total*100:.1f}%)")

    return all(results.values())


def main():
    parser = argparse.ArgumentParser(
        description="POKER-BRAIN 주차별 검증 실행"
    )

    parser.add_argument(
        '--week',
        type=str,
        choices=['1-2', '4', '5', '7-8', '9', 'all'],
        required=True,
        help="검증할 주차 (예: 1-2, 4, 5, 7-8, 9, all)"
    )

    parser.add_argument(
        '--max-attempts',
        type=int,
        default=3,
        help="최대 재시도 횟수 (기본: 3)"
    )

    args = parser.parse_args()

    # 검증 실행
    start_time = time.time()

    if args.week == 'all':
        success = run_all_weeks(max_attempts=args.max_attempts)
    else:
        success = run_validation(args.week, max_attempts=args.max_attempts)

    elapsed = time.time() - start_time

    # 최종 결과
    print(f"\n" + "="*60)

    if success:
        print("✅ 검증 성공!")
    else:
        print("❌ 검증 실패!")

    print(f"소요 시간: {elapsed:.1f}초")
    print("="*60 + "\n")

    # Exit code 설정 (GitHub Actions용)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
