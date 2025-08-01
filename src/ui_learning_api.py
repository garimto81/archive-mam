"""
UI Learning API - Flask 백엔드 통합
"""

from flask import Blueprint, request, jsonify, send_file
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from .advanced_ui_detector import AdvancedUIDetector
import base64
from io import BytesIO
from PIL import Image

# Blueprint 생성
ui_learning_bp = Blueprint('ui_learning', __name__)

# 전역 감지기 인스턴스
detector = AdvancedUIDetector()

# 설정
UPLOAD_FOLDER = 'ui_learning_uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ui_learning_bp.route('/api/ui-learning/analyze-frame', methods=['POST'])
def analyze_frame():
    """단일 프레임 분석"""
    try:
        data = request.json
        
        # Base64 이미지 디코딩
        image_data = data.get('frame')
        if not image_data:
            return jsonify({'error': 'No frame data provided'}), 400
        
        # Base64 to OpenCV image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(BytesIO(image_bytes))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 특징 추출
        features = detector.extract_features(frame)
        
        # 분석 결과
        timestamp = data.get('timestamp', 0)
        result = detector.analyze_frame(frame, timestamp)
        
        return jsonify({
            'success': True,
            'features': features,
            'ui_probability': result['ui_probability'],
            'is_ui': result['is_ui'],
            'confidence': result['confidence']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/save-sample', methods=['POST'])
def save_sample():
    """학습 샘플 저장"""
    try:
        data = request.json
        
        # 프레임 데이터
        frame_data = data.get('frame')
        features = data.get('features')
        is_ui = data.get('is_ui')
        timestamp = data.get('timestamp')
        video_name = data.get('video_name', 'unknown')
        
        if not all([frame_data, features is not None, is_ui is not None]):
            return jsonify({'error': 'Missing required data'}), 400
        
        # Base64 to OpenCV image
        image_bytes = base64.b64decode(frame_data.split(',')[1])
        image = Image.open(BytesIO(image_bytes))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 샘플 저장
        detector.save_training_sample(frame, features, is_ui, timestamp, video_name)
        
        return jsonify({
            'success': True,
            'total_samples': len(detector.training_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/train', methods=['POST'])
def train_model():
    """모델 학습"""
    try:
        data = request.json
        min_samples = data.get('min_samples', 50)
        
        # 저장된 데이터 로드
        loaded = detector.load_training_data()
        
        if len(detector.training_data) < min_samples:
            return jsonify({
                'error': f'Not enough samples. Need {min_samples}, have {len(detector.training_data)}'
            }), 400
        
        # 모델 학습
        train_result = detector.train_model(min_samples)
        
        return jsonify({
            'success': True,
            'result': train_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/save-model', methods=['POST'])
def save_model():
    """학습된 모델 저장"""
    try:
        data = request.json
        model_name = data.get('model_name', 'ui_detector_model')
        
        if not detector.is_trained:
            return jsonify({'error': 'Model not trained yet'}), 400
        
        detector.save_model(model_name)
        
        return jsonify({
            'success': True,
            'model_name': model_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/load-model', methods=['POST'])
def load_model():
    """저장된 모델 로드"""
    try:
        data = request.json
        model_name = data.get('model_name', 'ui_detector_model')
        
        metadata = detector.load_model(model_name)
        
        return jsonify({
            'success': True,
            'metadata': metadata
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/analyze-video', methods=['POST'])
def analyze_video():
    """전체 비디오 분석 (1초 1프레임)"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # 비디오 분석
            def progress_callback(progress, timestamp):
                # 실시간 진행률은 WebSocket이나 SSE로 구현 가능
                print(f"Progress: {progress:.1%} at {timestamp:.1f}s")
            
            results = detector.analyze_video(filepath, progress_callback)
            
            # 파일 정리
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'results': results
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/stats', methods=['GET'])
def get_stats():
    """현재 학습 데이터 통계"""
    try:
        # 저장된 데이터 로드
        detector.load_training_data()
        
        total = len(detector.training_data)
        ui_count = sum(1 for s in detector.training_data if s['is_ui'])
        game_count = total - ui_count
        
        return jsonify({
            'total_samples': total,
            'ui_samples': ui_count,
            'game_samples': game_count,
            'is_trained': detector.is_trained,
            'model_accuracy': None  # 교차 검증으로 계산 가능
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/export-dataset', methods=['GET'])
def export_dataset():
    """학습 데이터셋 내보내기"""
    try:
        # 데이터 준비
        export_data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'samples': detector.training_data,
            'total_samples': len(detector.training_data)
        }
        
        # JSON 파일로 저장
        export_path = os.path.join(detector.data_dir, f'dataset_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return send_file(export_path, as_attachment=True, download_name='ui_dataset.json')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ui_learning_bp.route('/api/ui-learning/import-dataset', methods=['POST'])
def import_dataset():
    """학습 데이터셋 가져오기"""
    try:
        if 'dataset' not in request.files:
            return jsonify({'error': 'No dataset file provided'}), 400
        
        file = request.files['dataset']
        if file.filename.endswith('.json'):
            # JSON 데이터 읽기
            data = json.load(file)
            
            # 기존 데이터에 추가
            imported_count = 0
            for sample in data.get('samples', []):
                detector.training_data.append(sample)
                imported_count += 1
            
            return jsonify({
                'success': True,
                'imported_samples': imported_count,
                'total_samples': len(detector.training_data)
            })
        
        return jsonify({'error': 'Invalid file format'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 핸드 감지 통합 API
@ui_learning_bp.route('/api/ui-learning/detect-hands', methods=['POST'])
def detect_hands():
    """학습된 모델로 핸드 감지"""
    try:
        data = request.json
        video_path = data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'error': 'Invalid video path'}), 400
        
        if not detector.is_trained:
            return jsonify({'error': 'Model not trained. Please train or load a model first.'}), 400
        
        # 비디오 분석
        results = detector.analyze_video(video_path)
        
        # UI 세그먼트를 핸드로 변환
        hands = []
        for i, ui_segment in enumerate(results['ui_segments']):
            # UI 시작 15초 전이 이전 핸드 종료
            hand_end = ui_segment['start'] - 15
            
            # UI 종료 15초 후가 다음 핸드 시작
            if i < len(results['ui_segments']) - 1:
                next_hand_start = ui_segment['end'] + 15
                next_ui_start = results['ui_segments'][i + 1]['start']
                next_hand_end = next_ui_start - 15
                
                if next_hand_start < next_hand_end:  # 유효한 핸드
                    hands.append({
                        'hand_id': len(hands) + 1,
                        'start_time': next_hand_start,
                        'end_time': next_hand_end,
                        'duration': next_hand_end - next_hand_start,
                        'confidence': 0.9
                    })
        
        return jsonify({
            'success': True,
            'video_path': video_path,
            'total_hands': len(hands),
            'hands': hands,
            'ui_segments': results['ui_segments']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500