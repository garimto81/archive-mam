#!/usr/bin/env python
"""
핸드 감지 시각화 도구
실시간으로 감지 과정을 시각화하여 디버깅 및 튜닝에 활용
"""
import cv2
import numpy as np
import json
from pathlib import Path
import argparse
from typing import Dict, List, Any

from hand_boundary_detector import HandBoundaryDetector, MotionTracker, ObjectDetector

class HandDetectionVisualizer:
    """핸드 감지 과정 시각화"""
    
    def __init__(self, show_debug=True):
        self.detector = HandBoundaryDetector()
        self.show_debug = show_debug
        
        # 시각화 색상 정의
        self.colors = {
            'motion': (0, 255, 255),      # 노란색 - 모션 영역
            'cards': (0, 255, 0),         # 녹색 - 카드
            'chips': (255, 0, 0),         # 파란색 - 칩
            'roi': (255, 255, 0),         # 시안색 - ROI
            'hand_start': (0, 0, 255),    # 빨간색 - 핸드 시작
            'hand_end': (255, 0, 255),    # 마젠타색 - 핸드 종료
            'text': (255, 255, 255)       # 흰색 - 텍스트
        }
        
        # 상태 추적
        self.frame_count = 0
        self.current_hand_info = None
        self.detection_history = []
    
    def visualize_video(self, video_path: str, output_path: str = None, save_frames: bool = False):
        """비디오 분석과 동시에 시각화"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"비디오 정보: {width}x{height}, {fps} FPS, {total_frames} 프레임")
        
        # 출력 비디오 설정
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width * 2, height))
        else:
            out = None
        
        # 프레임 저장 디렉토리
        if save_frames:
            frames_dir = Path("debug_frames")
            frames_dir.mkdir(exist_ok=True)
        
        # 첫 번째 프레임으로 ROI 설정
        ret, first_frame = cap.read()
        if ret:
            self.detector.object_detector.set_regions(first_frame.shape)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        hand_id = 1
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            current_time = self.frame_count / fps
            
            # 원본 프레임 복사
            display_frame = frame.copy()
            debug_frame = np.zeros_like(frame)
            
            # 모션 추적 및 객체 감지
            motion_info = self.detector.motion_tracker.update(frame)
            cards = self.detector.object_detector.detect_cards(frame)
            chips = self.detector.object_detector.detect_chips(frame)
            
            # 핸드 감지 로직
            if self.detector.current_hand_start is None:
                is_start, confidence, indicators = self.detector._detect_hand_start(
                    frame, motion_info, current_time
                )
                
                if is_start:
                    self.detector.current_hand_start = {
                        'hand_id': hand_id,
                        'frame': self.frame_count,
                        'time': current_time,
                        'confidence': confidence,
                        'indicators': indicators
                    }
                    self.current_hand_info = {
                        'status': 'in_progress',
                        'start_time': current_time,
                        'hand_id': hand_id
                    }
                    print(f"핸드 {hand_id} 시작 감지: {current_time:.2f}초 (신뢰도: {confidence:.1f})")
            else:
                # 최소 30초 후부터 종료 감지
                if current_time - self.detector.current_hand_start['time'] > 30:
                    is_end, confidence, indicators = self.detector._detect_hand_end(
                        frame, motion_info, current_time
                    )
                    
                    if is_end:
                        duration = current_time - self.detector.current_hand_start['time']
                        print(f"핸드 {hand_id} 종료 감지: {current_time:.2f}초 (길이: {duration:.1f}초)")
                        
                        self.current_hand_info = {
                            'status': 'completed',
                            'end_time': current_time,
                            'duration': duration
                        }
                        
                        self.detector.current_hand_start = None
                        hand_id += 1
            
            # 시각화 수행
            self._draw_motion_regions(display_frame, debug_frame, motion_info)
            self._draw_detected_objects(display_frame, debug_frame, cards, chips)
            self._draw_roi_regions(display_frame, debug_frame)
            self._draw_hand_status(display_frame, current_time)
            self._draw_detection_info(debug_frame, motion_info, cards, chips, current_time)
            
            # 두 프레임을 나란히 결합
            combined_frame = np.hstack([display_frame, debug_frame])
            
            # 비디오 저장
            if out:
                out.write(combined_frame)
            
            # 프레임 저장
            if save_frames and self.frame_count % 30 == 0:  # 1초마다
                frame_path = frames_dir / f"frame_{self.frame_count:06d}.jpg"
                cv2.imwrite(str(frame_path), combined_frame)
            
            # 실시간 표시 (선택사항)
            if self.show_debug and self.frame_count % 5 == 0:  # 5프레임마다 표시
                resized = cv2.resize(combined_frame, (1280, 360))
                cv2.imshow('Hand Detection Debug', resized)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):  # 스페이스바로 일시정지
                    cv2.waitKey(0)
            
            self.frame_count += 1
            
            # 진행률 표시
            if self.frame_count % 300 == 0:
                progress = (self.frame_count / total_frames) * 100
                print(f"진행률: {progress:.1f}%")
        
        # 정리
        cap.release()
        if out:
            out.release()
        cv2.destroyAllWindows()
        
        print(f"시각화 완료: {self.frame_count} 프레임 처리")
        if output_path:
            print(f"결과 비디오 저장: {output_path}")
    
    def _draw_motion_regions(self, display_frame, debug_frame, motion_info):
        """모션 영역 시각화"""
        for region in motion_info['motion_regions']:
            x, y, w, h = region['bbox']
            
            # 원본 프레임에 반투명 박스
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), self.colors['motion'], -1)
            cv2.addWeighted(display_frame, 0.8, overlay, 0.2, 0, display_frame)
            
            # 디버그 프레임에 윤곽선
            cv2.rectangle(debug_frame, (x, y), (x + w, y + h), self.colors['motion'], 2)
            
            # 중심점 표시
            center = region['center']
            cv2.circle(debug_frame, center, 5, self.colors['motion'], -1)
            
            # 영역 정보 텍스트
            cv2.putText(debug_frame, f"A:{region['area']}", 
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['text'])
    
    def _draw_detected_objects(self, display_frame, debug_frame, cards, chips):
        """감지된 객체 시각화"""
        # 카드 시각화
        for card in cards:
            if 'bbox' in card:
                x, y, w, h = card['bbox']
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), self.colors['cards'], 2)
                cv2.rectangle(debug_frame, (x, y), (x + w, y + h), self.colors['cards'], 2)
                
                # 카드 정보
                info_text = f"Card({card.get('confidence', 0):.1f})"
                cv2.putText(debug_frame, info_text, (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['cards'])
        
        # 칩 시각화
        for chip in chips:
            center = chip['center']
            radius = chip['radius']
            color = self.colors['chips']
            
            cv2.circle(display_frame, center, radius, color, 2)
            cv2.circle(debug_frame, center, radius, color, 2)
            
            # 칩 정보
            chip_text = f"{chip['color']}"
            cv2.putText(debug_frame, chip_text, (center[0] - 20, center[1] - radius - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, color)
    
    def _draw_roi_regions(self, display_frame, debug_frame):
        """ROI 영역 시각화"""
        # 팟 영역
        if self.detector.object_detector.pot_region:
            pot = self.detector.object_detector.pot_region
            cv2.rectangle(debug_frame, (pot['x1'], pot['y1']), 
                         (pot['x2'], pot['y2']), self.colors['roi'], 1)
            cv2.putText(debug_frame, "POT", (pot['x1'], pot['y1'] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['roi'])
        
        # 플레이어 영역
        for player_id, region in self.detector.object_detector.player_regions.items():
            cv2.rectangle(debug_frame, (region['x1'], region['y1']), 
                         (region['x2'], region['y2']), self.colors['roi'], 1)
            cv2.putText(debug_frame, f"P{player_id}", 
                       (region['x1'], region['y1'] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['roi'])
    
    def _draw_hand_status(self, display_frame, current_time):
        """현재 핸드 상태 표시"""
        status_text = []
        
        if self.current_hand_info:
            if self.current_hand_info['status'] == 'in_progress':
                duration = current_time - self.current_hand_info['start_time']
                status_text.append(f"Hand {self.current_hand_info['hand_id']} - {duration:.1f}s")
                color = self.colors['hand_start']
            else:
                status_text.append(f"Hand Completed - {self.current_hand_info['duration']:.1f}s")
                color = self.colors['hand_end']
        else:
            status_text.append("Waiting for Hand Start")
            color = self.colors['text']
        
        # 시간 정보
        status_text.append(f"Time: {current_time:.1f}s")
        status_text.append(f"Frame: {self.frame_count}")
        
        # 화면 상단에 상태 표시
        for i, text in enumerate(status_text):
            y_pos = 30 + i * 25
            cv2.putText(display_frame, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    def _draw_detection_info(self, debug_frame, motion_info, cards, chips, current_time):
        """감지 정보 표시"""
        info_lines = [
            f"Motion Areas: {len(motion_info['motion_regions'])}",
            f"Total Motion: {motion_info['total_motion_area']}",
            f"Cards: {len(cards)}",
            f"Chips: {len(chips)}",
        ]
        
        # 모션 패턴 분석 결과
        dealing_score = self.detector.motion_tracker.analyze_motion_pattern('dealing')
        collection_score = self.detector.motion_tracker.analyze_motion_pattern('collection')
        
        info_lines.extend([
            f"Dealing Score: {dealing_score:.2f}",
            f"Collection Score: {collection_score:.2f}",
        ])
        
        # 화면 하단에 정보 표시
        frame_height = debug_frame.shape[0]
        for i, line in enumerate(info_lines):
            y_pos = frame_height - 20 - (len(info_lines) - i - 1) * 20
            cv2.putText(debug_frame, line, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'])

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='핸드 감지 시각화 도구')
    parser.add_argument('video_path', help='분석할 비디오 파일 경로')
    parser.add_argument('--output', '-o', help='출력 비디오 파일 경로')
    parser.add_argument('--save-frames', action='store_true', help='디버그 프레임 저장')
    parser.add_argument('--no-display', action='store_true', help='실시간 표시 비활성화')
    
    args = parser.parse_args()
    
    if not Path(args.video_path).exists():
        print(f"❌ 비디오 파일을 찾을 수 없습니다: {args.video_path}")
        return
    
    print(f"🎥 핸드 감지 시각화 시작: {args.video_path}")
    
    visualizer = HandDetectionVisualizer(show_debug=not args.no_display)
    
    try:
        visualizer.visualize_video(
            video_path=args.video_path,
            output_path=args.output,
            save_frames=args.save_frames
        )
        print("✅ 시각화 완료")
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()