"""
통합 분석 파이프라인
GFX 오버레이 감지, 팟 사이즈 OCR, 참여 플레이어 감지를 통합하는 메인 파이프라인
"""

import cv2
import numpy as np
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import time

# 모듈 import
from pot_size_ocr import PotSizeOCR, PotSizeReading
from player_detection import PlayerDetector, HandParticipation

@dataclass
class HandAnalysisResult:
    """핸드 분석 종합 결과"""
    hand_id: int
    start_time: float
    end_time: float
    duration: float
    
    # GFX 오버레이 정보
    gfx_start: Optional[float]
    gfx_end: Optional[float]
    gfx_confidence: float
    
    # 팟 사이즈 정보
    pot_readings: List[Dict]
    max_pot_size: Optional[float]
    pot_changes: List[Dict]
    
    # 참여 플레이어 정보
    participating_seats: List[int]
    total_players: int
    player_detection_confidence: float
    
    # 메타데이터
    analysis_timestamp: float
    processing_time: float
    video_source: str

@dataclass
class VideoAnalysisResult:
    """전체 영상 분석 결과"""
    video_path: str
    video_duration: float
    total_hands: int
    analysis_duration: float
    hands: List[HandAnalysisResult]
    
    # 통계
    avg_hand_duration: float
    avg_players_per_hand: float
    max_pot_in_video: float
    total_pot_value: float
    
    # 메타데이터
    analysis_settings: Dict
    created_at: str

