"""
GFX 텍스트 분석기 - OCR 기반 GFX 오버레이 감지
포커 방송의 GFX 오버레이에 포함된 텍스트 정보를 분석하여 더 정확한 감지 수행
"""

import cv2
import numpy as np
import pytesseract
import re
from typing import List, Dict, Tuple, Optional, Set
import json
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from collections import Counter, defaultdict
import string

# Tesseract 실행 파일 경로 설정 (Windows 기본 경로)
# pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

@dataclass
class TextFeature:
    """텍스트 특징 정보"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    char_count: int
    word_count: int
    digit_ratio: float
    symbol_ratio: float
    area_ratio: float

@dataclass
class GFXTextProfile:
    """GFX 텍스트 프로필"""
    common_keywords: Set[str]
    typical_patterns: List[str]
    text_density_range: Tuple[float, float]
    avg_confidence: float
    char_distribution: Dict[str, float]
    spatial_distribution: Dict[str, List[Tuple[int, int]]]

class GFXTextAnalyzer:
    """GFX 텍스트 분석기 - OCR 기반 특징 추출"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # 포커 GFX에서 자주 나타나는 키워드
        self.poker_keywords = {
            # 기본 용어
            'pot', 'call', 'raise', 'fold', 'check', 'all', 'in', 'allin',
            'bet', 'blind', 'ante', 'stack', 'chips', 'bb', 'sb',
            
            # 카드 관련
            'hole', 'cards', 'flop', 'turn', 'river', 'showdown',
            'straight', 'flush', 'full', 'house', 'pair', 'high',
            
            # 액션/결과
            'wins', 'loses', 'split', 'side', 'main', 'eliminate',
            'double', 'triple', 'quad', 'royal',
            
            # 숫자/기호 패턴
            '$', '₩', '€', '£', '%', 'k', 'm', 'bb', 'x'
        }
        
        # 일반 게임 화면에서 나타나는 키워드 (제외 대상)
        self.game_keywords = {
            'player', 'table', 'seat', 'join', 'leave', 'wait',
            'lobby', 'tournament', 'cash', 'game', 'level',
            'time', 'break', 'pause', 'resume', 'exit'
        }
        
        # OCR 설정
        self.ocr_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$€£₩%.,:-+xKMB'
        
        # 텍스트 패턴 (정규식)
        self.patterns = {
            'money': r'[\$€£₩]\s*[\d,]+(?:\.\d{2})?[KMB]?',
            'percentage': r'\d+(?:\.\d+)?%',
            'ratio': r'\d+:\d+',
            'card': r'[AKQJT2-9][hdcs]',
            'time': r'\d{1,2}:\d{2}(?::\d{2})?',
            'big_blind': r'\d+(?:\.\d+)?\s*BB',
        }
        
        # 학습된 GFX 텍스트 프로필
        self.gfx_profile = None
        
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
            
            if 'gfx_text_profile' in config:
                profile_data = config['gfx_text_profile']
                self.gfx_profile = GFXTextProfile(**profile_data)
                
            self.logger.info(f"GFX 텍스트 설정 로드 완료: {config_path}")
            
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
    
    def preprocess_for_ocr(self, frame: np.ndarray) -> List[np.ndarray]:
        """OCR을 위한 프레임 전처리 (여러 버전 생성)"""
        preprocessed = []
        
        # 1. 원본 그레이스케일
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame.copy()
        preprocessed.append(gray)
        
        # 2. 대비 향상
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        preprocessed.append(enhanced)
        
        # 3. 이진화 (OTSU)
        _, binary1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed.append(binary1)
        
        # 4. 이진화 (적응적)
        binary2 = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        preprocessed.append(binary2)
        
        # 5. 엣지 강조
        edges = cv2.Canny(enhanced, 50, 150)
        preprocessed.append(edges)
        
        return preprocessed
    
    def extract_text_features(self, frame: np.ndarray) -> List[TextFeature]:
        """프레임에서 텍스트 특징 추출"""
        features = []
        frame_area = frame.shape[0] * frame.shape[1]
        
        try:
            # 여러 전처리 버전으로 OCR 수행
            preprocessed_frames = self.preprocess_for_ocr(frame)
            
            all_detections = []
            
            for proc_frame in preprocessed_frames:
                try:
                    # OCR 데이터 추출
                    data = pytesseract.image_to_data(
                        proc_frame, 
                        config=self.ocr_config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # 유효한 텍스트만 수집
                    for i in range(len(data['text'])):
                        if int(data['conf'][i]) > 30:  # 신뢰도 30 이상
                            text = data['text'][i].strip()
                            if len(text) >= 2:  # 2글자 이상
                                bbox = (
                                    int(data['left'][i]),
                                    int(data['top'][i]),
                                    int(data['width'][i]),
                                    int(data['height'][i])
                                )
                                all_detections.append({
                                    'text': text,
                                    'confidence': int(data['conf'][i]),
                                    'bbox': bbox
                                })
                                
                except Exception as e:
                    self.logger.debug(f"OCR 처리 실패 (전처리 버전): {e}")
                    continue
            
            # 중복 제거 및 특징 계산
            unique_texts = self._remove_duplicate_detections(all_detections)
            
            for detection in unique_texts:
                text = detection['text']
                confidence = detection['confidence']
                bbox = detection['bbox']
                
                # 텍스트 특징 계산
                char_count = len(text)
                word_count = len(text.split())
                
                # 숫자 비율
                digit_count = sum(1 for c in text if c.isdigit())
                digit_ratio = digit_count / char_count if char_count > 0 else 0
                
                # 기호 비율
                symbol_count = sum(1 for c in text if c in string.punctuation)
                symbol_ratio = symbol_count / char_count if char_count > 0 else 0
                
                # 영역 비율
                text_area = bbox[2] * bbox[3]
                area_ratio = text_area / frame_area
                
                feature = TextFeature(
                    text=text,
                    confidence=confidence / 100.0,  # 0-1 범위로 정규화
                    bbox=bbox,
                    char_count=char_count,
                    word_count=word_count,
                    digit_ratio=digit_ratio,
                    symbol_ratio=symbol_ratio,
                    area_ratio=area_ratio
                )
                
                features.append(feature)
                
        except Exception as e:
            self.logger.error(f"텍스트 특징 추출 실패: {e}")
        
        return features
    
    def _remove_duplicate_detections(self, detections: List[Dict]) -> List[Dict]:
        """중복된 텍스트 검출 제거"""
        if not detections:
            return []
        
        # 텍스트와 위치 기반으로 그룹화
        groups = defaultdict(list)
        
        for detection in detections:
            text = detection['text'].lower()
            x, y = detection['bbox'][:2]
            # 근접한 위치의 같은 텍스트를 그룹화
            key = (text, x // 10, y // 10)  # 10픽셀 단위로 그룹화
            groups[key].append(detection)
        
        # 각 그룹에서 가장 신뢰도가 높은 것 선택
        unique_detections = []
        for group in groups.values():
            best = max(group, key=lambda x: x['confidence'])
            unique_detections.append(best)
        
        return unique_detections
    
    def analyze_poker_relevance(self, features: List[TextFeature]) -> Dict:
        """텍스트 특징의 포커 관련성 분석"""
        if not features:
            return {
                'poker_score': 0.0,
                'keyword_matches': [],
                'pattern_matches': [],
                'total_confidence': 0.0
            }
        
        keyword_matches = []
        pattern_matches = []
        total_confidence = 0.0
        
        for feature in features:
            text_lower = feature.text.lower()
            total_confidence += feature.confidence
            
            # 포커 키워드 매칭
            for keyword in self.poker_keywords:
                if keyword in text_lower:
                    keyword_matches.append({
                        'keyword': keyword,
                        'text': feature.text,
                        'confidence': feature.confidence,
                        'bbox': feature.bbox
                    })
            
            # 패턴 매칭
            for pattern_name, pattern in self.patterns.items():
                matches = re.findall(pattern, feature.text, re.IGNORECASE)
                if matches:
                    pattern_matches.append({
                        'pattern': pattern_name,
                        'matches': matches,
                        'text': feature.text,
                        'confidence': feature.confidence
                    })
        
        # 포커 점수 계산
        keyword_score = len(keyword_matches) * 0.3
        pattern_score = len(pattern_matches) * 0.4
        confidence_score = (total_confidence / len(features)) * 0.3 if features else 0
        
        poker_score = min(keyword_score + pattern_score + confidence_score, 1.0)
        
        return {
            'poker_score': poker_score,
            'keyword_matches': keyword_matches,
            'pattern_matches': pattern_matches,
            'total_confidence': total_confidence / len(features) if features else 0,
            'text_density': len(features)
        }
    
    def compute_text_density_features(self, features: List[TextFeature], 
                                    frame_shape: Tuple[int, int]) -> Dict:
        """텍스트 밀도 기반 특징 계산"""
        if not features:
            return {
                'text_density': 0.0,
                'avg_text_size': 0.0,
                'text_distribution': 'empty',
                'dominant_regions': []
            }
        
        height, width = frame_shape[:2]
        
        # 텍스트 밀도 계산
        total_text_area = sum(f.bbox[2] * f.bbox[3] for f in features)
        frame_area = width * height
        text_density = total_text_area / frame_area
        
        # 평균 텍스트 크기
        avg_text_size = total_text_area / len(features)
        
        # 공간적 분포 분석 (그리드 기반)
        grid_size = 4
        grid_width = width // grid_size
        grid_height = height // grid_size
        
        grid_counts = np.zeros((grid_size, grid_size))
        
        for feature in features:
            x, y = feature.bbox[:2]
            grid_x = min(x // grid_width, grid_size - 1)
            grid_y = min(y // grid_height, grid_size - 1)
            grid_counts[grid_y, grid_x] += 1
        
        # 지배적인 영역 찾기
        max_count = np.max(grid_counts)
        dominant_regions = []
        
        if max_count > 0:
            for i in range(grid_size):
                for j in range(grid_size):
                    if grid_counts[i, j] >= max_count * 0.7:  # 최대값의 70% 이상
                        dominant_regions.append((j, i))  # (x, y) 순서
        
        # 분포 패턴 분류
        if len(dominant_regions) == 1:
            distribution = 'concentrated'
        elif len(dominant_regions) <= 3:
            distribution = 'clustered'
        else:
            distribution = 'distributed'
        
        return {
            'text_density': text_density,
            'avg_text_size': avg_text_size / frame_area,  # 정규화
            'text_distribution': distribution,
            'dominant_regions': dominant_regions,
            'grid_counts': grid_counts.tolist()
        }
    
    def create_gfx_text_profile(self, gfx_samples: List[Dict]) -> GFXTextProfile:
        """GFX 샘플들로부터 텍스트 프로필 생성"""
        all_keywords = []
        all_patterns = []
        all_confidences = []
        char_counter = Counter()
        spatial_positions = defaultdict(list)
        
        for sample in gfx_samples:
            if 'frame_data' not in sample:
                continue
            
            frame = sample['frame_data']
            features = self.extract_text_features(frame)
            analysis = self.analyze_poker_relevance(features)
            
            # 키워드 수집
            for match in analysis['keyword_matches']:
                all_keywords.append(match['keyword'])
            
            # 패턴 수집
            for match in analysis['pattern_matches']:
                all_patterns.append(match['pattern'])
            
            # 신뢰도 수집
            all_confidences.append(analysis['total_confidence'])
            
            # 문자 분포 수집
            for feature in features:
                for char in feature.text.lower():
                    char_counter[char] += 1
            
            # 공간적 분포 수집
            density_features = self.compute_text_density_features(features, frame.shape)
            for region in density_features['dominant_regions']:
                spatial_positions[sample.get('label', 'unknown')].append(region)
        
        # 공통 키워드 (빈도 기반)
        keyword_counter = Counter(all_keywords)
        common_keywords = set(keyword for keyword, count in keyword_counter.most_common(10))
        
        # 일반적인 패턴
        pattern_counter = Counter(all_patterns)
        typical_patterns = [pattern for pattern, count in pattern_counter.most_common(5)]
        
        # 텍스트 밀도 범위
        if all_confidences:
            min_conf = min(all_confidences)
            max_conf = max(all_confidences)
            text_density_range = (min_conf, max_conf)
            avg_confidence = sum(all_confidences) / len(all_confidences)
        else:
            text_density_range = (0.0, 0.0)
            avg_confidence = 0.0
        
        # 문자 분포 정규화
        total_chars = sum(char_counter.values())
        char_distribution = {
            char: count / total_chars 
            for char, count in char_counter.most_common(50)
        } if total_chars > 0 else {}
        
        profile = GFXTextProfile(
            common_keywords=common_keywords,
            typical_patterns=typical_patterns,
            text_density_range=text_density_range,
            avg_confidence=avg_confidence,
            char_distribution=char_distribution,
            spatial_distribution=dict(spatial_positions)
        )
        
        self.gfx_profile = profile
        self.logger.info(f"GFX 텍스트 프로필 생성 완료: {len(common_keywords)}개 키워드")
        
        return profile
    
    def classify_frame_by_text(self, frame: np.ndarray, 
                             visual_score: float = 0.5) -> Dict:
        """텍스트 분석과 시각적 분석을 결합한 프레임 분류"""
        # 텍스트 특징 추출
        text_features = self.extract_text_features(frame)
        
        # 포커 관련성 분석
        poker_analysis = self.analyze_poker_relevance(text_features)
        
        # 텍스트 밀도 특징
        density_features = self.compute_text_density_features(text_features, frame.shape)
        
        # GFX 프로필과 비교 (학습된 경우)
        profile_score = 0.0
        if self.gfx_profile:
            profile_score = self._compare_with_profile(text_features, poker_analysis)
        
        # 최종 점수 계산 (텍스트 + 시각적)
        text_score = (
            poker_analysis['poker_score'] * 0.4 +
            (poker_analysis['total_confidence'] / 100) * 0.3 +
            density_features['text_density'] * 100 * 0.2 +  # 밀도 점수 조정
            profile_score * 0.1
        )
        
        # 가중 평균으로 최종 점수 계산
        final_score = (text_score * 0.6 + visual_score * 0.4)
        
        # GFX 여부 판정
        is_gfx = final_score > 0.5
        
        return {
            'is_gfx': is_gfx,
            'confidence': final_score,
            'text_score': text_score,
            'visual_score': visual_score,
            'poker_analysis': poker_analysis,
            'density_features': density_features,
            'text_features_count': len(text_features),
            'method': 'text+visual'
        }
    
    def _compare_with_profile(self, features: List[TextFeature], 
                            analysis: Dict) -> float:
        """텍스트 특징을 학습된 프로필과 비교"""
        if not self.gfx_profile or not features:
            return 0.0
        
        score = 0.0
        
        # 키워드 매칭 점수
        matched_keywords = set(match['keyword'] for match in analysis['keyword_matches'])
        keyword_overlap = len(matched_keywords & self.gfx_profile.common_keywords)
        if self.gfx_profile.common_keywords:
            score += (keyword_overlap / len(self.gfx_profile.common_keywords)) * 0.4
        
        # 신뢰도 범위 점수
        avg_conf = analysis['total_confidence']
        if (self.gfx_profile.text_density_range[0] <= avg_conf <= 
            self.gfx_profile.text_density_range[1]):
            score += 0.3
        
        # 문자 분포 유사도
        if self.gfx_profile.char_distribution:
            feature_chars = Counter()
            for feature in features:
                for char in feature.text.lower():
                    feature_chars[char] += 1
            
            total_chars = sum(feature_chars.values())
            if total_chars > 0:
                similarity = 0.0
                for char, count in feature_chars.most_common(20):
                    char_ratio = count / total_chars
                    profile_ratio = self.gfx_profile.char_distribution.get(char, 0)
                    similarity += min(char_ratio, profile_ratio)
                
                score += similarity * 0.3
        
        return min(score, 1.0)
    
    def save_profile(self, output_path: str):
        """GFX 텍스트 프로필 저장"""
        if not self.gfx_profile:
            raise ValueError("저장할 GFX 프로필이 없습니다")
        
        # Set을 list로 변환 (JSON 직렬화용)
        profile_dict = asdict(self.gfx_profile)
        profile_dict['common_keywords'] = list(self.gfx_profile.common_keywords)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile_dict, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"GFX 텍스트 프로필 저장 완료: {output_path}")
    
    def load_profile(self, profile_path: str):
        """GFX 텍스트 프로필 로드"""
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_dict = json.load(f)
        
        # list를 set으로 변환
        profile_dict['common_keywords'] = set(profile_dict['common_keywords'])
        
        self.gfx_profile = GFXTextProfile(**profile_dict)
        self.logger.info(f"GFX 텍스트 프로필 로드 완료: {profile_path}")


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GFX 텍스트 분석기')
    parser.add_argument('image_path', help='분석할 이미지 파일 경로')
    parser.add_argument('--output', '-o', help='결과 저장 경로')
    parser.add_argument('--profile', '-p', help='GFX 프로필 파일 경로')
    parser.add_argument('--debug', '-d', action='store_true', help='디버그 모드')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 텍스트 분석기 생성
        analyzer = GFXTextAnalyzer()
        
        # 프로필 로드 (있는 경우)
        if args.profile and Path(args.profile).exists():
            analyzer.load_profile(args.profile)
        
        # 이미지 로드
        frame = cv2.imread(args.image_path)
        if frame is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {args.image_path}")
        
        # 텍스트 분석 수행
        features = analyzer.extract_text_features(frame)
        poker_analysis = analyzer.analyze_poker_relevance(features)
        density_features = analyzer.compute_text_density_features(features, frame.shape)
        
        # 결과 출력
        print(f"\n📊 GFX 텍스트 분석 결과:")
        print(f"• 추출된 텍스트 수: {len(features)}")
        print(f"• 포커 관련성 점수: {poker_analysis['poker_score']:.3f}")
        print(f"• 텍스트 밀도: {density_features['text_density']:.6f}")
        print(f"• 평균 신뢰도: {poker_analysis['total_confidence']:.1f}%")
        
        if poker_analysis['keyword_matches']:
            print(f"\n🎯 매칭된 포커 키워드:")
            for match in poker_analysis['keyword_matches'][:5]:
                print(f"  - '{match['keyword']}' in '{match['text']}' (신뢰도: {match['confidence']:.1f}%)")
        
        if poker_analysis['pattern_matches']:
            print(f"\n🔍 매칭된 패턴:")
            for match in poker_analysis['pattern_matches'][:3]:
                print(f"  - {match['pattern']}: {match['matches']}")
        
        # 결과 저장
        if args.output:
            result_data = {
                'image_path': args.image_path,
                'text_features': [asdict(f) for f in features],
                'poker_analysis': poker_analysis,
                'density_features': density_features
            }
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 결과 저장: {args.output}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())