"""
Advanced UI Detection System with Machine Learning
1초에 1프레임만 분석하여 효율적이고 정교한 UI 감지
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import hashlib

class AdvancedUIDetector:
    """고급 UI 감지 시스템 - 학습 기반"""
    
    def __init__(self, fps: int = 30):
        self.fps = fps
        self.frame_interval = fps  # 1초에 1프레임 (30fps 기준 30프레임마다)
        
        # 특징 추출 설정
        self.grid_size = (3, 3)  # 9개 영역 분석
        self.color_bins = 16  # 색상 히스토그램 빈
        
        # 학습 모델
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # 데이터 저장 경로
        self.data_dir = "ui_detection_data"
        self.ensure_data_directory()
        
        # 학습 데이터
        self.training_data = []
        self.feature_names = []
        
        # UI 패턴 캐시
        self.pattern_cache = {}
        
    def ensure_data_directory(self):
        """데이터 저장 디렉토리 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "features"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "models"), exist_ok=True)
    
    def extract_features(self, frame: np.ndarray) -> Dict[str, float]:
        """프레임에서 다양한 특징 추출"""
        features = {}
        
        # 1. 전역 특징 (Global Features)
        features.update(self._extract_global_features(frame))
        
        # 2. 영역별 특징 (Regional Features)
        features.update(self._extract_regional_features(frame))
        
        # 3. 텍스처 특징 (Texture Features)
        features.update(self._extract_texture_features(frame))
        
        # 4. 엣지 특징 (Edge Features)
        features.update(self._extract_edge_features(frame))
        
        # 5. 색상 특징 (Color Features)
        features.update(self._extract_color_features(frame))
        
        return features
    
    def _extract_global_features(self, frame: np.ndarray) -> Dict[str, float]:
        """전역 특징 추출"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        features = {
            # 밝기 통계
            'global_brightness_mean': np.mean(gray),
            'global_brightness_std': np.std(gray),
            'global_brightness_min': np.min(gray),
            'global_brightness_max': np.max(gray),
            
            # 색상 다양성
            'global_hue_std': np.std(hsv[:,:,0]),
            'global_saturation_mean': np.mean(hsv[:,:,1]),
            'global_value_range': np.max(hsv[:,:,2]) - np.min(hsv[:,:,2]),
            
            # 전체 엔트로피
            'global_entropy': self._calculate_entropy(gray)
        }
        
        return features
    
    def _extract_regional_features(self, frame: np.ndarray) -> Dict[str, float]:
        """9개 영역별 특징 추출"""
        h, w = frame.shape[:2]
        cell_h = h // self.grid_size[0]
        cell_w = w // self.grid_size[1]
        
        features = {}
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        for row in range(self.grid_size[0]):
            for col in range(self.grid_size[1]):
                # 영역 추출
                y1 = row * cell_h
                y2 = (row + 1) * cell_h if row < self.grid_size[0] - 1 else h
                x1 = col * cell_w
                x2 = (col + 1) * cell_w if col < self.grid_size[1] - 1 else w
                
                region = gray[y1:y2, x1:x2]
                region_color = frame[y1:y2, x1:x2]
                
                region_id = row * self.grid_size[1] + col
                
                # 영역별 특징
                features[f'region_{region_id}_brightness'] = np.mean(region)
                features[f'region_{region_id}_std'] = np.std(region)
                features[f'region_{region_id}_entropy'] = self._calculate_entropy(region)
                
                # 색상 균일도
                color_std = np.std(region_color.reshape(-1, 3), axis=0)
                features[f'region_{region_id}_color_uniformity'] = 1.0 / (1.0 + np.mean(color_std))
                
                # 엣지 밀도
                edges = cv2.Canny(region, 50, 150)
                features[f'region_{region_id}_edge_density'] = np.count_nonzero(edges) / edges.size
        
        return features
    
    def _extract_texture_features(self, frame: np.ndarray) -> Dict[str, float]:
        """텍스처 특징 추출 (GLCM 기반)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 간단한 텍스처 분석
        features = {}
        
        # Gabor 필터 응답
        kernels = []
        for theta in [0, np.pi/4, np.pi/2, 3*np.pi/4]:
            kernel = cv2.getGaborKernel((31, 31), 4.0, theta, 10.0, 0.5, 0)
            kernels.append(kernel)
        
        for i, kernel in enumerate(kernels):
            filtered = cv2.filter2D(gray, cv2.CV_8UC3, kernel)
            features[f'texture_gabor_{i}_mean'] = np.mean(filtered)
            features[f'texture_gabor_{i}_std'] = np.std(filtered)
        
        # LBP (Local Binary Pattern) 간단 버전
        features['texture_contrast'] = self._calculate_contrast(gray)
        features['texture_homogeneity'] = self._calculate_homogeneity(gray)
        
        return features
    
    def _extract_edge_features(self, frame: np.ndarray) -> Dict[str, float]:
        """엣지 기반 특징 추출"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Canny 엣지
        edges = cv2.Canny(gray, 50, 150)
        
        # Hough 변환으로 직선 감지
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        features = {
            'edge_pixel_ratio': np.count_nonzero(edges) / edges.size,
            'edge_line_count': len(lines) if lines is not None else 0
        }
        
        if lines is not None:
            # 수평/수직 라인 분석
            h_lines = 0
            v_lines = 0
            diagonal_lines = 0
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                if angle < 10 or angle > 170:
                    h_lines += 1
                elif 80 < angle < 100:
                    v_lines += 1
                else:
                    diagonal_lines += 1
            
            features['edge_horizontal_lines'] = h_lines
            features['edge_vertical_lines'] = v_lines
            features['edge_diagonal_lines'] = diagonal_lines
            features['edge_grid_score'] = (h_lines + v_lines) / (len(lines) + 1)
        else:
            features['edge_horizontal_lines'] = 0
            features['edge_vertical_lines'] = 0
            features['edge_diagonal_lines'] = 0
            features['edge_grid_score'] = 0
        
        return features
    
    def _extract_color_features(self, frame: np.ndarray) -> Dict[str, float]:
        """색상 기반 특징 추출"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        features = {}
        
        # HSV 색상 히스토그램
        h_hist = cv2.calcHist([hsv], [0], None, [self.color_bins], [0, 180])
        h_hist = h_hist.flatten() / np.sum(h_hist)
        
        # 주요 색상 비율
        for i, ratio in enumerate(h_hist):
            features[f'color_hue_bin_{i}'] = ratio
        
        # 색상 다양성 메트릭
        features['color_hue_entropy'] = -np.sum(h_hist * np.log2(h_hist + 1e-10))
        features['color_dominant_ratio'] = np.max(h_hist)
        
        # LAB 색공간 특징
        features['color_lab_a_mean'] = np.mean(lab[:,:,1])
        features['color_lab_b_mean'] = np.mean(lab[:,:,2])
        features['color_lab_variance'] = np.var(lab.reshape(-1, 3))
        
        return features
    
    def _calculate_entropy(self, gray_region: np.ndarray) -> float:
        """영역의 엔트로피 계산"""
        hist = cv2.calcHist([gray_region], [0], None, [256], [0, 256])
        hist = hist.flatten() / np.sum(hist)
        hist = hist[hist > 0]
        return -np.sum(hist * np.log2(hist))
    
    def _calculate_contrast(self, gray: np.ndarray) -> float:
        """대비 계산"""
        min_val = np.min(gray)
        max_val = np.max(gray)
        return (max_val - min_val) / (max_val + min_val + 1e-10)
    
    def _calculate_homogeneity(self, gray: np.ndarray) -> float:
        """균일도 계산"""
        return 1.0 / (1.0 + np.std(gray))
    
    def analyze_frame(self, frame: np.ndarray, timestamp: float) -> Dict:
        """프레임 분석 및 UI 확률 계산"""
        # 특징 추출
        features = self.extract_features(frame)
        
        # 프레임 해시 (중복 방지)
        frame_hash = self._calculate_frame_hash(frame)
        
        result = {
            'timestamp': timestamp,
            'frame_hash': frame_hash,
            'features': features,
            'ui_probability': 0.0,
            'is_ui': False,
            'confidence': 0.0
        }
        
        # 학습된 모델이 있으면 예측
        if self.is_trained:
            feature_vector = self._features_to_vector(features)
            ui_probability = self.classifier.predict_proba([feature_vector])[0][1]
            
            result['ui_probability'] = ui_probability
            result['is_ui'] = ui_probability > 0.65
            result['confidence'] = max(ui_probability, 1 - ui_probability)
        
        return result
    
    def _calculate_frame_hash(self, frame: np.ndarray) -> str:
        """프레임의 고유 해시 계산"""
        # 프레임을 작게 리사이즈하여 해시 계산
        small = cv2.resize(frame, (32, 32))
        return hashlib.md5(small.tobytes()).hexdigest()
    
    def _features_to_vector(self, features: Dict[str, float]) -> np.ndarray:
        """특징 딕셔너리를 벡터로 변환"""
        if not self.feature_names:
            self.feature_names = sorted(features.keys())
        
        return np.array([features.get(name, 0) for name in self.feature_names])
    
    def save_training_sample(self, frame: np.ndarray, features: Dict, 
                           is_ui: bool, timestamp: float, video_name: str):
        """학습 샘플 저장"""
        sample_id = f"{video_name}_{timestamp:.2f}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 특징 저장
        feature_path = os.path.join(self.data_dir, "features", f"{sample_id}.json")
        with open(feature_path, 'w') as f:
            json.dump({
                'features': features,
                'is_ui': is_ui,
                'timestamp': timestamp,
                'video_name': video_name,
                'created_at': datetime.now().isoformat()
            }, f, indent=2)
        
        # 스크린샷 저장 (선택적)
        if is_ui:  # UI인 경우만 이미지 저장
            img_path = os.path.join(self.data_dir, "screenshots", f"{sample_id}.jpg")
            cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # 메모리에도 추가
        self.training_data.append({
            'features': features,
            'is_ui': is_ui,
            'timestamp': timestamp,
            'video_name': video_name
        })
    
    def load_training_data(self) -> int:
        """저장된 학습 데이터 로드"""
        feature_dir = os.path.join(self.data_dir, "features")
        loaded_count = 0
        
        for filename in os.listdir(feature_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(feature_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        self.training_data.append(data)
                        loaded_count += 1
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        return loaded_count
    
    def train_model(self, min_samples: int = 50):
        """학습 모델 훈련"""
        if len(self.training_data) < min_samples:
            raise ValueError(f"최소 {min_samples}개의 샘플이 필요합니다. 현재: {len(self.training_data)}개")
        
        # 특징과 레이블 준비
        X = []
        y = []
        
        for sample in self.training_data:
            feature_vector = self._features_to_vector(sample['features'])
            X.append(feature_vector)
            y.append(1 if sample['is_ui'] else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # 데이터 정규화
        X_scaled = self.scaler.fit_transform(X)
        
        # 모델 훈련
        self.classifier.fit(X_scaled, y)
        self.is_trained = True
        
        # 특징 중요도
        feature_importance = self.classifier.feature_importances_
        important_features = sorted(
            zip(self.feature_names, feature_importance),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        return {
            'total_samples': len(self.training_data),
            'ui_samples': sum(y),
            'non_ui_samples': len(y) - sum(y),
            'accuracy': self.classifier.score(X_scaled, y),
            'important_features': important_features
        }
    
    def save_model(self, model_name: str = "ui_detector_model"):
        """학습된 모델 저장"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        model_path = os.path.join(self.data_dir, "models", f"{model_name}.pkl")
        scaler_path = os.path.join(self.data_dir, "models", f"{model_name}_scaler.pkl")
        metadata_path = os.path.join(self.data_dir, "models", f"{model_name}_metadata.json")
        
        # 모델과 스케일러 저장
        with open(model_path, 'wb') as f:
            pickle.dump(self.classifier, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # 메타데이터 저장
        metadata = {
            'created_at': datetime.now().isoformat(),
            'feature_names': self.feature_names,
            'training_samples': len(self.training_data),
            'model_type': 'RandomForestClassifier',
            'version': '1.0'
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_model(self, model_name: str = "ui_detector_model"):
        """저장된 모델 로드"""
        model_path = os.path.join(self.data_dir, "models", f"{model_name}.pkl")
        scaler_path = os.path.join(self.data_dir, "models", f"{model_name}_scaler.pkl")
        metadata_path = os.path.join(self.data_dir, "models", f"{model_name}_metadata.json")
        
        # 모델과 스케일러 로드
        with open(model_path, 'rb') as f:
            self.classifier = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        # 메타데이터 로드
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            self.feature_names = metadata['feature_names']
        
        self.is_trained = True
        return metadata
    
    def analyze_video(self, video_path: str, progress_callback=None) -> Dict:
        """비디오 전체 분석 (1초에 1프레임)"""
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        results = {
            'video_path': video_path,
            'fps': fps,
            'total_frames': total_frames,
            'analyzed_frames': 0,
            'ui_segments': [],
            'frame_results': []
        }
        
        frame_count = 0
        current_ui_start = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 1초에 1프레임만 분석
            if frame_count % fps == 0:
                timestamp = frame_count / fps
                
                # 프레임 분석
                analysis = self.analyze_frame(frame, timestamp)
                results['frame_results'].append(analysis)
                results['analyzed_frames'] += 1
                
                # UI 세그먼트 추적
                if analysis['is_ui'] and current_ui_start is None:
                    current_ui_start = timestamp
                elif not analysis['is_ui'] and current_ui_start is not None:
                    results['ui_segments'].append({
                        'start': current_ui_start,
                        'end': timestamp,
                        'duration': timestamp - current_ui_start
                    })
                    current_ui_start = None
                
                # 진행률 콜백
                if progress_callback:
                    progress = frame_count / total_frames
                    progress_callback(progress, timestamp)
            
            frame_count += 1
        
        # 마지막 UI 세그먼트 처리
        if current_ui_start is not None:
            results['ui_segments'].append({
                'start': current_ui_start,
                'end': frame_count / fps,
                'duration': (frame_count / fps) - current_ui_start
            })
        
        cap.release()
        return results