class IntegratedAnalysisPipeline:
    """통합 분석 파이프라인"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # 모듈 초기화
        self.pot_analyzer = PotSizeOCR(config_path)
        self.player_detector = PlayerDetector(config_path)
        
        # 기본 설정
        self.settings = {
            'frame_skip_interval': 30,  # 팟 사이즈 분석용
            'gfx_confidence_threshold': 70.0,  # GFX 신뢰도 임계값
            'pot_confidence_threshold': 60.0,  # 팟 인식 신뢰도 임계값
            'player_confidence_threshold': 60.0,  # 플레이어 감지 신뢰도 임계값
            'min_hand_duration': 30.0,  # 최소 핸드 길이 (초)
            'max_hand_duration': 600.0,  # 최대 핸드 길이 (초)
        }
        
        if config_path and Path(config_path).exists():
            self.load_config(config_path)
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self, config_path: str):
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'pipeline_settings' in config:
                self.settings.update(config['pipeline_settings'])
                
            self.logger.info(f"파이프라인 설정 로드 완료: {config_path}")
            
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
    
    def load_gfx_segments(self, gfx_data_path: str) -> List[Dict]:
        """GFX 오버레이 분석 결과 로드"""
        try:
            with open(gfx_data_path, 'r', encoding='utf-8') as f:
                gfx_data = json.load(f)
            
            segments = gfx_data.get('segments', [])
            self.logger.info(f"GFX 구간 {len(segments)}개 로드 완료")
            return segments
            
        except Exception as e:
            self.logger.error(f"GFX 데이터 로드 실패: {e}")
            return []
    
    def validate_hand_segment(self, segment: Dict) -> bool:
        """핸드 구간 유효성 검증"""
        try:
            start_time = segment.get('handStart', 0)
            end_time = segment.get('handEnd', 0)
            duration = end_time - start_time
            
            # 기간 검증
            if duration < self.settings['min_hand_duration']:
                self.logger.warning(f"핸드 길이 부족: {duration:.1f}초")
                return False
                
            if duration > self.settings['max_hand_duration']:
                self.logger.warning(f"핸드 길이 초과: {duration:.1f}초")
                return False
            
            # GFX 신뢰도 검증
            gfx_confidence = segment.get('confidence', 0)
            if gfx_confidence < self.settings['gfx_confidence_threshold']:
                self.logger.warning(f"GFX 신뢰도 부족: {gfx_confidence:.1f}%")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"구간 검증 실패: {e}")
            return False
    
    def analyze_single_hand(self, video_path: str, segment: Dict, 
                           hand_id: int) -> Optional[HandAnalysisResult]:
        """단일 핸드 종합 분석"""
        start_time = time.time()
        
        try:
            # 구간 정보 추출
            hand_start = segment.get('handStart', 0)
            hand_end = segment.get('handEnd', 0)
            gfx_start = segment.get('gfxStart')
            gfx_end = segment.get('gfxEnd')
            gfx_confidence = segment.get('confidence', 0)
            
            self.logger.info(f"핸드 {hand_id} 분석 시작: {hand_start:.1f}s - {hand_end:.1f}s")
            
            # 1. 팟 사이즈 분석 (구간 전체)
            self.logger.debug("팟 사이즈 분석 시작...")
            pot_readings = self.analyze_pot_in_segment(video_path, hand_start, hand_end)
            
            # 팟 사이즈 통계
            valid_pot_readings = [r for r in pot_readings if r.pot_value and r.confidence >= self.settings['pot_confidence_threshold']]
            max_pot_size = max([r.pot_value for r in valid_pot_readings]) if valid_pot_readings else None
            
            # 팟 변화 감지
            pot_changes = self.detect_pot_changes_in_readings(valid_pot_readings)
            
            # 2. 참여 플레이어 분석
            self.logger.debug("참여 플레이어 분석 시작...")
            player_result = self.player_detector.analyze_hand_segment(
                video_path, hand_start, hand_end, hand_id
            )
            
            # 3. 결과 통합
            processing_time = time.time() - start_time
            
            result = HandAnalysisResult(
                hand_id=hand_id,
                start_time=hand_start,
                end_time=hand_end,
                duration=hand_end - hand_start,
                
                gfx_start=gfx_start,
                gfx_end=gfx_end,
                gfx_confidence=gfx_confidence,
                
                pot_readings=[{
                    'timestamp': r.timestamp,
                    'pot_value': r.pot_value,
                    'confidence': r.confidence,
                    'raw_text': r.raw_text
                } for r in valid_pot_readings],
                max_pot_size=max_pot_size,
                pot_changes=pot_changes,
                
                participating_seats=player_result.participating_seats,
                total_players=player_result.total_players,
                player_detection_confidence=player_result.detection_confidence,
                
                analysis_timestamp=time.time(),
                processing_time=processing_time,
                video_source=str(Path(video_path).name)
            )
            
            self.logger.info(f"핸드 {hand_id} 분석 완료 - 플레이어: {result.total_players}명, 최대 팟: ${max_pot_size or 0:,.0f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"핸드 {hand_id} 분석 실패: {e}")
            return None
    
    def analyze_pot_in_segment(self, video_path: str, start_time: float, 
                              end_time: float) -> List[PotSizeReading]:
        """구간 내 팟 사이즈 분석"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        readings = []
        
        try:
            # 샘플링 간격 계산 (최대 20개 샘플)
            duration = end_time - start_time
            sample_interval = max(2.0, duration / 20)
            
            current_time = start_time
            while current_time < end_time:
                # 프레임으로 이동
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # 팟 사이즈 분석
                frame_readings = self.pot_analyzer.analyze_frame(frame, current_time)
                readings.extend(frame_readings)
                
                current_time += sample_interval
                
        finally:
            cap.release()
        
        return readings
    
    def detect_pot_changes_in_readings(self, readings: List[PotSizeReading], 
                                     threshold_percent: float = 15.0) -> List[Dict]:
        """팟 사이즈 변화 감지"""
        if len(readings) < 2:
            return []
        
        changes = []
        prev_pot = readings[0].pot_value
        
        for reading in readings[1:]:
            if not reading.pot_value:
                continue
                
            change_percent = abs(reading.pot_value - prev_pot) / prev_pot * 100
            
            if change_percent >= threshold_percent:
                changes.append({
                    'timestamp': reading.timestamp,
                    'previous_pot': prev_pot,
                    'current_pot': reading.pot_value,
                    'change_amount': reading.pot_value - prev_pot,
                    'change_percent': change_percent
                })
                prev_pot = reading.pot_value
        
        return changes
    
    def analyze_video_complete(self, video_path: str, gfx_data_path: str, 
                              output_path: Optional[str] = None) -> VideoAnalysisResult:
        """전체 영상 종합 분석"""
        analysis_start = time.time()
        
        self.logger.info(f"통합 분석 시작: {video_path}")
        
        # GFX 구간 데이터 로드
        gfx_segments = self.load_gfx_segments(gfx_data_path)
        if not gfx_segments:
            raise ValueError("유효한 GFX 구간 데이터가 없습니다")
        
        # 비디오 정보 확인
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps
        cap.release()
        
        # 각 핸드 분석
        hand_results = []
        valid_segments = [s for s in gfx_segments if self.validate_hand_segment(s)]
        
        self.logger.info(f"유효한 핸드 구간: {len(valid_segments)}개")
        
        for i, segment in enumerate(valid_segments):
            hand_result = self.analyze_single_hand(video_path, segment, i + 1)
            if hand_result:
                hand_results.append(hand_result)
                
                # 진행률 표시
                if (i + 1) % 5 == 0:
                    progress = (i + 1) / len(valid_segments) * 100
                    self.logger.info(f"분석 진행률: {progress:.1f}% ({i + 1}/{len(valid_segments)})")
        
        # 전체 통계 계산
        analysis_duration = time.time() - analysis_start
        
        avg_hand_duration = np.mean([h.duration for h in hand_results]) if hand_results else 0
        avg_players_per_hand = np.mean([h.total_players for h in hand_results]) if hand_results else 0
        
        all_pot_values = []
        for hand in hand_results:
            if hand.max_pot_size:
                all_pot_values.append(hand.max_pot_size)
        
        max_pot_in_video = max(all_pot_values) if all_pot_values else 0
        total_pot_value = sum(all_pot_values)
        
        # 결과 생성
        result = VideoAnalysisResult(
            video_path=video_path,
            video_duration=video_duration,
            total_hands=len(hand_results),
            analysis_duration=analysis_duration,
            hands=hand_results,
            
            avg_hand_duration=avg_hand_duration,
            avg_players_per_hand=avg_players_per_hand,
            max_pot_in_video=max_pot_in_video,
            total_pot_value=total_pot_value,
            
            analysis_settings=self.settings.copy(),
            created_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 결과 저장
        if output_path:
            self.save_analysis_result(result, output_path)
        
        self.logger.info(f"통합 분석 완료 - {len(hand_results)}개 핸드, {analysis_duration:.1f}초 소요")
        
        return result
    
    def save_analysis_result(self, result: VideoAnalysisResult, output_path: str):
        """분석 결과 저장"""
        export_data = {
            'analysis_type': 'integrated_poker_analysis',
            'version': '1.0',
            'video_analysis': asdict(result),
            'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"분석 결과 저장 완료: {output_path}")
    
    def generate_summary_report(self, result: VideoAnalysisResult) -> str:
        """요약 보고서 생성"""
        report = f"""
📊 포커 영상 통합 분석 보고서
{'='*50}

🎬 비디오 정보:
• 파일: {Path(result.video_path).name}
• 총 길이: {result.video_duration/60:.1f}분
• 분석 시간: {result.analysis_duration:.1f}초

🃏 핸드 분석 결과:
• 총 핸드 수: {result.total_hands}개
• 평균 핸드 길이: {result.avg_hand_duration:.1f}초
• 핸드당 평균 플레이어: {result.avg_players_per_hand:.1f}명

💰 팟 사이즈 분석:
• 최대 팟 사이즈: ${result.max_pot_in_video:,.0f}
• 총 팟 가치: ${result.total_pot_value:,.0f}

👥 플레이어 참여 통계:
"""
        
        # 좌석별 참여 통계
        seat_participation = {}
        for hand in result.hands:
            for seat_id in hand.participating_seats:
                seat_participation[seat_id] = seat_participation.get(seat_id, 0) + 1
        
        if seat_participation:
            for seat_id, count in sorted(seat_participation.items()):
                report += f"• Seat {seat_id}: {count}회 참여\n"
        
        # 상위 5개 핸드
        top_hands = sorted([h for h in result.hands if h.max_pot_size], 
                          key=lambda x: x.max_pot_size, reverse=True)[:5]
        
        if top_hands:
            report += f"\n🏆 최대 팟 사이즈 TOP 5:\n"
            for i, hand in enumerate(top_hands, 1):
                report += f"{i}. 핸드 {hand.hand_id}: ${hand.max_pot_size:,.0f} ({hand.total_players}명)\n"
        
        report += f"\n📈 분석 완료 시각: {result.created_at}\n"
        
        return report
    
    def export_hand_clips_info(self, result: VideoAnalysisResult, 
                              output_dir: str) -> str:
        """핸드 클립 정보 내보내기"""
        clips_info = []
        
        for hand in result.hands:
            clip_info = {
                'hand_id': hand.hand_id,
                'filename': f"hand_{hand.hand_id:03d}.mp4",
                'start_time': hand.start_time,
                'end_time': hand.end_time,
                'duration': hand.duration,
                'players': hand.total_players,
                'max_pot': hand.max_pot_size or 0,
                'participating_seats': hand.participating_seats,
                'description': f"{hand.total_players}명 참여, 최대 팟 ${hand.max_pot_size or 0:,.0f}"
            }
            clips_info.append(clip_info)
        
        # FFmpeg 명령어 생성
        ffmpeg_commands = []
        for clip in clips_info:
            cmd = f'ffmpeg -i "{result.video_path}" -ss {clip["start_time"]} -t {clip["duration"]:.1f} -c copy "{output_dir}/{clip["filename"]}"'
            ffmpeg_commands.append(cmd)
        
        # 배치 파일 생성
        batch_file = Path(output_dir) / "extract_clips.bat"
        batch_content = "\n".join(ffmpeg_commands)
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # 클립 정보 JSON 저장
        clips_json = Path(output_dir) / "clips_info.json"
        with open(clips_json, 'w', encoding='utf-8') as f:
            json.dump(clips_info, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"클립 정보 및 추출 스크립트 생성: {output_dir}")
        
        return str(batch_file)


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='통합 분석 파이프라인')
    parser.add_argument('video_path', help='분석할 비디오 파일 경로')
    parser.add_argument('gfx_data', help='GFX 구간 분석 결과 JSON 파일')
    parser.add_argument('--output', '-o', help='결과 저장 경로 (JSON)')
    parser.add_argument('--clips-dir', '-c', help='클립 정보 저장 디렉토리')
    parser.add_argument('--config', help='설정 파일 경로')
    parser.add_argument('--debug', '-d', action='store_true', help='디버그 모드')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 파이프라인 생성
        pipeline = IntegratedAnalysisPipeline(config_path=args.config)
        
        # 통합 분석 실행
        output_path = args.output or f"{Path(args.video_path).stem}_integrated_analysis.json"
        result = pipeline.analyze_video_complete(args.video_path, args.gfx_data, output_path)
        
        # 요약 보고서 출력
        summary = pipeline.generate_summary_report(result)
        print(summary)
        
        # 클립 정보 생성
        if args.clips_dir:
            Path(args.clips_dir).mkdir(exist_ok=True)
            batch_file = pipeline.export_hand_clips_info(result, args.clips_dir)
            print(f"\n📁 클립 추출 스크립트: {batch_file}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())