
#!/usr/bin/env python
"""
테스트용 샘플 포커 비디오 생성
실제 분석 테스트를 위한 가상 포커 영상 생성기
"""
import cv2
import numpy as np
import random
import math
import os
from pathlib import Path

def create_sample_video(output_path="test_videos/sample_poker_video.mp4", 
                       duration=300, fps=30, width=1280, height=720):
    """
    포커 테이블 시뮬레이션 비디오 생성
    
    Args:
        output_path: 출력 비디오 파일 경로
        duration: 비디오 길이 (초)
        fps: 초당 프레임 수
        width, height: 비디오 해상도
    """
    
    # 출력 디렉토리 생성
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 비디오 작성기 설정
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    print(f"[VIDEO] 샘플 비디오 생성 시작: {output_path}")
    print(f"[INFO] 설정: {width}x{height}, {fps}FPS, {duration}초 ({total_frames} 프레임)")
    
    # 포커 테이블 설정
    table_center = (width // 2, height // 2)
    table_radius = min(width, height) // 3
    
    # 플레이어 위치 (6명 기준)
    player_positions = []
    for i in range(6):
        angle = i * math.pi / 3  # 60도씩
        x = table_center[0] + int(table_radius * 1.2 * math.cos(angle))
        y = table_center[1] + int(table_radius * 1.2 * math.sin(angle))
        player_positions.append((x, y))
    
    # 핸드 시나리오 생성
    hands = generate_hand_scenarios(duration, fps)
    
    current_hand_index = 0
    current_hand = hands[0] if hands else None
    
    for frame_num in range(total_frames):
        current_time = frame_num / fps
        
        # 배경 생성 (녹색 포커 테이블)
        frame = create_poker_table_background(width, height, table_center, table_radius)
        
        # 현재 핸드 업데이트
        if current_hand and current_time > current_hand['end_time']:
            current_hand_index += 1
            current_hand = hands[current_hand_index] if current_hand_index < len(hands) else None
        
        # 핸드가 진행 중인 경우
        if current_hand and current_hand['start_time'] <= current_time <= current_hand['end_time']:
            hand_progress = (current_time - current_hand['start_time']) / current_hand['duration']
            
            # 딜링 애니메이션 (시작 10초 동안)
            if hand_progress < 0.1:
                draw_dealing_animation(frame, table_center, player_positions, 
                                     hand_progress * 10, current_hand['num_players'])
            
            # 게임 진행 중
            elif hand_progress < 0.9:
                draw_game_state(frame, table_center, player_positions, 
                              current_hand, hand_progress)
            
            # 팟 수집 애니메이션 (끝 10초 동안)
            else:
                collection_progress = (hand_progress - 0.9) / 0.1
                draw_pot_collection(frame, table_center, player_positions, 
                                  collection_progress, current_hand['winner'])
        
        # 게임 정보 표시
        draw_game_info(frame, current_time, current_hand, len(hands))
        
        # 프레임 저장
        out.write(frame)
        
        # 진행률 표시
        if frame_num % (fps * 10) == 0:  # 10초마다
            progress = (frame_num / total_frames) * 100
            print(f"진행률: {progress:.1f}%")
    
    out.release()
    print(f"[DONE] 샘플 비디오 생성 완료: {output_path}")
    return output_path

def generate_hand_scenarios(duration, fps):
    """핸드 시나리오 생성"""
    hands = []
    current_time = 0
    hand_id = 1
    
    while current_time < duration - 60:  # 마지막 1분 여유
        # 핸드 길이 랜덤 생성 (30초 ~ 180초)
        hand_duration = random.randint(30, 180)
        
        # 핸드 간 간격 (10초 ~ 30초)
        gap = random.randint(10, 30)
        
        start_time = current_time + gap
        end_time = start_time + hand_duration
        
        if end_time > duration:
            break
        
        hands.append({
            'hand_id': hand_id,
            'start_time': start_time,
            'end_time': end_time,
            'duration': hand_duration,
            'num_players': random.randint(2, 6),
            'winner': random.randint(0, 5),
            'pot_size': random.randint(100, 5000)
        })
        
        current_time = end_time
        hand_id += 1
    
    print(f"🎲 생성된 핸드 수: {len(hands)}개")
    return hands

def create_poker_table_background(width, height, center, radius):
    """포커 테이블 배경 생성"""
    # 어두운 배경
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (20, 40, 20)  # 어두운 녹색
    
    # 테이블 (타원형)
    cv2.ellipse(frame, center, (radius, int(radius * 0.8)), 0, 0, 360, (0, 100, 0), -1)
    cv2.ellipse(frame, center, (radius, int(radius * 0.8)), 0, 0, 360, (0, 150, 0), 5)
    
    # 내부 타원
    cv2.ellipse(frame, center, (int(radius * 0.7), int(radius * 0.5)), 0, 0, 360, (0, 80, 0), 3)
    
    return frame

def draw_dealing_animation(frame, center, positions, progress, num_players):
    """딜링 애니메이션 그리기"""
    # 딜러 위치 (중앙 아래)
    dealer_pos = (center[0], center[1] + 50)
    cv2.circle(frame, dealer_pos, 15, (100, 100, 100), -1)
    cv2.putText(frame, "D", (dealer_pos[0]-5, dealer_pos[1]+5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # 카드 딜링 (순차적으로)
    cards_per_player = 2
    total_cards = num_players * cards_per_player
    cards_dealt = int(progress * total_cards)
    
    for i in range(min(cards_dealt, total_cards)):
        player_idx = i % num_players
        card_num = i // num_players
        
        pos = positions[player_idx]
        card_x = pos[0] + (card_num - 0.5) * 20
        card_y = pos[1]
        
        # 카드 그리기
        cv2.rectangle(frame, (card_x - 10, card_y - 15), 
                     (card_x + 10, card_y + 15), (255, 255, 255), -1)
        cv2.rectangle(frame, (card_x - 10, card_y - 15), 
                     (card_x + 10, card_y + 15), (0, 0, 0), 2)
    
    # 딜링 모션 표시
    if progress < 1.0:
        motion_angle = progress * 2 * math.pi * num_players
        motion_x = center[0] + int(30 * math.cos(motion_angle))
        motion_y = center[1] + int(30 * math.sin(motion_angle))
        cv2.circle(frame, (motion_x, motion_y), 8, (255, 255, 0), -1)

def draw_game_state(frame, center, positions, hand, progress):
    """게임 진행 상태 그리기"""
    # 플레이어 카드
    for i in range(hand['num_players']):
        pos = positions[i]
        
        # 2장의 카드
        for j in range(2):
            card_x = pos[0] + (j - 0.5) * 20
            card_y = pos[1]
            
            cv2.rectangle(frame, (card_x - 10, card_y - 15), 
                         (card_x + 10, card_y + 15), (255, 255, 255), -1)
            cv2.rectangle(frame, (card_x - 10, card_y - 15), 
                         (card_x + 10, card_y + 15), (0, 0, 0), 2)
    
    # 커뮤니티 카드 (플롭, 턴, 리버)
    community_cards = min(5, int(progress * 5) + 3)  # 3~5장
    for i in range(community_cards):
        card_x = center[0] + (i - 2) * 30
        card_y = center[1] - 50
        
        cv2.rectangle(frame, (card_x - 12, card_y - 18), 
                     (card_x + 12, card_y + 18), (255, 255, 255), -1)
        cv2.rectangle(frame, (card_x - 12, card_y - 18), 
                     (card_x + 12, card_y + 18), (0, 0, 0), 2)
    
    # 팟 (중앙에 칩들)
    pot_chips = int(hand['pot_size'] / 100)
    for i in range(min(pot_chips, 20)):  # 최대 20개 칩 표시
        chip_angle = i * 0.3
        chip_x = center[0] + int(15 * math.cos(chip_angle))
        chip_y = center[1] + int(15 * math.sin(chip_angle))
        
        color = [(0, 0, 200), (0, 200, 0), (200, 0, 0)][i % 3]  # 파랑, 녹색, 빨강
        cv2.circle(frame, (chip_x, chip_y), 8, color, -1)
        cv2.circle(frame, (chip_x, chip_y), 8, (255, 255, 255), 1)

def draw_pot_collection(frame, center, positions, progress, winner):
    """팟 수집 애니메이션 그리기"""
    winner_pos = positions[winner]
    
    # 칩들이 승자에게 이동하는 애니메이션
    for i in range(20):
        # 시작 위치 (팟 중앙)
        start_x = center[0] + int(15 * math.cos(i * 0.3))
        start_y = center[1] + int(15 * math.sin(i * 0.3))
        
        # 끝 위치 (승자)
        end_x = winner_pos[0]
        end_y = winner_pos[1] + 30
        
        # 현재 위치 (선형 보간)
        current_x = int(start_x + (end_x - start_x) * progress)
        current_y = int(start_y + (end_y - start_y) * progress)
        
        color = [(0, 0, 200), (0, 200, 0), (200, 0, 0)][i % 3]
        cv2.circle(frame, (current_x, current_y), 8, color, -1)
        cv2.circle(frame, (current_x, current_y), 8, (255, 255, 255), 1)
    
    # 승자 표시
    cv2.circle(frame, winner_pos, 25, (0, 255, 0), 3)
    cv2.putText(frame, "WIN", (winner_pos[0]-15, winner_pos[1]-30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

def draw_game_info(frame, current_time, current_hand, total_hands):
    """게임 정보 표시"""
    # 시간 표시
    time_text = f"Time: {current_time:.1f}s"
    cv2.putText(frame, time_text, (20, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # 현재 핸드 정보
    if current_hand:
        hand_text = f"Hand #{current_hand['hand_id']} ({current_hand['duration']}s)"
        cv2.putText(frame, hand_text, (20, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        pot_text = f"Pot: ${current_hand['pot_size']}"
        cv2.putText(frame, pot_text, (20, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    else:
        status_text = "Waiting for next hand..."
        cv2.putText(frame, status_text, (20, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
    
    # 총 핸드 수
    total_text = f"Total Hands: {total_hands}"
    cv2.putText(frame, total_text, (20, frame.shape[0] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

if __name__ == "__main__":
    # 샘플 비디오 생성
    create_sample_video(
        output_path="test_videos/sample_poker_tournament.mp4",
        duration=600,  # 10분
        fps=30
    )
    
    print("[COMPLETE] 샘플 비디오 생성 완료!")
    print("📁 파일 위치: test_videos/sample_poker_tournament.mp4")
    print("🔧 이 비디오로 핸드 감지 시스템을 테스트할 수 있습니다.")
