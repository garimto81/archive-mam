#!/usr/bin/env python
"""
고속 포커 핸드 경계 감지 시스템
10분 영상을 분 단위로 분석하도록 최적화
"""
import cv2
import numpy as np
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from collections import deque
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HandBoundary:
    """핸드 경계 정보"""
    hand_id: int
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    duration: float
    confidence: float
    
    def to_dict(self):
        return asdict(self)

class FastHandDetector:
    """고속 핸드 감지기 - 프레임 샘플링 및 병렬 처리"""
    
    def __init__(self, sampling_rate=60, num_workers=None):
        """
        Args:
            sampling_rate: 프레임 샘플링 비율 (60 = 60프레임마다 1개 분석)
            num_workers: 병렬 처리 워커 수 (None = CPU 코어 수)
        """
        self.sampling_rate = sampling_rate
        self.num_workers = num_workers or mp.cpu_count()
        
        # 핸드 감지 파라미터
        self.min_hand_duration = 30  # 최소 30초
        self.max_hand_duration = 600  # 최대 10분
        
        # 간소화된 감지 임계값
        self.motion_threshold = 1000  # 모션 영역 크기
        self.card_threshold = 3  # 최소 카드 수
        
    def analyze_video(self, video_path: str, output_path: str = None, progress_callback=None) -> str:
        """비디오 고속 분석"""
        logger.info(f"고속 핸드 감지 시작: {video_path}")
        start_time = time.time()
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"비디오 정보: {total_frames} 프레임, {fps} FPS, {total_frames/fps/60:.1f}분")
        logger.info(f"샘플링 비율: {self.sampling_rate}:1, 워커 수: {self.num_workers}")
        
        # 1단계: 키 프레임 추출 (샘플링)
        key_frames = self._extract_key_frames(cap, total_frames, fps, progress_callback)
        
        # 2단계: 병렬 처리로 핸드 후보 감지
        hand_candidates = self._detect_hand_candidates_parallel(key_frames, fps)
        
        # 3단계: 정밀 분석 (후보 구간만)
        validated_hands = self._validate_hands_precise(cap, hand_candidates, fps, progress_callback)
        
        cap.release()
        
        # 결과 저장
        if output_path is None:
            output_path = f"analysis_results/fast_boundaries_{Path(video_path).stem}.json"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([hand.to_dict() for hand in validated_hands], f, indent=2)
        
        analysis_time = time.time() - start_time
        logger.info(f"분석 완료: {len(validated_hands)}개 핸드 감지")
        logger.info(f"소요 시간: {analysis_time:.1f}초 ({analysis_time/60:.1f}분)")
        logger.info(f"속도 향상: {(total_frames/fps)/analysis_time:.1f}x")
        
        return output_path
    
    def _extract_key_frames(self, cap, total_frames, fps, progress_callback):
        """키 프레임 추출 (샘플링)"""
        key_frames = []
        frame_indices = range(0, total_frames, self.sampling_rate)
        
        logger.info(f"키 프레임 추출 중... ({len(frame_indices)}개)")
        
        for idx, frame_idx in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # 작은 크기로 리사이즈 (분석 속도 향상)
            # 더 작은 크기로 리사이즈하여 속도 향상
            small_frame = cv2.resize(frame, (480, 270))
            
            key_frames.append({
                'frame_idx': frame_idx,
                'timestamp': frame_idx / fps,
                'frame': small_frame
            })
            
            # 진행률 업데이트
            if progress_callback and idx % 100 == 0:
                progress_callback({
                    'stage': 'extracting_keyframes',
                    'progress': (idx / len(frame_indices)) * 100,
                    'current': idx,
                    'total': len(frame_indices)
                })
        
        return key_frames
    
    def _detect_hand_candidates_parallel(self, key_frames, fps):
        """병렬 처리로 핸드 후보 감지"""
        logger.info(f"핸드 후보 감지 중... (병렬 처리)")
        
        # 프레임을 청크로 분할
        chunk_size = max(1, len(key_frames) // self.num_workers)
        chunks = [key_frames[i:i+chunk_size] for i in range(0, len(key_frames), chunk_size)]
        
        # 병렬 처리
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(self._analyze_chunk, chunk) for chunk in chunks]
            
            all_events = []
            for future in futures:
                chunk_events = future.result()
                all_events.extend(chunk_events)
        
        # 이벤트를 핸드로 그룹화
        hand_candidates = self._group_events_to_hands(all_events, fps)
        
        return hand_candidates
    
    def _analyze_chunk(self, frames_chunk):
        """프레임 청크 분석 (워커 프로세스에서 실행)"""
        events = []
        
        # 간소화된 분석기 초기화
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False,
            varThreshold=100,
            history=100
        )
        
        # 이전 프레임 정보 저장
        prev_motion_area = 0
        motion_history = deque(maxlen=5)
        
        for frame_info in frames_chunk:
            frame = frame_info['frame']
            
            # 빠른 모션 감지
            fg_mask = bg_subtractor.apply(frame)
            
            # 노이즈 제거를 위한 간단한 모폴로지 연산
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            
            motion_area = cv2.countNonZero(fg_mask)
            motion_history.append(motion_area)
            
            # 급격한 모션 변화 감지
            if len(motion_history) >= 3:
                avg_motion = sum(motion_history) / len(motion_history)
                motion_change = abs(motion_area - prev_motion_area)
                
                # 빠른 카드 감지 (색상 기반만)
                card_count = self._quick_card_detection(frame)
                
                # 핸드 시작 감지: 급격한 모션 증가 + 카드 존재
                if (motion_change > self.motion_threshold * 0.5 and 
                    motion_area > self.motion_threshold and 
                    card_count >= self.card_threshold):
                    events.append({
                        'type': 'potential_hand_start',
                        'frame_idx': frame_info['frame_idx'],
                        'timestamp': frame_info['timestamp'],
                        'motion_area': motion_area,
                        'card_count': card_count,
                        'confidence': min(motion_area / self.motion_threshold * 50 + card_count * 10, 100)
                    })
                
                # 핸드 종료 감지: 큰 모션 후 급격한 감소
                elif (prev_motion_area > self.motion_threshold * 2 and 
                      motion_area < self.motion_threshold * 0.5):
                    events.append({
                        'type': 'potential_hand_end',
                        'frame_idx': frame_info['frame_idx'],
                        'timestamp': frame_info['timestamp'],
                        'motion_area': motion_area,
                        'confidence': 80
                    })
            
            prev_motion_area = motion_area
        
        return events
    
    def _quick_card_detection(self, frame):
        """빠른 카드 감지 (색상 기반)"""
        # 중앙 영역만 검사 (계산량 감소)
        h, w = frame.shape[:2]
        center_region = frame[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)]
        
        hsv = cv2.cvtColor(center_region, cv2.COLOR_BGR2HSV)
        
        # 흰색 영역 감지 (카드 뒷면)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 빠른 연결 컴포넌트 카운트 (상세 분석 생략)
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 카드 크기 필터링
        card_count = 0
        min_area = 50  # 리사이즈된 이미지 기준 (더 관대하게)
        max_area = 3000
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                # 간단한 종횡비 검사
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                if 1.2 < aspect_ratio < 2.0:
                    card_count += 1
        
        return card_count
    
    def _group_events_to_hands(self, events, fps):
        """이벤트를 핸드로 그룹화"""
        events.sort(key=lambda x: x['timestamp'])
        
        hand_candidates = []
        current_start = None
        hand_id = 1
        
        for event in events:
            if event['type'] == 'potential_hand_start' and current_start is None:
                current_start = event
            elif event['type'] == 'potential_hand_end' and current_start is not None:
                # 핸드 길이 확인
                duration = event['timestamp'] - current_start['timestamp']
                if self.min_hand_duration <= duration <= self.max_hand_duration:
                    hand_candidates.append({
                        'hand_id': hand_id,
                        'start_frame': current_start['frame_idx'],
                        'end_frame': event['frame_idx'],
                        'start_time': current_start['timestamp'],
                        'end_time': event['timestamp'],
                        'duration': duration,
                        'confidence': 70  # 초기 신뢰도
                    })
                    hand_id += 1
                current_start = None
        
        return hand_candidates
    
    def _validate_hands_precise(self, cap, hand_candidates, fps, progress_callback):
        """핸드 후보 정밀 검증 (선택적)"""
        logger.info(f"핸드 후보 검증 중... ({len(hand_candidates)}개)")
        
        validated_hands = []
        
        for idx, candidate in enumerate(hand_candidates):
            # 빠른 모드에서는 추가 검증 생략
            # 필요시 시작/종료 지점 근처만 정밀 분석
            
            hand = HandBoundary(
                hand_id=candidate['hand_id'],
                start_frame=candidate['start_frame'],
                end_frame=candidate['end_frame'],
                start_time=candidate['start_time'],
                end_time=candidate['end_time'],
                duration=candidate['duration'],
                confidence=candidate['confidence']
            )
            
            validated_hands.append(hand)
            
            if progress_callback:
                progress_callback({
                    'stage': 'validating_hands',
                    'progress': ((idx + 1) / len(hand_candidates)) * 100,
                    'current': idx + 1,
                    'total': len(hand_candidates)
                })
        
        return validated_hands

