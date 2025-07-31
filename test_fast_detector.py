#!/usr/bin/env python
"""
고속 핸드 감지기 테스트 스크립트
다양한 설정으로 성능을 비교 테스트
"""
import time
import sys
import os
from pathlib import Path

# 프로젝트 모듈 import
sys.path.append('.')
from src.fast_hand_detector import FastHandDetector
from src.hand_boundary_detector import HandBoundaryDetector

def test_performance_comparison(video_path):
    """성능 비교 테스트"""
    print(f"=== 성능 비교 테스트 ===")
    print(f"테스트 비디오: {video_path}")
    print()
    
    # 1. 기존 감지기 테스트 (샘플 비디오만)
    if "sample" in video_path.lower():
        print("1. 기존 감지기 (HandBoundaryDetector)")
        print("   - 모든 프레임 분석")
        print("   - 복잡한 CV 알고리즘 사용")
        
        start_time = time.time()
        detector = HandBoundaryDetector()
        
        try:
            result = detector.analyze_video(video_path)
            elapsed = time.time() - start_time
            
            with open(result, 'r') as f:
                import json
                hands = json.load(f)
            
            print(f"   ✓ 소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
            print(f"   ✓ 감지된 핸드: {len(hands)}개")
            print()
        except Exception as e:
            print(f"   ✗ 오류: {e}")
            print()
    
    # 2. 고속 감지기 테스트 (다양한 샘플링 비율)
    sampling_rates = [15, 30, 60, 90]
    
    for rate in sampling_rates:
        print(f"2. 고속 감지기 (샘플링 비율: {rate}:1)")
        print(f"   - {rate}프레임마다 1개 분석")
        print(f"   - 병렬 처리 (4 워커)")
        
        start_time = time.time()
        detector = FastHandDetector(sampling_rate=rate, num_workers=4)
        
        def progress_callback(info):
            stage = info.get('stage', 'unknown')
            progress = info.get('progress', 0)
            print(f"\r   [{stage}] {progress:.1f}%", end='', flush=True)
        
        try:
            result = detector.analyze_video(video_path, progress_callback=progress_callback)
            elapsed = time.time() - start_time
            
            with open(result, 'r') as f:
                import json
                hands = json.load(f)
            
            print(f"\n   ✓ 소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
            print(f"   ✓ 감지된 핸드: {len(hands)}개")
            
            # 속도 향상 계산
            if "sample" in video_path.lower() and 'elapsed' in locals():
                speedup = elapsed / elapsed if elapsed > 0 else 0
                print(f"   ✓ 속도 향상: {speedup:.1f}x")
            
            print()
        except Exception as e:
            print(f"\n   ✗ 오류: {e}")
            print()

def test_accuracy_analysis(video_path):
    """정확도 분석 테스트"""
    print(f"\n=== 정확도 분석 ===")
    
    # 60프레임 샘플링으로 테스트
    detector = FastHandDetector(sampling_rate=60, num_workers=4)
    
    print("고속 감지기 상세 분석 (샘플링 60:1)")
    result = detector.analyze_video(video_path)
    
    with open(result, 'r') as f:
        import json
        hands = json.load(f)
    
    if hands:
        print(f"\n감지된 핸드 상세:")
        for i, hand in enumerate(hands[:5]):  # 처음 5개만 표시
            print(f"  핸드 {hand['hand_id']}:")
            print(f"    - 시작: {hand['start_time']:.1f}초")
            print(f"    - 종료: {hand['end_time']:.1f}초")
            print(f"    - 길이: {hand['duration']:.1f}초")
            print(f"    - 신뢰도: {hand.get('confidence', 0):.1f}%")
        
        if len(hands) > 5:
            print(f"  ... 외 {len(hands)-5}개 핸드")
    else:
        print("감지된 핸드가 없습니다.")

def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("포커 핸드 고속 감지기 테스트")
    print("=" * 60)
    print()
    
    # 테스트할 비디오 파일 찾기
    test_videos = []
    
    # 1. 명령줄 인자로 제공된 비디오
    if len(sys.argv) > 1:
        test_videos.append(sys.argv[1])
    
    # 2. 샘플 비디오 찾기
    sample_paths = [
        "videos/sample_poker_video.mp4",
        "temp_videos/*.mp4"
    ]
    
    for path in sample_paths:
        if "*" in path:
            from glob import glob
            files = glob(path)
            test_videos.extend(files[:2])  # 최대 2개만
        elif os.path.exists(path):
            test_videos.append(path)
    
    if not test_videos:
        print("테스트할 비디오 파일이 없습니다.")
        print("사용법: python test_fast_detector.py [비디오파일경로]")
        return
    
    # 각 비디오에 대해 테스트 실행
    for video_path in test_videos:
        if os.path.exists(video_path):
            print(f"\n{'='*60}")
            print(f"테스트 비디오: {os.path.basename(video_path)}")
            print(f"{'='*60}\n")
            
            # 성능 비교 테스트
            test_performance_comparison(video_path)
            
            # 정확도 분석
            test_accuracy_analysis(video_path)
            
            print("\n" + "="*60)

if __name__ == "__main__":
    main()