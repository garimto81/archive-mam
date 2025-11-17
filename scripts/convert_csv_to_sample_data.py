"""
CSV 핸드 데이터를 POKER-BRAIN 샘플 데이터로 변환

Usage:
    python scripts/convert_csv_to_sample_data.py

Input:
    CSV file from Downloads folder

Output:
    mock_data/bigquery/hand_summary_real.json (M1용)
    mock_data/bigquery/video_files_real.json (M2용 - 가상 생성)
    mock_data/embeddings/hand_embeddings_real.json (M4용 - 가상 생성)
"""

import csv
import json
import random
from datetime import datetime
from typing import List, Dict, Any

# 입력 파일
INPUT_CSV = r'c:\Users\레노버\Downloads\Hands Logger Database - HANDS (1).csv'

# 출력 파일
OUTPUT_HAND_SUMMARY = r'mock_data/bigquery/hand_summary_real.json'
OUTPUT_VIDEO_FILES = r'mock_data/bigquery/video_files_real.json'
OUTPUT_EMBEDDINGS = r'mock_data/embeddings/hand_embeddings_real.json'


def parse_board_cards(row: Dict) -> str:
    """보드 카드를 문자열로 조합"""
    cards = []
    if row.get('board_f1'):
        cards.append(row['board_f1'])
    if row.get('board_f2'):
        cards.append(row['board_f2'])
    if row.get('board_f3'):
        cards.append(row['board_f3'])
    if row.get('board_turn'):
        cards.append(row['board_turn'])
    if row.get('board_river'):
        cards.append(row['board_river'])

    return ', '.join(cards) if cards else ''


def parse_hole_cards(holes_json_str: str) -> List[str]:
    """홀 카드 JSON을 파싱"""
    if not holes_json_str or holes_json_str == '{}':
        return []

    try:
        holes = json.loads(holes_json_str)
        all_holes = []
        for seat, cards in holes.items():
            if isinstance(cards, list) and len(cards) == 2:
                all_holes.append(f"Seat {seat}: {cards[0]}, {cards[1]}")
        return all_holes
    except:
        return []


def parse_player_names(stacks_json_str: str) -> List[str]:
    """스택 JSON에서 플레이어 시트 번호 추출 (실제 이름은 없으므로 가상 생성)"""
    if not stacks_json_str or stacks_json_str == '{}':
        return []

    try:
        stacks = json.loads(stacks_json_str)

        # 가상 플레이어 이름 풀
        player_names = [
            "Tom Dwan", "Phil Ivey", "Daniel Negreanu", "Phil Hellmuth",
            "Doyle Brunson", "Chris Moneymaker", "Vanessa Selbst", "Erik Seidel",
            "Antonio Esfandiari", "Jason Mercier", "Patrik Antonius", "Gus Hansen"
        ]

        # 시트 번호에 랜덤 플레이어 할당
        seats = sorted([int(seat) for seat in stacks.keys()])
        assigned_names = random.sample(player_names, min(len(seats), len(player_names)))

        return assigned_names
    except:
        return []


def generate_summary_text(row: Dict, board_cards: str, player_names: List[str]) -> str:
    """핸드 요약 텍스트 생성"""
    hand_no = row.get('hand_no', '?')
    start_street = row.get('start_street', 'PREFLOP')
    pot = row.get('pre_pot', '0')

    # 플레이어 이름
    players_str = ', '.join(player_names[:3]) if player_names else "Unknown players"

    # 요약 생성
    summary = f"Hand #{hand_no}: {players_str}. "
    summary += f"Action started at {start_street}. "

    if board_cards:
        summary += f"Board: {board_cards}. "

    if pot and pot != '0':
        summary += f"Pre-flop pot: {pot} chips. "

    # 랜덤 액션 추가 (더 현실감 있게)
    actions = [
        f"{player_names[0] if player_names else 'Player'} raises pre-flop",
        f"{player_names[1] if len(player_names) > 1 else 'Player'} calls",
        "All-in on the flop",
        "Big bluff on the turn",
        "Hero call on the river"
    ]
    summary += random.choice(actions) + "."

    return summary


def convert_to_hand_summary(csv_file: str) -> List[Dict[str, Any]]:
    """CSV를 hand_summary 형식으로 변환"""
    hands = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, 1):
            # 기본 정보 추출
            hand_id = row.get('hand_id', f'hand_{idx}')
            table_id = row.get('table_id', '1')
            hand_number = int(row.get('hand_no', idx))
            timestamp = row.get('started_at', datetime.now().isoformat())

            # 보드 카드 조합
            board_cards = parse_board_cards(row)

            # 플레이어 정보
            player_names = parse_player_names(row.get('stacks_json', '{}'))

            # 홀 카드
            hole_cards = parse_hole_cards(row.get('holes_json', '{}'))

            # 팟 크기 (USD로 변환 가정: 칩을 100으로 나눔)
            pot_chips = int(row.get('pre_pot', 0)) if row.get('pre_pot') else 0
            pot_usd = round(pot_chips / 100, 2)

            # 요약 텍스트 생성
            summary_text = generate_summary_text(row, board_cards, player_names)

            # hand_summary 형식
            hand = {
                "hand_id": hand_id,
                "event_id": f"event_2025_{idx % 5 + 1}",  # 가상 이벤트 ID
                "tournament_id": f"tournament_{idx % 3 + 1}",  # 가상 토너먼트 ID
                "table_id": table_id,
                "hand_number": hand_number,
                "timestamp": timestamp,
                "summary_text": summary_text,
                "player_names": player_names,
                "pot_size_usd": pot_usd,
                "board_cards": board_cards,
                "hole_cards": hole_cards,
                "start_street": row.get('start_street', 'PREFLOP'),
                "created_at": datetime.now().isoformat()
            }

            hands.append(hand)

    return hands


