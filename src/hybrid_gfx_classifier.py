"""
하이브리드 GFX 분류기
컴퓨터 비전 + OCR 텍스트 분석을 결합한 고정확도 GFX 오버레이 감지 시스템
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
import json
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import time
from collections import defaultdict

from gfx_text_analyzer import GFXTextAnalyzer, TextFeature

@dataclass
class VisualFeature:
    """시각적 특징 정보"""
    color_uniformity: float
    edge_density: float
    text_density: float
    layout_score: float
    contrast_level: float
    brightness_mean: float
    saturation_variance: float

@dataclass
class HybridClassification:
    """하이브리드 분류 결과"""
    is_gfx: bool
    confidence: float
    visual_score: float
    text_score: float
    method: str
    
    # 세부 정보
    visual_features: VisualFeature
    text_features_count: int
    poker_relevance: float
    processing_time: float
    
    # 디버깅 정보
    debug_info: Dict

class HybridGFXClassifier:
    """하이브리드 GFX 분류기 - 비전 + OCR 융합"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # OCR 텍스트 분석기
        self.text_analyzer = GFXTextAnalyzer(config_path)
        
        # 시각적 특징 추출 설정
        self.visual_config = {
            'blur_kernel_size': 5,
            'edge_threshold1': 50,
            'edge_threshold2': 150,
            'color_bins': 32,
            'min_contour_area': 100,
            'uniformity_threshold': 0.15,
            'text_density_weight': 0.3,
            'layout_weight': 0.4,
            'color_weight': 0.3
        }
        
        # 학습된 특징 통계
        self.feature_stats = {
            'gfx': {
                'color_uniformity': {'mean': 0.7, 'std': 0.2},
                'edge_density': {'mean': 0.15, 'std': 0.1},
                'text_density': {'mean': 0.05, 'std': 0.03},
                'layout_score': {'mean': 0.6, 'std': 0.2},
                'poker_relevance': {'mean': 0.8, 'std': 0.2}
            },
            'game': {
                'color_uniformity': {'mean': 0.3, 'std': 0.2},
                'edge_density': {'mean': 0.4, 'std': 0.2},
                'text_density': {'mean': 0.01, 'std': 0.02},
                'layout_score': {'mean': 0.2, 'std': 0.2},
                'poker_relevance': {'mean': 0.1, 'std': 0.1}
            }
        }
        
        # 분류 임계값
        self.thresholds = {
            'visual_threshold': 0.6,
            'text_threshold': 0.5,
            'hybrid_threshold': 0.65,
            'confidence_weight': 0.7  # 시각적 vs 텍스트 가중치
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
            
            if 'visual_config' in config:
                self.visual_config.update(config['visual_config'])
            
            if 'feature_stats' in config:
                self.feature_stats.update(config['feature_stats'])
            
            if 'thresholds' in config:
                self.thresholds.update(config['thresholds'])
                
            self.logger.info(f"하이브리드 분류기 설정 로드 완료: {config_path}")
            
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
    
    def extract_visual_features(self, frame: np.ndarray) -> VisualFeature:
        """시각적 특징 추출"""
        try:
            # 색상 공간 변환
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) if len(frame.shape) == 3 else cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV)
            
            height, width = gray.shape
            total_pixels = height * width
            
            # 1. 색상 균일성 계산
            color_uniformity = self._calculate_color_uniformity(hsv)
            
            # 2. 엣지 밀도 계산
            edges = cv2.Canny(gray, 
                            self.visual_config['edge_threshold1'], 
                            self.visual_config['edge_threshold2'])
            edge_density = np.sum(edges > 0) / total_pixels
            
            # 3. 텍스트 영역 밀도 (형태학적 연산 기반)
            text_density = self._estimate_text_density(gray)
            
            # 4. 레이아웃 점수 (구조적 특징)
            layout_score = self._calculate_layout_score(gray, edges)
            
            # 5. 대비 수준
            contrast_level = np.std(gray) / 255.0
            
            # 6. 평균 밝기
            brightness_mean = np.mean(gray) / 255.0
            
            # 7. 채도 분산
            saturation_variance = np.var(hsv[:, :, 1]) / (255.0 ** 2)
            
            return VisualFeature(
                color_uniformity=color_uniformity,
                edge_density=edge_density,
                text_density=text_density,
                layout_score=layout_score,
                contrast_level=contrast_level,
                brightness_mean=brightness_mean,
                saturation_variance=saturation_variance
            )
            
        except Exception as e:
            self.logger.error(f"시각적 특징 추출 실패: {e}")
            return VisualFeature(0, 0, 0, 0, 0, 0, 0)
    
    def _calculate_color_uniformity(self, hsv: np.ndarray) -> float:
        """색상 균일성 계산"""
        try:
            # HSV에서 색조(H) 채널 분석
            hue = hsv[:, :, 1]  # 채도 채널 사용 (더 안정적)
            
            # 히스토그램 계산
            hist = cv2.calcHist([hue], [0], None, [self.visual_config['color_bins']], [0, 256])
            hist_norm = hist / np.sum(hist)
            
            # 엔트로피 계산 (낮을수록 균일)
            entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
            max_entropy = np.log2(self.visual_config['color_bins'])
            
            # 균일성 점수 (0-1, 높을수록 균일)
            uniformity = 1.0 - (entropy / max_entropy)
            
            return uniformity
            
        except Exception:
            return 0.0
    
    def _estimate_text_density(self, gray: np.ndarray) -> float:
        """텍스트 영역 밀도 추정 (형태학적 연산 기반)"""
        try:
            # 텍스트 후보 영역 검출
            # 1. 적응적 이진화
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # 2. 형태학적 연산으로 텍스트 라인 검출
            kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
            kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
            
            # 수평/수직 구조 강조
            horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_horizontal)
            vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_vertical)
            
            # 텍스트 후보 영역 결합
            text_candidate = cv2.bitwise_or(horizontal, vertical)
            
            # 텍스트 밀도 계산
            text_pixels = np.sum(text_candidate > 0)
            total_pixels = gray.shape[0] * gray.shape[1]
            
            return text_pixels / total_pixels
            
        except Exception:
            return 0.0
    
    def _calculate_layout_score(self, gray: np.ndarray, edges: np.ndarray) -> float:
        """레이아웃 구조 점수 계산"""
        try:
            height, width = gray.shape
            
            # 1. 윤곽선 기반 구조 분석
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 유의미한 크기의 윤곽선만 필터링
            significant_contours = [
                c for c in contours 
                if cv2.contourArea(c) > self.visual_config['min_contour_area']
            ]
            
            if not significant_contours:
                return 0.0
            
            # 2. 정렬성 점수 (수평/수직 정렬 정도)
            alignment_score = self._calculate_alignment_score(significant_contours, width, height)
            
            # 3. 대칭성 점수
            symmetry_score = self._calculate_symmetry_score(edges, width, height)
            
            # 4. 영역 분포 점수
            distribution_score = self._calculate_distribution_score(significant_contours, width, height)
            
            # 종합 레이아웃 점수
            layout_score = (alignment_score * 0.4 + 
                          symmetry_score * 0.3 + 
                          distribution_score * 0.3)
            
            return layout_score
            
        except Exception:
            return 0.0
    
    def _calculate_alignment_score(self, contours: List, width: int, height: int) -> float:
        """윤곽선들의 정렬 점수 계산"""
        if len(contours) < 2:
            return 0.0
        
        try:
            # 각 윤곽선의 중심점과 경계 상자 계산
            centers = []
            boxes = []
            
            for contour in contours:
                M = cv2.moments(contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    centers.append((cx, cy))
                    boxes.append(cv2.boundingRect(contour))
            
            if len(centers) < 2:
                return 0.0
            
            # 수평 정렬 점수 (y 좌표 분산)
            y_coords = [center[1] for center in centers]
            y_variance = np.var(y_coords) / (height ** 2)
            horizontal_alignment = np.exp(-y_variance * 10)  # 낮은 분산일수록 높은 점수
            
            # 수직 정렬 점수 (x 좌표 분산)
            x_coords = [center[0] for center in centers]
            x_variance = np.var(x_coords) / (width ** 2)
            vertical_alignment = np.exp(-x_variance * 10)
            
            return max(horizontal_alignment, vertical_alignment)
            
        except Exception:
            return 0.0
    
    def _calculate_symmetry_score(self, edges: np.ndarray, width: int, height: int) -> float:
        """대칭성 점수 계산"""
        try:
            # 수직 대칭성 (좌우 대칭)
            left_half = edges[:, :width//2]
            right_half = np.fliplr(edges[:, width//2:])
            
            # 크기 맞추기
            min_width = min(left_half.shape[1], right_half.shape[1])
            left_half = left_half[:, :min_width]
            right_half = right_half[:, :min_width]
            
            # 대칭성 계산 (유사도)
            if left_half.size > 0 and right_half.size > 0:
                similarity = np.sum(left_half == right_half) / left_half.size
                return similarity
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _calculate_distribution_score(self, contours: List, width: int, height: int) -> float:
        """윤곽선 분포 점수 계산"""
        if not contours:
            return 0.0
        
        try:
            # 이미지를 그리드로 나누어 분포 분석
            grid_size = 3
            grid_counts = np.zeros((grid_size, grid_size))
            
            for contour in contours:
                # 윤곽선 중심점 계산
                M = cv2.moments(contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    
                    # 그리드 위치 결정
                    grid_x = min(cx * grid_size // width, grid_size - 1)
                    grid_y = min(cy * grid_size // height, grid_size - 1)
                    
                    grid_counts[grid_y, grid_x] += 1
            
            # 분포 균등성 계산 (엔트로피 기반)
            total = np.sum(grid_counts)
            if total > 0:
                probs = grid_counts.flatten() / total
                probs = probs[probs > 0]  # 0이 아닌 확률만
                entropy = -np.sum(probs * np.log2(probs))
                max_entropy = np.log2(grid_size * grid_size)
                return entropy / max_entropy if max_entropy > 0 else 0
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def classify_frame(self, frame: np.ndarray, 
                      use_visual: bool = True, 
                      use_text: bool = True) -> HybridClassification:
        """하이브리드 프레임 분류"""
        start_time = time.time()
        debug_info = {}
        
        # 기본값
        visual_score = 0.0
        text_score = 0.0
        visual_features = None
        text_features_count = 0
        poker_relevance = 0.0
        
        try:
            # 1. 시각적 특징 분석
            if use_visual:
                visual_features = self.extract_visual_features(frame)
                visual_score = self._calculate_visual_score(visual_features)
                debug_info['visual_features'] = asdict(visual_features)
            
            # 2. 텍스트 특징 분석
            if use_text:
                text_result = self.text_analyzer.classify_frame_by_text(frame, visual_score)
                text_score = text_result['text_score']
                text_features_count = text_result['text_features_count']
                poker_relevance = text_result['poker_analysis']['poker_score']
                debug_info['text_analysis'] = text_result['poker_analysis']
                debug_info['density_features'] = text_result['density_features']
            
            # 3. 하이브리드 점수 계산
            if use_visual and use_text:
                # 두 점수 모두 사용
                confidence = (visual_score * self.thresholds['confidence_weight'] + 
                            text_score * (1 - self.thresholds['confidence_weight']))
                method = 'hybrid'
            elif use_visual:
                # 시각적 분석만
                confidence = visual_score
                method = 'visual_only'
            elif use_text:
                # 텍스트 분석만
                confidence = text_score
                method = 'text_only'
            else:
                raise ValueError("최소 하나의 분석 방법이 활성화되어야 합니다")
            
            # 4. 최종 분류 결정
            is_gfx = confidence >= self.thresholds['hybrid_threshold']
            
            # 5. 신뢰도 보정 (특징 일관성 기반)
            confidence = self._adjust_confidence(confidence, visual_features, 
                                               text_features_count, poker_relevance)
            
            processing_time = time.time() - start_time
            debug_info['processing_time'] = processing_time
            
            return HybridClassification(
                is_gfx=is_gfx,
                confidence=confidence,
                visual_score=visual_score,
                text_score=text_score,
                method=method,
                visual_features=visual_features or VisualFeature(0, 0, 0, 0, 0, 0, 0),
                text_features_count=text_features_count,
                poker_relevance=poker_relevance,
                processing_time=processing_time,
                debug_info=debug_info
            )
            
        except Exception as e:
            self.logger.error(f"프레임 분류 실패: {e}")
            return HybridClassification(
                is_gfx=False,
                confidence=0.0,
                visual_score=0.0,
                text_score=0.0,
                method='error',
                visual_features=VisualFeature(0, 0, 0, 0, 0, 0, 0),
                text_features_count=0,
                poker_relevance=0.0,
                processing_time=time.time() - start_time,
                debug_info={'error': str(e)}
            )
    
    def _calculate_visual_score(self, features: VisualFeature) -> float:
        """시각적 특징을 점수로 변환"""
        try:
            # 각 특징을 GFX 프로필과 비교하여 점수 계산
            scores = []
            
            # 색상 균일성 점수 (GFX는 높은 균일성)
            color_score = features.color_uniformity
            scores.append(color_score * 0.25)
            
            # 엣지 밀도 점수 (GFX는 중간 정도의 엣지 밀도)
            edge_optimal = 0.15  # 최적 엣지 밀도
            edge_score = 1.0 - abs(features.edge_density - edge_optimal) / edge_optimal
            edge_score = max(0, edge_score)
            scores.append(edge_score * 0.2)
            
            # 텍스트 밀도 점수 (GFX는 적당한 텍스트 밀도)
            text_optimal = 0.05
            text_score = 1.0 - abs(features.text_density - text_optimal) / text_optimal
            text_score = max(0, min(1, text_score))
            scores.append(text_score * 0.2)
            
            # 레이아웃 점수 (GFX는 구조적)
            layout_score = features.layout_score
            scores.append(layout_score * 0.25)
            
            # 대비 점수 (GFX는 높은 대비)
            contrast_score = min(features.contrast_level * 2, 1.0)  # 0.5 이상이면 만점
            scores.append(contrast_score * 0.1)
            
            return sum(scores)
            
        except Exception:
            return 0.0
    
    def _adjust_confidence(self, base_confidence: float, 
                         visual_features: Optional[VisualFeature],
                         text_count: int, poker_relevance: float) -> float:
        """특징 일관성을 기반으로 신뢰도 조정"""
        try:
            adjustment = 0.0
            
            # 텍스트와 시각적 특징의 일관성 검사
            if visual_features and text_count > 0:
                # 텍스트 밀도와 실제 텍스트 검출 수의 일관성
                expected_text_count = visual_features.text_density * 1000  # 대략적 추정
                consistency = 1.0 - abs(text_count - expected_text_count) / max(text_count, expected_text_count, 1)
                adjustment += consistency * 0.1
            
            # 포커 관련성이 높으면 보너스
            if poker_relevance > 0.7:
                adjustment += 0.05
            elif poker_relevance > 0.5:
                adjustment += 0.02
            
            # 시각적 특징들 간의 일관성
            if visual_features:
                # 높은 색상 균일성 + 적당한 텍스트 밀도 = GFX 가능성 높음
                if (visual_features.color_uniformity > 0.6 and 
                    0.02 < visual_features.text_density < 0.1):
                    adjustment += 0.05
                
                # 좋은 레이아웃 + 적당한 대비 = GFX 가능성 높음
                if (visual_features.layout_score > 0.5 and 
                    visual_features.contrast_level > 0.3):
                    adjustment += 0.03
            
            # 최종 신뢰도는 0-1 범위로 클리핑
            final_confidence = base_confidence + adjustment
            return max(0.0, min(1.0, final_confidence))
            
        except Exception:
            return base_confidence
    
    def analyze_video_segment(self, video_path: str, start_time: float, 
                            end_time: float, frame_skip: int = 30) -> List[HybridClassification]:
        """비디오 구간의 하이브리드 분석"""
        self.logger.info(f"비디오 구간 분석: {start_time:.1f}s - {end_time:.1f}s")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        results = []
        
        try:
            current_time = start_time
            frame_count = 0
            
            while current_time < end_time:
                # 특정 시간으로 이동
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # 하이브리드 분류 수행
                classification = self.classify_frame(frame)
                classification.debug_info['timestamp'] = current_time
                
                results.append(classification)
                
                current_time += frame_skip / fps
                frame_count += 1
                
                if frame_count % 10 == 0:
                    progress = (current_time - start_time) / (end_time - start_time) * 100
                    self.logger.debug(f"분석 진행률: {progress:.1f}%")
        
        finally:
            cap.release()
        
        self.logger.info(f"구간 분석 완료: {len(results)}개 프레임 분석")
        return results
    
    def save_model(self, output_path: str, samples: List[Dict]):
        """하이브리드 모델 저장"""
        model_data = {
            'model_type': 'hybrid_gfx_classifier',
            'version': '1.0',
            'visual_config': self.visual_config,
            'feature_stats': self.feature_stats,
            'thresholds': self.thresholds,
            'samples_count': len(samples),
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # GFX 텍스트 프로필도 포함
        if self.text_analyzer.gfx_profile:
            profile_dict = asdict(self.text_analyzer.gfx_profile)
            profile_dict['common_keywords'] = list(self.text_analyzer.gfx_profile.common_keywords)
            model_data['gfx_text_profile'] = profile_dict
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"하이브리드 모델 저장 완료: {output_path}")
    
    def load_model(self, model_path: str):
        """하이브리드 모델 로드"""
        with open(model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        if model_data.get('model_type') != 'hybrid_gfx_classifier':
            raise ValueError("잘못된 모델 타입입니다")
        
        # 설정 로드
        self.visual_config.update(model_data.get('visual_config', {}))
        self.feature_stats.update(model_data.get('feature_stats', {}))
        self.thresholds.update(model_data.get('thresholds', {}))
        
        # GFX 텍스트 프로필 로드
        if 'gfx_text_profile' in model_data:
            from gfx_text_analyzer import GFXTextProfile
            profile_dict = model_data['gfx_text_profile']
            profile_dict['common_keywords'] = set(profile_dict['common_keywords'])
            self.text_analyzer.gfx_profile = GFXTextProfile(**profile_dict)
        
        self.logger.info(f"하이브리드 모델 로드 완료: {model_path}")


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='하이브리드 GFX 분류기')
    parser.add_argument('image_path', help='분석할 이미지 파일 경로')
    parser.add_argument('--visual-only', action='store_true', help='시각적 분석만 사용')
    parser.add_argument('--text-only', action='store_true', help='텍스트 분석만 사용')
    parser.add_argument('--output', '-o', help='결과 저장 경로')
    parser.add_argument('--model', '-m', help='모델 파일 경로')
    parser.add_argument('--debug', '-d', action='store_true', help='디버그 모드')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 하이브리드 분류기 생성
        classifier = HybridGFXClassifier()
        
        # 모델 로드 (있는 경우)
        if args.model and Path(args.model).exists():
            classifier.load_model(args.model)
        
        # 이미지 로드
        frame = cv2.imread(args.image_path)
        if frame is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {args.image_path}")
        
        # 분석 모드 설정
        use_visual = not args.text_only
        use_text = not args.visual_only
        
        # 하이브리드 분류 수행
        result = classifier.classify_frame(frame, use_visual, use_text)
        
        # 결과 출력
        print(f"\n🎯 하이브리드 GFX 분류 결과:")
        print(f"• GFX 여부: {'✅ GFX' if result.is_gfx else '❌ Game'}")
        print(f"• 신뢰도: {result.confidence:.3f}")
        print(f"• 시각적 점수: {result.visual_score:.3f}")
        print(f"• 텍스트 점수: {result.text_score:.3f}")
        print(f"• 분석 방법: {result.method}")
        print(f"• 처리 시간: {result.processing_time:.3f}초")
        print(f"• 포커 관련성: {result.poker_relevance:.3f}")
        print(f"• 텍스트 개수: {result.text_features_count}")
        
        if result.visual_features:
            print(f"\n📊 시각적 특징:")
            print(f"• 색상 균일성: {result.visual_features.color_uniformity:.3f}")
            print(f"• 엣지 밀도: {result.visual_features.edge_density:.3f}")
            print(f"• 텍스트 밀도: {result.visual_features.text_density:.3f}")
            print(f"• 레이아웃 점수: {result.visual_features.layout_score:.3f}")
        
        # 결과 저장
        if args.output:
            result_data = asdict(result)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 결과 저장: {args.output}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())