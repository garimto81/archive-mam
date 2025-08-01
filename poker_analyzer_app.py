#!/usr/bin/env python
"""
포커 대회 영상 분석 웹 애플리케이션
YouTube 링크나 비디오 URL을 입력받아 핸드 길이를 분석하는 Flask 앱
"""
import os
import sys
import json
import uuid
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import logging

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import cv2

# 프로젝트 모듈 import
try:
    from src.hand_boundary_detector import HandBoundaryDetector
    from src.fast_hand_detector import FastHandDetector
    from src.streaming_video_handler import StreamingVideoHandler
    from src.local_file_browser import LocalFileBrowser
except ImportError:
    sys.path.append('.')
    from src.hand_boundary_detector import HandBoundaryDetector
    from src.fast_hand_detector import FastHandDetector
    from src.streaming_video_handler import StreamingVideoHandler
    from src.local_file_browser import LocalFileBrowser

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'poker_analyzer_secret_key_2024'

# UI 학습 API 추가
try:
    from src.ui_learning_api import ui_learning_bp
    app.register_blueprint(ui_learning_bp)
    logger.info("UI Learning API loaded successfully")
except ImportError:
    logger.warning("UI Learning API not available - install scikit-learn")

# 설정
UPLOAD_FOLDER = 'temp_videos'
RESULTS_FOLDER = 'analysis_results'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'webm'}

# 디렉토리 생성
for folder in [UPLOAD_FOLDER, RESULTS_FOLDER, 'static/results']:
    Path(folder).mkdir(parents=True, exist_ok=True)

# 진행 상황 추적용 전역 변수
analysis_progress = {}

# 파일 브라우저 인스턴스
file_browser = LocalFileBrowser()

class HandLengthClassifier:
    """핸드 길이 분류 시스템"""
    
    def __init__(self):
        self.categories = {
            'very_short': {'min': 0, 'max': 45, 'name': '매우 짧은 핸드', 'color': '#ff4444'},
            'short': {'min': 45, 'max': 90, 'name': '짧은 핸드', 'color': '#ff8800'},
            'medium': {'min': 90, 'max': 180, 'name': '보통 핸드', 'color': '#ffcc00'},
            'long': {'min': 180, 'max': 300, 'name': '긴 핸드', 'color': '#88cc00'},
            'very_long': {'min': 300, 'max': float('inf'), 'name': '매우 긴 핸드', 'color': '#0088cc'}
        }
    
    def classify_hands(self, hands_data):
        """핸드들을 길이별로 분류"""
        classified = {category: [] for category in self.categories}
        statistics = {category: 0 for category in self.categories}
        
        for hand in hands_data:
            duration = hand['duration']
            
            for category, criteria in self.categories.items():
                if criteria['min'] <= duration < criteria['max']:
                    classified[category].append(hand)
                    statistics[category] += 1
                    break
        
        return classified, statistics
    
    def generate_summary(self, hands_data, statistics):
        """분석 결과 요약 생성"""
        if not hands_data:
            return {
                'total_hands': 0,
                'total_duration': 0,
                'average_duration': 0,
                'longest_hand': None,
                'shortest_hand': None
            }
        
        total_hands = len(hands_data)
        total_duration = sum(hand['duration'] for hand in hands_data)
        average_duration = total_duration / total_hands
        
        longest_hand = max(hands_data, key=lambda x: x['duration'])
        shortest_hand = min(hands_data, key=lambda x: x['duration'])
        
        return {
            'total_hands': total_hands,
            'total_duration': round(total_duration, 1),
            'average_duration': round(average_duration, 1),
            'longest_hand': {
                'id': longest_hand['hand_id'],
                'duration': round(longest_hand['duration'], 1),
                'start_time': round(longest_hand['start_time'], 1)
            },
            'shortest_hand': {
                'id': shortest_hand['hand_id'],
                'duration': round(shortest_hand['duration'], 1),
                'start_time': round(shortest_hand['start_time'], 1)
            },
            'distribution': statistics
        }

