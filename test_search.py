#!/usr/bin/env python3
"""
검색 API 인터랙티브 테스트
v4.0.0
"""

from fastapi.testclient import TestClient
from app.main import app
import json

# TestClient 생성
client = TestClient(app)


def print_separator(title=""):
    """구분선 출력"""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def test_search(query, limit=5):
    """검색 API 테스트"""
    print_separator(f"검색: '{query}'")

    response = client.get(
        "/api/search",
        params={"q": query, "limit": limit}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        print(f"\n총 {data['total']}개 결과 (응답 시간: {data['query_time_ms']}ms)")
        print(f"쿼리: {data['query']}")

        for result in data['results']:
            hand = result['hand']
            print(f"\n[{result['rank']}] {hand['hand_id']} (Score: {result['score']:.3f})")
            print(f"  Players: {hand['hero_name']} vs {hand['villain_name']}")
            print(f"  Pot: {hand['pot_bb']:.1f} BB")
            print(f"  Street: {hand['street']}")
            print(f"  Description: {hand['description'][:150]}...")
            if hand['tags']:
                print(f"  Tags: {', '.join(hand['tags'][:5])}")
    else:
        print(f"\nError: {response.json()}")


def test_hand_detail(hand_id):
    """핸드 상세 조회 테스트"""
    print_separator(f"핸드 상세: {hand_id}")

    response = client.get(f"/api/hands/{hand_id}")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        hand = response.json()

        print(f"\nHand ID: {hand['hand_id']}")
        print(f"Tournament: {hand['tournament_id']}")
        print(f"Players: {hand['hero_name']} vs {hand['villain_name']}")
        print(f"Positions: {hand['hero_position']} vs {hand['villain_position']}")
        print(f"Stacks: {hand['hero_stack_bb']:.1f} BB vs {hand['villain_stack_bb']:.1f} BB")
        print(f"Pot: {hand['pot_bb']:.1f} BB")
        print(f"Street: {hand['street']}")
        print(f"Actions: {' -> '.join(hand['action_sequence'])}")
        print(f"Result: {hand['result']}")
        print(f"\nDescription:")
        print(f"  {hand['description']}")
        print(f"\nVideo: {hand['video_url']}")
        print(f"  Start: {hand['video_start_time']:.1f}s")
        print(f"  End: {hand['video_end_time']:.1f}s")
    else:
        print(f"\nError: {response.json()}")


def interactive_mode():
    """인터랙티브 모드"""
    print_separator("검색 API 인터랙티브 테스트")
    print("\n명령어:")
    print("  search <query>        - 검색 (예: search river call)")
    print("  detail <hand_id>      - 핸드 상세 (예: detail mpp_2023_hand_0006)")
    print("  quit                  - 종료")

    while True:
        print("\n" + "-" * 70)
        cmd = input("명령 입력> ").strip()

        if not cmd:
            continue

        if cmd.lower() in ['quit', 'exit', 'q']:
            print("\n종료합니다.")
            break

        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()

        if command == 'search':
            if len(parts) < 2:
                print("사용법: search <query>")
                continue
            query = parts[1]
            test_search(query)

        elif command == 'detail':
            if len(parts) < 2:
                print("사용법: detail <hand_id>")
                continue
            hand_id = parts[1]
            test_hand_detail(hand_id)

        elif command in ['quit', 'exit', 'q']:
            # 이미 위에서 처리됨
            pass

        else:
            # 알 수 없는 명령 → 자동으로 검색으로 처리
            print(f"'{cmd}' 검색 중...")
            test_search(cmd)


def quick_demo():
    """빠른 데모"""
    print_separator("빠른 데모")

    # 1. 검색 테스트
    test_search("river call", limit=3)

    # 2. 핸드 상세 테스트
    test_hand_detail("mpp_2023_hand_0006")

    print_separator("데모 완료")
    print("\n인터랙티브 모드를 시작하려면 interactive_mode()를 실행하세요.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            quick_demo()
        elif sys.argv[1] == "interactive":
            interactive_mode()
        else:
            print("사용법:")
            print("  python test_search.py demo        - 빠른 데모")
            print("  python test_search.py interactive - 인터랙티브 모드")
    else:
        # 기본: 빠른 데모
        quick_demo()
