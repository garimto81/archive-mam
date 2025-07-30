#!/usr/bin/env python
"""
스트리밍 비디오 처리 핸들러
다운로드 없이 직접 URL에서 비디오를 스트리밍하여 처리
"""
import cv2
import yt_dlp
import requests
import logging
from urllib.parse import urlparse
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class StreamingVideoHandler:
    """스트리밍 비디오 처리 클래스"""
    
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best[height<=720]',  # 720p 이하로 제한
            'noplaylist': True,
        }
    
    def get_stream_url(self, input_url: str) -> Dict[str, Any]:
        """
        입력 URL에서 스트리밍 가능한 직접 URL 추출
        
        Args:
            input_url: YouTube URL 또는 직접 비디오 URL
            
        Returns:
            Dict containing stream_url, title, duration, etc.
        """
        try:
            if self.is_youtube_url(input_url):
                return self._get_youtube_stream_url(input_url)
            else:
                return self._get_direct_stream_url(input_url)
                
        except Exception as e:
            logger.error(f"스트림 URL 추출 실패: {e}")
            raise
    
    def is_youtube_url(self, url: str) -> bool:
        """YouTube URL인지 확인"""
        youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in youtube_domains)
    
    def _get_youtube_stream_url(self, youtube_url: str) -> Dict[str, Any]:
        """YouTube URL에서 스트리밍 URL 추출"""
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(youtube_url, download=False)
                
                # 스트리밍 URL 찾기
                stream_url = None
                formats = info.get('formats', [])
                
                # 비디오+오디오 통합 포맷 우선 선택
                for fmt in reversed(formats):
                    if (fmt.get('vcodec') != 'none' and 
                        fmt.get('acodec') != 'none' and
                        fmt.get('height', 0) <= 720):
                        stream_url = fmt.get('url')
                        break
                
                # 통합 포맷이 없으면 비디오만 선택
                if not stream_url:
                    for fmt in reversed(formats):
                        if (fmt.get('vcodec') != 'none' and
                            fmt.get('height', 0) <= 720):
                            stream_url = fmt.get('url')
                            break
                
                if not stream_url:
                    raise Exception("스트리밍 가능한 포맷을 찾을 수 없습니다")
                
                return {
                    'stream_url': stream_url,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'width': info.get('width', 1280),
                    'height': info.get('height', 720),
                    'fps': info.get('fps', 30),
                    'source_type': 'youtube'
                }
                
            except Exception as e:
                logger.error(f"YouTube 정보 추출 실패: {e}")
                raise Exception(f"YouTube 비디오 정보를 가져올 수 없습니다: {str(e)}")
    
    def _get_direct_stream_url(self, direct_url: str) -> Dict[str, Any]:
        """직접 비디오 URL 처리"""
        try:
            # HEAD 요청으로 파일 정보 확인
            response = requests.head(direct_url, timeout=10)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            content_length = response.headers.get('content-length', 0)
            
            if not content_type.startswith('video/'):
                raise Exception("비디오 파일이 아닙니다")
            
            return {
                'stream_url': direct_url,
                'title': direct_url.split('/')[-1],
                'duration': 0,  # 직접 URL에서는 미리 알 수 없음
                'content_length': int(content_length) if content_length else 0,
                'content_type': content_type,
                'source_type': 'direct'
            }
            
        except Exception as e:
            logger.error(f"직접 URL 처리 실패: {e}")
            raise Exception(f"비디오 URL에 접근할 수 없습니다: {str(e)}")
    
    def create_video_capture(self, stream_info: Dict[str, Any]) -> cv2.VideoCapture:
        """
        스트림 정보를 이용해 VideoCapture 객체 생성
        
        Args:
            stream_info: get_stream_url에서 반환된 정보
            
        Returns:
            OpenCV VideoCapture 객체
        """
        stream_url = stream_info['stream_url']
        
        try:
            # OpenCV VideoCapture로 스트림 열기
            cap = cv2.VideoCapture(stream_url)
            
            if not cap.isOpened():
                # 재시도 (네트워크 지연 등을 고려)
                time.sleep(2)
                cap = cv2.VideoCapture(stream_url)
                
                if not cap.isOpened():
                    raise Exception("비디오 스트림을 열 수 없습니다")
            
            # 기본 설정
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화
            
            logger.info(f"스트림 연결 성공: {stream_info.get('title', 'Unknown')}")
            return cap
            
        except Exception as e:
            logger.error(f"VideoCapture 생성 실패: {e}")
            raise Exception(f"비디오 스트림을 열 수 없습니다: {str(e)}")
    
    def validate_stream(self, cap: cv2.VideoCapture) -> Dict[str, Any]:
        """
        스트림 유효성 검사 및 메타데이터 추출
        
        Args:
            cap: VideoCapture 객체
            
        Returns:
            스트림 메타데이터
        """
        try:
            # 첫 번째 프레임 읽기 테스트
            ret, frame = cap.read()
            if not ret or frame is None:
                raise Exception("첫 번째 프레임을 읽을 수 없습니다")
            
            # 메타데이터 추출
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 처음으로 되돌리기
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            metadata = {
                'fps': fps if fps > 0 else 30,  # 기본값 30
                'width': width,
                'height': height,
                'frame_count': frame_count if frame_count > 0 else None,
                'duration': frame_count / fps if frame_count > 0 and fps > 0 else None,
                'first_frame_shape': frame.shape
            }
            
            logger.info(f"스트림 검증 완료: {width}x{height}, {fps:.1f}FPS")
            return metadata
            
        except Exception as e:
            logger.error(f"스트림 검증 실패: {e}")
            raise Exception(f"비디오 스트림이 유효하지 않습니다: {str(e)}")

