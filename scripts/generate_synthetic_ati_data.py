"""
ATI 메타데이터 합성 데이터 생성 스크립트

Purpose:
- PoC용 100개 포커 핸드 메타데이터 생성
- 실제 ATI 데이터와 유사한 구조와 다양성 제공
- JSON Schema (ati_metadata_schema.json) 준수

Usage:
    python scripts/generate_synthetic_ati_data.py --count 100 --output mock_data/

Generated Files:
    - mock_data/ati_metadata_001.json
    - mock_data/ati_metadata_002.json
    - ...
    - mock_data/ati_metadata_100.json
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import argparse
from typing import List, Dict


# 실제 프로 포커 플레이어 이름 (다양성 확보)
PLAYERS = [
    "Phil Ivey", "Daniel Negreanu", "Doug Polk", "Tom Dwan", "Fedor Holz",
    "Jason Koon", "Justin Bonomo", "Bryn Kenney", "Stephen Chidwick",
    "Alex Foxen", "David Peters", "Mikki Mase", "Garrett Adelstein",
    "Eric Persson", "Wesley Fei", "Patrik Antonius", "Junglemann",
    "Nik Airball", "Andrew Robl", "Phil Hellmuth", "Vanessa Selbst",
    "Maria Ho", "Liv Boeree", "Kristen Bicknell", "Vanessa Kade"
]

# 토너먼트 목록
TOURNAMENTS = [
    "wsop_2024", "wsop_2023", "mpp_2024", "mpp_2023",
    "apl_2024", "hustler_casino_live_2024", "triton_poker_2024"
]

# 포지션
POSITIONS = ["BTN", "SB", "BB", "UTG", "UTG1", "MP", "CO"]

# 스트릿
STREETS = ["PREFLOP", "FLOP", "TURN", "RIVER"]

# 핸드 타입과 대응 태그
HAND_TYPES = {
    "HERO_CALL": ["HERO_CALL", "RIVER_DECISION", "SICK_CALL"],
    "BLUFF": ["BLUFF", "RIVER_DECISION", "HIGH_STAKES"],
    "VALUE_BET": ["VALUE_BET", "RIVER_DECISION"],
    "HERO_FOLD": ["HERO_FOLD", "SICK_FOLD", "RIVER_DECISION"],
    "ALL_IN": ["ALL_IN", "HIGH_STAKES"],
    "SLOW_PLAY": ["SLOW_PLAY", "TRAP"]
}

# 추가 태그 풀
EXTRA_TAGS = [
    "DEEP_STACK", "SHORT_STACK", "CONTINUATION_BET", "CHECK_RAISE",
    "DONK_BET", "SQUEEZE", "3BET", "4BET", "COOLER", "BAD_BEAT", "TILT"
]

# 액션 시퀀스 템플릿
ACTION_TEMPLATES = {
    "HERO_CALL": [
        ["raise 2.5bb", "call", "check", "bet 0.33pot", "call",
         "check", "bet 0.5pot", "call", "check", "bet 0.8pot", "tank 180s", "call"],
        ["raise 3bb", "3bet 9bb", "call", "check", "bet 0.5pot", "call",
         "check", "bet 0.75pot", "call", "check", "all-in", "tank 240s", "call"]
    ],
    "BLUFF": [
        ["raise 2.5bb", "call", "check", "bet 0.5pot", "call",
         "check", "bet 0.75pot", "call", "check", "all-in", "fold"],
        ["raise 3bb", "call", "bet 0.33pot", "call", "bet 0.5pot",
         "call", "all-in", "tank 120s", "fold"]
    ],
    "ALL_IN": [
        ["raise 3bb", "3bet 9bb", "4bet 24bb", "all-in", "call"],
        ["limp", "raise 5bb", "call", "check", "bet 0.5pot", "raise 2x", "all-in", "call"]
    ]
}

# 설명 템플릿
DESCRIPTION_TEMPLATES = {
    "HERO_CALL": [
        "{hero} makes an insane {street} call with {hand_strength} against {villain}'s {action}. After {villain} bets {bet_size}bb into a {pot_before}bb pot on the {street}, {hero} tanks for {tank_time} and makes the hero call with {hand_strength}. {villain} shows {villain_hand} and {hero} wins a massive {final_pot}bb pot.",
        "{hero} makes a sick {street} call against {villain}. {villain} fires {num_barrels} barrels and shoves {bet_size}bb on the {street}. {hero} thinks for {tank_time} and calls with just {hand_strength}. {villain} was bluffing with {villain_hand} and {hero} scoops a {final_pot}bb pot."
    ],
    "BLUFF": [
        "{hero} attempts a bold {street} bluff against {villain}. After {villain} checks, {hero} fires {bet_size}bb into a {pot_before}bb pot. {villain} tanks for {tank_time} and makes the hero fold with {villain_hand}. {hero} shows {hero_hand} bluff and {villain} wins {final_pot}bb.",
        "{hero} triple barrels against {villain} with {hero_hand}. On the {street}, {hero} shoves {bet_size}bb. {villain} thinks for {tank_time} and folds {villain_hand}. {hero} takes down a {final_pot}bb pot with pure air."
    ],
    "ALL_IN": [
        "{hero} goes all-in for {bet_size}bb on the {street} against {villain}. {villain} has {villain_hand} and {decision}. {result} and {winner} wins a {final_pot}bb pot.",
        "Massive all-in pot! {hero} shoves {bet_size}bb with {hero_hand} against {villain}'s {villain_hand} on the {street}. {villain} {decision} and {result}. Final pot: {final_pot}bb."
    ]
}


def generate_hand_metadata(hand_number: int, tournament: str) -> Dict:
    """단일 핸드 메타데이터 생성"""

    # 핸드 타입 랜덤 선택
    hand_type = random.choice(list(HAND_TYPES.keys()))

    # Hero/Villain 선택
    hero = random.choice(PLAYERS)
    villain = random.choice([p for p in PLAYERS if p != hero])

    # 포지션
    hero_pos = random.choice(POSITIONS)
    villain_pos = random.choice([p for p in POSITIONS if p != hero_pos])

    # 스택 크기 (bb)
    hero_stack = round(random.uniform(30, 500), 1)
    villain_stack = round(random.uniform(30, 500), 1)

    # 스트릿
    street = random.choice(STREETS)

    # 팟 사이즈
    final_pot = round(random.uniform(20, 800), 1)
    pot_before = round(final_pot * random.uniform(0.3, 0.7), 1)
    bet_size = round(final_pot - pot_before, 1)

    # 액션 시퀀스
    action_sequence = random.choice(ACTION_TEMPLATES.get(hand_type, [["check", "bet", "call"]]))

    # 태그
    base_tags = HAND_TYPES[hand_type].copy()
    extra_tags = random.sample(EXTRA_TAGS, random.randint(1, 3))
    all_tags = list(set(base_tags + extra_tags))[:10]  # 최대 10개

    # 핸드 강도 표현
    hand_strengths = ["ace-high", "king-high", "queen-high", "top pair", "middle pair",
                     "bottom pair", "two pair", "trips", "straight", "flush", "full house"]
    hero_hand_str = random.choice(hand_strengths)
    villain_hand_str = random.choice(hand_strengths)

    # Result
    result = random.choice(["WIN", "LOSE", "SPLIT"])
    hero_action = random.choice(["call", "fold", "raise", "all-in"])

    # 설명 생성
    template = random.choice(DESCRIPTION_TEMPLATES.get(hand_type, DESCRIPTION_TEMPLATES["HERO_CALL"]))
    description = template.format(
        hero=hero,
        villain=villain,
        street=street.lower(),
        hand_strength=hero_hand_str,
        action="triple barrel bluff" if hand_type == "BLUFF" else "value bet",
        bet_size=bet_size,
        pot_before=pot_before,
        tank_time=f"{random.randint(60, 300)}s",
        villain_hand=f"{villain_hand_str} bluff" if hand_type == "HERO_CALL" else villain_hand_str,
        hero_hand=hero_hand_str,
        final_pot=final_pot,
        num_barrels="three" if len(action_sequence) > 10 else "two",
        decision="calls" if result == "LOSE" else "folds",
        result="Hero wins" if result == "WIN" else "Villain wins",
        winner=hero if result == "WIN" else villain
    )

    # 타임스탬프 (2024년 랜덤 날짜)
    base_date = datetime(2024, 1, 1)
    random_days = random.randint(0, 365)
    timestamp = (base_date + timedelta(days=random_days)).isoformat() + "Z"

    # hand_id 생성
    hand_id = f"{tournament}_hand_{hand_number:04d}"

    # GCS URL
    video_url = f"gs://poker-videos-prod/{tournament}/day{random.randint(1,10)}_table{random.randint(1,20)}.mp4"

    # 메타데이터 객체 생성
    metadata = {
        "hand_id": hand_id,
        "tournament_id": tournament,
        "hand_number": hand_number,
        "timestamp": timestamp,
        "duration_seconds": random.randint(30, 600),
        "description": description,
        "hero_name": hero,
        "villain_name": villain,
        "hero_position": hero_pos,
        "villain_position": villain_pos,
        "hero_stack_bb": hero_stack,
        "villain_stack_bb": villain_stack,
        "street": street,
        "pot_bb": final_pot,
        "action_sequence": action_sequence,
        "hero_action": hero_action,
        "result": result,
        "tags": all_tags,
        "hand_type": hand_type,
        "video_url": video_url,
        "video_start_time": round(random.uniform(0, 10000), 1),
        "video_end_time": round(random.uniform(10001, 20000), 1),
        "thumbnail_url": f"gs://poker-videos-prod/thumbnails/{hand_id}.jpg",
        "ati_version": "1.0.0",
        "ati_confidence": round(random.uniform(0.75, 0.99), 2)
    }

    return metadata


def generate_dataset(count: int, output_dir: str):
    """전체 데이터셋 생성"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"[*] Generating {count} synthetic ATI metadata files...")
    print(f"[*] Output directory: {output_path.absolute()}")

    all_metadata = []

    for i in range(1, count + 1):
        tournament = random.choice(TOURNAMENTS)
        metadata = generate_hand_metadata(i, tournament)

        # 개별 JSON 파일로 저장 (실제 ATI 출력 형식)
        filename = f"ati_metadata_{i:03d}.json"
        filepath = output_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        all_metadata.append(metadata)

        if i % 10 == 0:
            print(f"  [OK] {i}/{count} completed")

    # 전체 데이터를 하나의 JSON으로도 저장 (분석용)
    combined_file = output_path / "all_hands_combined.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Generation complete!")
    print(f"[STATS] Statistics:")
    print(f"  - Total hands: {count}")
    print(f"  - Individual files: {count}")
    print(f"  - Combined file: {combined_file}")

    # 핸드 타입 분포
    hand_type_counts = {}
    for hand in all_metadata:
        ht = hand['hand_type']
        hand_type_counts[ht] = hand_type_counts.get(ht, 0) + 1

    print(f"\n[DISTRIBUTION] Hand type distribution:")
    for hand_type, count in sorted(hand_type_counts.items(), key=lambda x: -x[1]):
        print(f"  - {hand_type}: {count} ({count/len(all_metadata)*100:.1f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ATI Synthetic Data Generator")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of hands to generate (default: 100)")
    parser.add_argument("--output", type=str, default="mock_data/synthetic_ati/",
                       help="Output directory (default: mock_data/synthetic_ati/)")

    args = parser.parse_args()

    generate_dataset(args.count, args.output)

    print(f"\n[NEXT STEPS]:")
    print(f"  1. Upload to GCS bucket:")
    print(f"     gsutil -m cp {args.output}/*.json gs://ati-metadata-dev/")
    print(f"  2. Pub/Sub event auto-triggers")
    print(f"  3. Cloud Functions ETL pipeline runs")
    print(f"  4. Wait for Vertex AI indexing")
    print(f"  5. Start search testing")