def generate_video_files(hands: List[Dict]) -> List[Dict[str, Any]]:
    """hand_summary 기반으로 가상 비디오 파일 생성 (M2용)"""
    videos = []

    # 테이블별로 그룹화
    tables = {}
    for hand in hands:
        table_id = hand['table_id']
        if table_id not in tables:
            tables[table_id] = []
        tables[table_id].append(hand)

    # 각 테이블당 1개 비디오
    for table_id, table_hands in tables.items():
        video = {
            "file_id": f"video_table_{table_id}",
            "video_path": f"/nas/poker/2025/table_{table_id}.mp4",
            "proxy_path": f"gs://gg-poker-proxies/table_{table_id}_720p.mp4",
            "duration_seconds": len(table_hands) * 180.0,  # 핸드당 3분 가정
            "resolution": "1920x1080",
            "codec": "h264",
            "file_size_bytes": len(table_hands) * 100 * 1024 * 1024,  # 핸드당 100MB 가정
            "created_at": datetime.now().isoformat()
        }
        videos.append(video)

    return videos


def generate_embeddings(hands: List[Dict]) -> List[Dict[str, Any]]:
    """hand_summary 기반으로 가상 임베딩 생성 (M4용)"""
    embeddings = []

    for hand in hands:
        # 768차원 가상 임베딩 (랜덤, 정규화)
        embedding_vector = [random.gauss(0, 0.3) for _ in range(768)]

        # 정규화
        magnitude = sum(x ** 2 for x in embedding_vector) ** 0.5
        if magnitude > 0:
            embedding_vector = [x / magnitude for x in embedding_vector]

        embedding = {
            "hand_id": hand['hand_id'],
            "summary_text": hand['summary_text'],
            "embedding": embedding_vector,
            "created_at": datetime.now().isoformat()
        }

        embeddings.append(embedding)

    return embeddings


def main():
    print("=" * 60)
    print("POKER-BRAIN 샘플 데이터 변환")
    print("=" * 60)
    print()

    # 1. CSV 읽기 및 hand_summary 변환
    print("[1/5] CSV 파일 읽기...")
    print(f"  입력: {INPUT_CSV}")
    hands = convert_to_hand_summary(INPUT_CSV)
    print(f"  ✅ {len(hands)}개 핸드 변환 완료")
    print()

    # 2. hand_summary 저장
    print("[2/5] hand_summary 저장...")
    print(f"  출력: {OUTPUT_HAND_SUMMARY}")
    with open(OUTPUT_HAND_SUMMARY, 'w', encoding='utf-8') as f:
        json.dump(hands, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 저장 완료 ({len(hands)}개)")
    print()

    # 3. video_files 생성 및 저장
    print("[3/5] video_files 생성...")
    print(f"  출력: {OUTPUT_VIDEO_FILES}")
    videos = generate_video_files(hands)
    with open(OUTPUT_VIDEO_FILES, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 저장 완료 ({len(videos)}개 비디오)")
    print()

    # 4. embeddings 생성 및 저장
    print("[4/5] embeddings 생성...")
    print(f"  출력: {OUTPUT_EMBEDDINGS}")
    embeddings = generate_embeddings(hands)
    with open(OUTPUT_EMBEDDINGS, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 저장 완료 ({len(embeddings)}개 임베딩)")
    print()

    # 5. 요약
    print("[5/5] 변환 완료!")
    print("=" * 60)
    print(f"✅ hand_summary: {len(hands)}개")
    print(f"✅ video_files: {len(videos)}개")
    print(f"✅ embeddings: {len(embeddings)}개")
    print()
    print("다음 단계:")
    print("  1. 생성된 파일 확인:")
    print(f"     - {OUTPUT_HAND_SUMMARY}")
    print(f"     - {OUTPUT_VIDEO_FILES}")
    print(f"     - {OUTPUT_EMBEDDINGS}")
    print()
    print("  2. 테스트 실행:")
    print("     cd modules/m4-rag-search")
    print("     pytest tests/ -v")
    print()
    print("  3. API 서버 실행:")
    print("     python -m app.api")
    print("=" * 60)


if __name__ == '__main__':
    main()