class StreamingAnalyzer:
    """스트리밍 기반 비디오 분석 시스템"""
    
    def __init__(self):
        self.streaming_handler = StreamingVideoHandler()
    
    def prepare_stream(self, url, task_id):
        """스트림 준비 및 정보 추출"""
        try:
            analysis_progress[task_id]['status'] = 'preparing'
            analysis_progress[task_id]['message'] = '스트림 정보 추출 중...'
            
            # 스트림 URL 및 정보 추출
            stream_info = self.streaming_handler.get_stream_url(url)
            
            analysis_progress[task_id]['video_info'] = {
                'title': stream_info.get('title', 'Unknown'),
                'duration': stream_info.get('duration', 0),
                'width': stream_info.get('width', 1280),
                'height': stream_info.get('height', 720),
                'source_type': stream_info.get('source_type', 'unknown'),
                'url': url
            }
            
            # VideoCapture 객체 생성
            cap = self.streaming_handler.create_video_capture(stream_info)
            
            # 스트림 검증
            metadata = self.streaming_handler.validate_stream(cap)
            
            # 메타데이터 업데이트
            analysis_progress[task_id]['video_info'].update(metadata)
            
            return cap, stream_info
                
        except Exception as e:
            analysis_progress[task_id]['status'] = 'error'
            analysis_progress[task_id]['message'] = f'스트림 준비 실패: {str(e)}'
            raise