class StreamingProgressTracker:
    """스트리밍 진행률 추적기"""
    
    def __init__(self, total_frames: Optional[int] = None):
        self.total_frames = total_frames
        self.current_frame = 0
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, frame_number: int) -> Dict[str, Any]:
        """
        진행률 업데이트
        
        Args:
            frame_number: 현재 프레임 번호
            
        Returns:
            진행률 정보
        """
        self.current_frame = frame_number
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # 진행률 계산
        if self.total_frames and self.total_frames > 0:
            progress_percent = (frame_number / self.total_frames) * 100
        else:
            progress_percent = 0  # 총 프레임 수를 모르는 경우
        
        # 처리 속도 계산
        fps_processing = frame_number / elapsed_time if elapsed_time > 0 else 0
        
        # 예상 완료 시간
        eta = None
        if self.total_frames and fps_processing > 0:
            remaining_frames = self.total_frames - frame_number
            eta_seconds = remaining_frames / fps_processing
            eta = eta_seconds
        
        progress_info = {
            'current_frame': frame_number,
            'total_frames': self.total_frames,
            'progress_percent': progress_percent,
            'elapsed_time': elapsed_time,
            'processing_fps': fps_processing,
            'eta_seconds': eta
        }
        
        self.last_update = current_time
        return progress_info

def test_streaming_handler():
    """스트리밍 핸들러 테스트"""
    handler = StreamingVideoHandler()
    
    # 테스트 URL (실제 사용 시에는 유효한 URL로 변경)
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # 테스트용
        "https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4"  # 직접 URL
    ]
    
    for url in test_urls:
        try:
            print(f"\n테스트 URL: {url}")
            
            # 스트림 정보 추출
            stream_info = handler.get_stream_url(url)
            print(f"스트림 정보: {stream_info}")
            
            # VideoCapture 생성
            cap = handler.create_video_capture(stream_info)
            
            # 스트림 검증
            metadata = handler.validate_stream(cap)
            print(f"메타데이터: {metadata}")
            
            # 몇 프레임 읽기 테스트
            for i in range(5):
                ret, frame = cap.read()
                if ret:
                    print(f"프레임 {i+1}: {frame.shape}")
                else:
                    print(f"프레임 {i+1}: 읽기 실패")
                    break
            
            cap.release()
            print("✅ 테스트 성공")
            
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    test_streaming_handler()