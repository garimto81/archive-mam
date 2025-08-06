"""
팟 사이즈 OCR 분석 모듈
포커 영상에서 팟 사이즈 정보를 자동으로 추출하는 모듈
"""

import cv2
import numpy as np
import pytesseract
import re
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Tesseract 실행 파일 경로 설정 (Windows 기본 경로)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@dataclass
class PotSizeReading:
    """팟 사이즈 읽기 결과"""
    timestamp: float
    raw_text: str
    cleaned_text: str
    pot_value: Optional[float]
    confidence: float
    roi_coords: Tuple[int, int, int, int]

@dataclass
class ROIRegion:
    """관심 영역 정의"""
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str

class PotSizeOCR:
    """팟 사이즈 OCR 분석기"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # 기본 ROI 영역들 (일반적인 포커 UI 위치)
        self.roi_regions = [
            ROIRegion("center_pot", 300, 200, 240, 60, "화면 중앙 팟 사이즈"),
            ROIRegion("top_center", 300, 50, 240, 40, "상단 중앙 팟 사이즈"),
            ROIRegion("bottom_center", 300, 350, 240, 40, "하단 중앙 팟 사이즈"),
        ]
        
        # OCR 설정
        self.tesseract_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789$,.KMB'
        
        # 팟 사이즈 패턴 정규표현식
        self.pot_patterns = [
            r'\$?([\d,]+(?:\.\d{2})?)\s*[KMB]?',  # $1,234.56K 형태
            r'POT:?\s*\$?([\d,]+(?:\.\d{2})?)\s*[KMB]?',  # POT: $1,234 형태
            r'([\d,]+(?:\.\d{2})?)\s*BB',  # 1,234 BB 형태
            r'Total:?\s*\$?([\d,]+(?:\.\d{2})?)',  # Total: $1,234 형태
        ]
        
        # 숫자 승수 매핑
        self.multipliers = {
            'K': 1000,
            'M': 1000000,
            'B': 1000000000,
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
            
            # ROI 영역 업데이트
            if 'roi_regions' in config:
                self.roi_regions = [
                    ROIRegion(**region) for region in config['roi_regions']
                ]
            
            # OCR 설정 업데이트
            if 'tesseract_config' in config:
                self.tesseract_config = config['tesseract_config']
                
            self.logger.info(f"설정 파일 로드 완료: {config_path}")
            
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """프레임 전처리"""
        # 그레이스케일 변환
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 대비 향상
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 이진화 (텍스트 인식용)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def extract_roi(self, frame: np.ndarray, roi: ROIRegion) -> np.ndarray:
        """ROI 영역 추출"""
        h, w = frame.shape[:2]
        
        # 좌표 범위 체크
        x1 = max(0, roi.x)
        y1 = max(0, roi.y)
        x2 = min(w, roi.x + roi.width)
        y2 = min(h, roi.y + roi.height)
        
        return frame[y1:y2, x1:x2]
    
    def perform_ocr(self, roi_image: np.ndarray) -> Tuple[str, float]:
        """OCR 수행"""
        try:
            # 이미지 크기가 너무 작으면 확대
            h, w = roi_image.shape[:2]
            if h < 30 or w < 100:
                scale_factor = max(30 / h, 100 / w)
                new_h, new_w = int(h * scale_factor), int(w * scale_factor)
                roi_image = cv2.resize(roi_image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            
            # OCR 수행
            data = pytesseract.image_to_data(roi_image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
            
            # 텍스트 추출 및 신뢰도 계산
            text_parts = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 30:  # 신뢰도 30 이상만
                    text = data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(int(data['conf'][i]))
            
            full_text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0
            
            return full_text, avg_confidence
            
        except Exception as e:
            self.logger.error(f"OCR 실패: {e}")
            return "", 0.0
    
    def clean_and_parse_pot_text(self, raw_text: str) -> Tuple[str, Optional[float]]:
        """팟 텍스트 정제 및 파싱"""
        if not raw_text:
            return "", None
        
        # 텍스트 정규화
        cleaned = raw_text.upper().replace(' ', '').replace('O', '0')
        
        # 패턴 매칭
        for pattern in self.pot_patterns:
            match = re.search(pattern, cleaned)
            if match:
                number_str = match.group(1)
                
                # 승수 확인 (K, M, B)
                multiplier = 1
                for suffix, mult in self.multipliers.items():
                    if suffix in cleaned:
                        multiplier = mult
                        break
                
                try:
                    # 쉼표 제거 후 숫자 변환
                    value = float(number_str.replace(',', '')) * multiplier
                    return number_str + ('K' if multiplier == 1000 else 'M' if multiplier == 1000000 else 'B' if multiplier == 1000000000 else ''), value
                except ValueError:
                    continue
        
        return cleaned, None
    
    def analyze_frame(self, frame: np.ndarray, timestamp: float) -> List[PotSizeReading]:
        """단일 프레임 분석"""
        readings = []
        preprocessed = self.preprocess_frame(frame)
        
        for roi in self.roi_regions:
            try:
                # ROI 추출
                roi_image = self.extract_roi(preprocessed, roi)
                if roi_image.size == 0:
                    continue
                
                # OCR 수행
                raw_text, confidence = self.perform_ocr(roi_image)
                
                # 텍스트 정제 및 파싱
                cleaned_text, pot_value = self.clean_and_parse_pot_text(raw_text)
                
                # 결과 저장
                reading = PotSizeReading(
                    timestamp=timestamp,
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    pot_value=pot_value,
                    confidence=confidence,
                    roi_coords=(roi.x, roi.y, roi.width, roi.height)
                )
                
                readings.append(reading)
                
                if pot_value and confidence > 50:
                    self.logger.info(f"팟 사이즈 감지: ${pot_value:,.2f} (신뢰도: {confidence:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"ROI {roi.name} 분석 실패: {e}")
                continue
        
        return readings
    
    def analyze_video(self, video_path: str, output_path: Optional[str] = None, 
                     frame_skip: int = 30) -> List[PotSizeReading]:
        """비디오 전체 분석"""
        self.logger.info(f"비디오 분석 시작: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        self.logger.info(f"비디오 정보: {duration:.1f}초, {fps:.1f}fps, {total_frames}프레임")
        
        all_readings = []
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 지정된 간격으로만 분석
                if frame_count % frame_skip == 0:
                    timestamp = frame_count / fps
                    readings = self.analyze_frame(frame, timestamp)
                    all_readings.extend(readings)
                    
                    # 진행률 표시
                    if frame_count % (frame_skip * 10) == 0:
                        progress = (frame_count / total_frames) * 100
                        self.logger.info(f"진행률: {progress:.1f}% ({frame_count}/{total_frames})")
                
                frame_count += 1
        
        finally:
            cap.release()
        
        self.logger.info(f"분석 완료: 총 {len(all_readings)}개 읽기 결과")
        
        # 결과 저장
        if output_path:
            self.save_results(all_readings, output_path)
        
        return all_readings
    
    def save_results(self, readings: List[PotSizeReading], output_path: str):
        """결과를 JSON 파일로 저장"""
        results = {
            'analysis_type': 'pot_size_ocr',
            'timestamp': cv2.getTickCount(),
            'total_readings': len(readings),
            'readings': [asdict(reading) for reading in readings]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"결과 저장 완료: {output_path}")
    
    def get_pot_timeline(self, readings: List[PotSizeReading], 
                        min_confidence: float = 50.0) -> List[Dict]:
        """팟 사이즈 타임라인 생성"""
        timeline = []
        
        for reading in readings:
            if reading.pot_value and reading.confidence >= min_confidence:
                timeline.append({
                    'timestamp': reading.timestamp,
                    'pot_size': reading.pot_value,
                    'confidence': reading.confidence,
                    'formatted_time': f"{int(reading.timestamp // 60):02d}:{int(reading.timestamp % 60):02d}"
                })
        
        # 시간순 정렬
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def detect_pot_changes(self, readings: List[PotSizeReading], 
                          threshold_percent: float = 10.0) -> List[Dict]:
        """팟 사이즈 변화 감지"""
        timeline = self.get_pot_timeline(readings)
        changes = []
        
        if len(timeline) < 2:
            return changes
        
        prev_pot = timeline[0]['pot_size']
        
        for entry in timeline[1:]:
            current_pot = entry['pot_size']
            change_percent = abs(current_pot - prev_pot) / prev_pot * 100
            
            if change_percent >= threshold_percent:
                changes.append({
                    'timestamp': entry['timestamp'],
                    'formatted_time': entry['formatted_time'],
                    'previous_pot': prev_pot,
                    'current_pot': current_pot,
                    'change_amount': current_pot - prev_pot,
                    'change_percent': change_percent
                })
                prev_pot = current_pot
        
        return changes


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='팟 사이즈 OCR 분석기')
    parser.add_argument('video_path', help='분석할 비디오 파일 경로')
    parser.add_argument('--output', '-o', help='결과 저장 경로 (JSON)')
    parser.add_argument('--frame-skip', '-s', type=int, default=30, 
                       help='프레임 스킵 간격 (기본: 30)')
    parser.add_argument('--config', '-c', help='설정 파일 경로')
    parser.add_argument('--debug', '-d', action='store_true', help='디버그 모드')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # OCR 분석기 생성
        analyzer = PotSizeOCR(config_path=args.config)
        
        # 비디오 분석
        output_path = args.output or f"{Path(args.video_path).stem}_pot_analysis.json"
        readings = analyzer.analyze_video(args.video_path, output_path, args.frame_skip)
        
        # 결과 요약
        timeline = analyzer.get_pot_timeline(readings)
        changes = analyzer.detect_pot_changes(readings)
        
        print(f"\n📊 분석 결과 요약:")
        print(f"• 총 읽기 횟수: {len(readings)}")
        print(f"• 유효한 팟 사이즈: {len(timeline)}")
        print(f"• 팟 변화 감지: {len(changes)}회")
        
        if timeline:
            print(f"• 최소 팟: ${min(t['pot_size'] for t in timeline):,.2f}")
            print(f"• 최대 팟: ${max(t['pot_size'] for t in timeline):,.2f}")
        
        if changes:
            print(f"\n🔄 주요 팟 변화:")
            for change in changes[:5]:  # 상위 5개만 표시
                print(f"  {change['formatted_time']}: ${change['previous_pot']:,.0f} → ${change['current_pot']:,.0f}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())