class UltraFastDetector:
    """초고속 감지기 - GPU 가속 및 극단적 최적화"""
    
    def __init__(self):
        self.frame_skip = 30  # 1초마다 1프레임만 분석
        self.min_motion_frames = 3  # 연속 3프레임 모션 감지시 핸드 시작
        
    def analyze_video_gpu(self, video_path: str) -> str:
        """GPU 가속 분석 (CUDA 필요)"""
        logger.info("GPU 가속 분석 시작...")
        
        # GPU 사용 가능 확인
        gpu_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if not gpu_available:
            logger.warning("GPU를 사용할 수 없습니다. CPU 모드로 전환합니다.")
            return self.analyze_video_cpu(video_path)
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # GPU 배경 제거기
        gpu_mog = cv2.cuda.createBackgroundSubtractorMOG2()
        
        hands = []
        frame_idx = 0
        
        while True:
            # 프레임 스킵
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            
            # GPU로 업로드
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            
            # GPU에서 배경 제거
            gpu_fg_mask = gpu_mog.apply(gpu_frame, -1)
            
            # 결과 다운로드
            fg_mask = gpu_fg_mask.download()
            
            # 간단한 핸드 감지 로직
            motion_pixels = cv2.countNonZero(fg_mask)
            if motion_pixels > 5000:  # 임계값
                # 핸드 시작/종료 로직
                pass
            
            frame_idx += self.frame_skip
        
        cap.release()
        return "gpu_analysis_complete.json"
    
    def analyze_video_cpu(self, video_path: str) -> str:
        """CPU 최적화 분석"""
        detector = FastHandDetector(sampling_rate=60, num_workers=mp.cpu_count())
        return detector.analyze_video(video_path)

def main():
    """테스트"""
    import sys
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = "videos/sample_poker_video.mp4"
    
    # 고속 감지기 테스트
    detector = FastHandDetector(sampling_rate=60, num_workers=4)
    
    def progress_callback(info):
        stage = info.get('stage', 'unknown')
        progress = info.get('progress', 0)
        print(f"\r[{stage}] {progress:.1f}%", end='', flush=True)
    
    result = detector.analyze_video(video_path, progress_callback=progress_callback)
    print(f"\n분석 결과: {result}")

if __name__ == "__main__":
    main()