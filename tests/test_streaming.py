#!/usr/bin/env python
"""
스트리밍 기능 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.append(str(Path(__file__).parent))

from src.streaming_video_handler import StreamingVideoHandler
from src.hand_boundary_detector import HandBoundaryDetector

def test_streaming_analysis():
    """스트리밍 분석 테스트"""
    
    # 테스트 URL들
    test_urls = [
        # 샘플 비디오 URL (실제 테스트용)
        "https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4",
        
        # YouTube URL 예시 (실제 URL로 변경하여 테스트)
        # "https://www.youtube.com/watch?v=VIDEO_ID"
    ]
    
    print("스트리밍 분석 시스템 테스트")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n테스트 {i}: {url}")
        
        try:
            # 1. 스트리밍 핸들러 테스트
            print("1. 스트림 정보 추출 중...")
            handler = StreamingVideoHandler()
            stream_info = handler.get_stream_url(url)
            
            print(f"   제목: {stream_info.get('title', 'Unknown')}")
            print(f"   길이: {stream_info.get('duration', 0)}초")
            print(f"   해상도: {stream_info.get('width', 0)}x{stream_info.get('height', 0)}")
            
            # 2. VideoCapture 생성 테스트
            print("2. 비디오 스트림 연결 중...")
            cap = handler.create_video_capture(stream_info)
            
            # 3. 스트림 검증
            print("3. 스트림 검증 중...")
            metadata = handler.validate_stream(cap)
            print(f"   FPS: {metadata.get('fps', 0)}")
            print(f"   실제 해상도: {metadata.get('width', 0)}x{metadata.get('height', 0)}")
            
            # 4. 핸드 감지 테스트 (짧은 시간만)
            print("4. 핸드 감지 시스템 테스트 (10초간)...")
            
            def progress_callback(info):
                print(f"   진행: {info.get('current_time', 0):.1f}초, "
                      f"핸드: {info.get('detected_hands', 0)}개")
            
            detector = HandBoundaryDetector()
            
            # 짧은 테스트를 위해 10초만 처리
            frame_count = 0
            max_frames = int(metadata.get('fps', 30)) * 10  # 10초
            
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 모션 추적만 테스트
                motion_info = detector.motion_tracker.update(frame)
                frame_count += 1
                
                if frame_count % 30 == 0:  # 1초마다
                    current_time = frame_count / metadata.get('fps', 30)
                    print(f"   {current_time:.1f}초: 모션 영역 {len(motion_info['motion_regions'])}개")
            
            cap.release()
            print(f"   {frame_count} 프레임 처리 완료")
            
        except Exception as e:
            print(f"   테스트 실패: {e}")
            continue
    
    print(f"\n스트리밍 분석 테스트 완료!")

def test_url_extraction():
    """URL 추출 기능만 테스트 (빠른 테스트)"""
    
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    ]
    
    print("URL 추출 기능 테스트")
    print("=" * 30)
    
    handler = StreamingVideoHandler()
    
    for url in test_urls:
        print(f"\n테스트 URL: {url}")
        
        try:
            stream_info = handler.get_stream_url(url)
            print(f"   제목: {stream_info.get('title', 'Unknown')}")
            print(f"   소스: {stream_info.get('source_type', 'unknown')}")
            print(f"   스트림 URL 추출 성공")
            
        except Exception as e:
            print(f"   실패: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='스트리밍 기능 테스트')
    parser.add_argument('--mode', choices=['full', 'quick'], default='quick',
                       help='테스트 모드 (quick: URL 추출만, full: 전체)')
    
    args = parser.parse_args()
    
    if args.mode == 'quick':
        test_url_extraction()
    else:
        test_streaming_analysis()