def allowed_file(filename):
    """허용된 파일 확장자인지 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_stream_task(url, task_id, use_fast_mode=False):
    """스트리밍 비디오 분석 작업 (백그라운드 실행)"""
    cap = None
    try:
        # 스트림 준비
        analyzer = StreamingAnalyzer()
        cap, stream_info = analyzer.prepare_stream(url, task_id)
        
        analysis_progress[task_id]['status'] = 'analyzing'
        analysis_progress[task_id]['message'] = '핸드 경계 감지 시작...'
        analysis_progress[task_id]['progress'] = 5
        
        # 진행률 업데이트 콜백 함수
        def progress_callback(progress_info):
            current_progress = analysis_progress[task_id]['progress']
            
            # 분석 진행률은 5%~80% 범위에서 업데이트
            if progress_info.get('progress_percent', 0) > 0:
                new_progress = 5 + (progress_info['progress_percent'] * 0.75)  # 5% + (0~100% * 75%)
            else:
                # 스트리밍의 경우 시간 기반으로 추정
                elapsed_time = progress_info.get('current_time', 0)
                if elapsed_time > 0:
                    # 10분 영상 기준으로 진행률 추정 (임의 기준)
                    estimated_progress = min((elapsed_time / 600) * 75, 75)
                    new_progress = 5 + estimated_progress
                else:
                    new_progress = current_progress + 1  # 점진적 증가
            
            analysis_progress[task_id]['progress'] = min(new_progress, 80)
            analysis_progress[task_id]['message'] = f'분석 중... ({progress_info.get("detected_hands", 0)}개 핸드 감지됨)'
            
            # 소스 정보 업데이트
            if 'source_info' in progress_info:
                analysis_progress[task_id]['video_info'].update(progress_info['source_info'])
        
        # 핸드 감지 수행 (스트리밍 방식)
        if use_fast_mode:
            detector = FastHandDetector(sampling_rate=60, num_workers=4)
            analysis_progress[task_id]['message'] = '고속 분석 모드로 실행 중...'
        else:
            detector = HandBoundaryDetector()
        
        # 스트림 정보를 source_info로 전달
        source_info = {
            'type': 'stream',
            'title': stream_info.get('title', 'Unknown'),
            'url': url,
            'source_type': stream_info.get('source_type', 'unknown')
        }
        
        result_file = detector.analyze_stream(
            cap, 
            source_info, 
            progress_callback=progress_callback
        )
        
        analysis_progress[task_id]['progress'] = 85
        analysis_progress[task_id]['message'] = '결과 분석 중...'
        
        # 결과 로드
        with open(result_file, 'r', encoding='utf-8') as f:
            hands_data = json.load(f)
        
        # 핸드 길이 분류
        classifier = HandLengthClassifier()
        classified_hands, statistics = classifier.classify_hands(hands_data)
        summary = classifier.generate_summary(hands_data, statistics)
        
        # 최종 결과 저장
        final_result = {
            'stream_url': url,
            'stream_info': stream_info,
            'analysis_time': datetime.now().isoformat(),
            'hands_data': hands_data,
            'classified_hands': classified_hands,
            'statistics': statistics,
            'summary': summary,
            'categories': classifier.categories
        }
        
        result_path = f"{RESULTS_FOLDER}/stream_analysis_{task_id}.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
        
        analysis_progress[task_id]['status'] = 'completed'
        analysis_progress[task_id]['message'] = '분석 완료!'
        analysis_progress[task_id]['progress'] = 100
        analysis_progress[task_id]['result_file'] = result_path
        
        logger.info(f"스트림 분석 완료: {len(hands_data)}개 핸드 감지")
        
    except Exception as e:
        analysis_progress[task_id]['status'] = 'error'
        analysis_progress[task_id]['message'] = f'분석 실패: {str(e)}'
        logger.error(f"스트림 분석 오류: {e}")
    finally:
        # VideoCapture 리소스 정리
        if cap is not None:
            cap.release()

def analyze_file_task(video_path, task_id, use_fast_mode=False):
    """로컬 파일 분석 작업 (기존 방식 유지)"""
    try:
        analysis_progress[task_id]['status'] = 'analyzing'
        analysis_progress[task_id]['message'] = '핸드 경계 감지 중...'
        analysis_progress[task_id]['progress'] = 0
        
        # 진행률 콜백
        def progress_callback(progress_info):
            if progress_info.get('progress_percent', 0) > 0:
                analysis_progress[task_id]['progress'] = progress_info['progress_percent'] * 0.8  # 80%까지
            analysis_progress[task_id]['message'] = f'분석 중... ({progress_info.get("detected_hands", 0)}개 핸드 감지됨)'
        
        # 핸드 감지 수행
        if use_fast_mode:
            detector = FastHandDetector(sampling_rate=60, num_workers=4)
            analysis_progress[task_id]['message'] = '고속 분석 모드로 실행 중...'
        else:
            detector = HandBoundaryDetector()
        result_file = detector.analyze_video(video_path, progress_callback=progress_callback)
        
        analysis_progress[task_id]['progress'] = 85
        analysis_progress[task_id]['message'] = '결과 분석 중...'
        
        # 결과 로드 및 분류
        with open(result_file, 'r', encoding='utf-8') as f:
            hands_data = json.load(f)
        
        classifier = HandLengthClassifier()
        classified_hands, statistics = classifier.classify_hands(hands_data)
        summary = classifier.generate_summary(hands_data, statistics)
        
        # 최종 결과 저장
        final_result = {
            'video_path': video_path,
            'analysis_time': datetime.now().isoformat(),
            'hands_data': hands_data,
            'classified_hands': classified_hands,
            'statistics': statistics,
            'summary': summary,
            'categories': classifier.categories
        }
        
        result_path = f"{RESULTS_FOLDER}/file_analysis_{task_id}.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
        
        analysis_progress[task_id]['status'] = 'completed'
        analysis_progress[task_id]['message'] = '분석 완료!'
        analysis_progress[task_id]['progress'] = 100
        analysis_progress[task_id]['result_file'] = result_path
        
        # 임시 파일 정리
        if video_path.startswith(UPLOAD_FOLDER):
            try:
                os.remove(video_path)
            except:
                pass
        
        logger.info(f"파일 분석 완료: {len(hands_data)}개 핸드 감지")
        
    except Exception as e:
        analysis_progress[task_id]['status'] = 'error'
        analysis_progress[task_id]['message'] = f'분석 실패: {str(e)}'
        logger.error(f"파일 분석 오류: {e}")

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/advanced_ui_learning.html')
def advanced_ui_learning():
    """고급 UI 학습 페이지"""
    return send_file('advanced_ui_learning.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """분석 시작"""
    try:
        task_id = str(uuid.uuid4())
        
        # 진행 상황 초기화
        analysis_progress[task_id] = {
            'status': 'starting',
            'message': '분석 준비 중...',
            'progress': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # 분석 모드 확인 (고속 모드 여부)
        use_fast_mode = request.form.get('fast_mode', 'false').lower() == 'true'
        
        # URL 입력인지 파일 업로드인지 확인
        if 'video_url' in request.form and request.form['video_url'].strip():
            # URL 스트리밍 분석
            url = request.form['video_url'].strip()
            
            # URL 유효성 검사
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return jsonify({'error': '유효한 URL을 입력하세요'}), 400
            
            # 백그라운드에서 스트리밍 분석 시작
            thread = threading.Thread(target=analyze_stream_task, args=(url, task_id, use_fast_mode))
            thread.daemon = True
            thread.start()
                
        elif 'video_file' in request.files:
            # 파일 업로드 분석
            file = request.files['video_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                video_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
                file.save(video_path)
                
                # 백그라운드에서 파일 분석 시작
                thread = threading.Thread(target=analyze_file_task, args=(video_path, task_id, use_fast_mode))
                thread.daemon = True
                thread.start()
            else:
                return jsonify({'error': '올바른 비디오 파일을 선택하세요'}), 400
        else:
            return jsonify({'error': 'URL 또는 파일을 입력하세요'}), 400
        
        return jsonify({'task_id': task_id})
        
    except Exception as e:
        logger.error(f"분석 시작 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """분석 진행 상황 조회"""
    if task_id not in analysis_progress:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    return jsonify(analysis_progress[task_id])

@app.route('/results/<task_id>')
def get_results(task_id):
    """분석 결과 조회"""
    if task_id not in analysis_progress:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    progress_info = analysis_progress[task_id]
    
    if progress_info['status'] != 'completed':
        return jsonify({'error': '분석이 아직 완료되지 않았습니다'}), 400
    
    try:
        with open(progress_info['result_file'], 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        return render_template('results.html', 
                             task_id=task_id, 
                             results=results)
    except Exception as e:
        return jsonify({'error': f'결과 로드 실패: {str(e)}'}), 500

@app.route('/api/results/<task_id>')
def api_get_results(task_id):
    """API로 결과 조회"""
    if task_id not in analysis_progress:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    progress_info = analysis_progress[task_id]
    
    if progress_info['status'] != 'completed':
        return jsonify({'error': '분석이 아직 완료되지 않았습니다'}), 400
    
    try:
        with open(progress_info['result_file'], 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': f'결과 로드 실패: {str(e)}'}), 500

@app.route('/download/<task_id>')
def download_results(task_id):
    """결과 파일 다운로드"""
    if task_id not in analysis_progress:
        return jsonify({'error': '작업을 찾을 수 없습니다'}), 404
    
    progress_info = analysis_progress[task_id]
    
    if progress_info['status'] != 'completed':
        return jsonify({'error': '분석이 아직 완료되지 않았습니다'}), 400
    
    try:
        return send_file(progress_info['result_file'], 
                        as_attachment=True,
                        download_name=f'poker_analysis_{task_id}.json')
    except Exception as e:
        return jsonify({'error': f'다운로드 실패: {str(e)}'}), 500

# 파일 브라우저 API 엔드포인트들
@app.route('/api/file-browser/drives')
def get_drives():
    """사용 가능한 드라이브 목록 조회"""
    try:
        drives = file_browser.get_drives()
        return jsonify({'drives': drives})
    except Exception as e:
        logger.error(f"드라이브 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file-browser/list')
def list_directory():
    """디렉토리 내용 조회"""
    try:
        path = request.args.get('path', os.getcwd())
        show_hidden = request.args.get('show_hidden', 'false').lower() == 'true'
        
        dir_info = file_browser.list_directory(path, show_hidden)
        return jsonify(dir_info)
        
    except Exception as e:
        logger.error(f"디렉토리 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file-browser/file-info')
def get_file_info():
    """파일 정보 조회"""
    try:
        file_path = request.args.get('path')
        if not file_path:
            return jsonify({'error': '파일 경로가 필요합니다'}), 400
        
        file_info = file_browser.get_file_info(file_path)
        return jsonify(file_info)
        
    except Exception as e:
        logger.error(f"파일 정보 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file-browser/validate')
def validate_video_file():
    """비디오 파일 유효성 검사"""
    try:
        file_path = request.args.get('path')
        if not file_path:
            return jsonify({'error': '파일 경로가 필요합니다'}), 400
        
        validation_result = file_browser.validate_video_file(file_path)
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"파일 검증 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file-browser/network-paths')
def get_network_paths():
    """네트워크 경로 조회"""
    try:
        network_paths = file_browser.get_network_paths()
        return jsonify({'network_paths': network_paths})
    except Exception as e:
        logger.error(f"네트워크 경로 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-local-file', methods=['POST'])
def analyze_local_file():
    """로컬 파일 경로로 분석 시작"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'error': '파일 경로가 필요합니다'}), 400
        
        # 파일 유효성 검사
        validation = file_browser.validate_video_file(file_path)
        if not validation['valid']:
            return jsonify({'error': f"파일이 유효하지 않습니다: {', '.join(validation['errors'])}"}), 400
        
        task_id = str(uuid.uuid4())
        
        # 진행 상황 초기화
        analysis_progress[task_id] = {
            'status': 'starting',
            'message': '로컬 파일 분석 준비 중...',
            'progress': 0,
            'start_time': datetime.now().isoformat(),
            'file_info': validation['file_info']
        }
        
        # 백그라운드에서 파일 분석 시작
        thread = threading.Thread(target=analyze_file_task, args=(file_path, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'file_info': validation['file_info']
        })
        
    except Exception as e:
        logger.error(f"로컬 파일 분석 시작 오류: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🃏 포커 대회 영상 분석기 시작")
    print("🌐 웹 브라우저에서 http://localhost:5000 접속")
    print("📹 YouTube 링크나 비디오 파일을 업로드하여 분석하세요")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)