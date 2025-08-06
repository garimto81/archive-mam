#!/usr/bin/env python
"""
핸드 감지 시스템 실행 스크립트
다양한 모드로 핸드 감지 시스템을 실행할 수 있습니다.
"""
import argparse
import sys
import os
from pathlib import Path
import json

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='포커 핸드 감지 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 분석
  python run_hand_detection.py analyze video.mp4
  
  # 시각화와 함께 분석
  python run_hand_detection.py analyze video.mp4 --visualize
  
  # 시각화만 (분석 결과 저장 안함)
  python run_hand_detection.py visualize video.mp4
  
  # 테스트 실행
  python run_hand_detection.py test
  
  # 성능 벤치마크
  python run_hand_detection.py benchmark video.mp4
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='실행할 명령')
    
    # 분석 명령
    analyze_parser = subparsers.add_parser('analyze', help='비디오 분석')
    analyze_parser.add_argument('video_path', help='분석할 비디오 파일')
    analyze_parser.add_argument('--output', '-o', help='결과 파일 경로')
    analyze_parser.add_argument('--visualize', '-v', action='store_true', help='시각화 활성화')
    analyze_parser.add_argument('--save-frames', action='store_true', help='디버그 프레임 저장')
    
    # 시각화 명령
    viz_parser = subparsers.add_parser('visualize', help='시각화만 실행')
    viz_parser.add_argument('video_path', help='분석할 비디오 파일')
    viz_parser.add_argument('--output', '-o', help='시각화 비디오 저장 경로')
    viz_parser.add_argument('--save-frames', action='store_true', help='디버그 프레임 저장')
    viz_parser.add_argument('--no-display', action='store_true', help='실시간 표시 비활성화')
    
    # 테스트 명령
    test_parser = subparsers.add_parser('test', help='테스트 실행')
    test_parser.add_argument('--comprehensive', '-c', action='store_true', help='종합 테스트')
    test_parser.add_argument('--performance', '-p', action='store_true', help='성능 테스트만')
    
    # 벤치마크 명령
    benchmark_parser = subparsers.add_parser('benchmark', help='성능 벤치마크')
    benchmark_parser.add_argument('video_path', help='벤치마크용 비디오 파일')
    benchmark_parser.add_argument('--iterations', '-i', type=int, default=3, help='반복 횟수')
    
    # 비교 명령
    compare_parser = subparsers.add_parser('compare', help='기존 시스템과 비교')
    compare_parser.add_argument('video_path', help='비교할 비디오 파일')
    compare_parser.add_argument('--baseline', help='기준 결과 파일 (JSON)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 명령별 실행
    if args.command == 'analyze':
        run_analysis(args)
    elif args.command == 'visualize':
        run_visualization(args)
    elif args.command == 'test':
        run_tests(args)
    elif args.command == 'benchmark':
        run_benchmark(args)
    elif args.command == 'compare':
        run_comparison(args)

def run_analysis(args):
    """분석 실행"""
    if not Path(args.video_path).exists():
        print(f"❌ 비디오 파일을 찾을 수 없습니다: {args.video_path}")
        return
    
    print(f"🎯 핸드 감지 분석 시작: {args.video_path}")
    
    try:
        from src.hand_boundary_detector import HandBoundaryDetector
        
        detector = HandBoundaryDetector()
        result_file = detector.analyze_video(args.video_path, args.output)
        
        # 결과 요약 출력
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"\n✅ 분석 완료!")
        print(f"📁 결과 파일: {result_file}")
        print(f"🎲 감지된 핸드: {len(results)}개")
        
        if results:
            total_duration = sum(hand['duration'] for hand in results)
            avg_duration = total_duration / len(results)
            avg_confidence = sum(hand['overall_confidence'] for hand in results) / len(results)
            
            print(f"⏱️  전체 게임 시간: {total_duration:.1f}초")
            print(f"📊 평균 핸드 길이: {avg_duration:.1f}초")
            print(f"📈 평균 신뢰도: {avg_confidence:.1f}")
            
            # 상위 5개 핸드 표시
            sorted_hands = sorted(results, key=lambda x: x['overall_confidence'], reverse=True)
            print(f"\n🔝 신뢰도 상위 핸드:")
            for i, hand in enumerate(sorted_hands[:5]):
                print(f"  {i+1}. 핸드 {hand['hand_id']}: {hand['overall_confidence']:.1f} "
                      f"({hand['start_time']:.1f}s-{hand['end_time']:.1f}s)")
        
        # 시각화 옵션
        if args.visualize:
            print(f"\n🎨 시각화 시작...")
            from src.hand_detection_visualizer import HandDetectionVisualizer
            
            visualizer = HandDetectionVisualizer()
            viz_output = result_file.replace('.json', '_visualization.mp4')
            visualizer.visualize_video(
                args.video_path, 
                output_path=viz_output,
                save_frames=args.save_frames
            )
            print(f"📹 시각화 비디오: {viz_output}")
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def run_visualization(args):
    """시각화 실행"""
    if not Path(args.video_path).exists():
        print(f"❌ 비디오 파일을 찾을 수 없습니다: {args.video_path}")
        return
    
    print(f"🎨 핸드 감지 시각화 시작: {args.video_path}")
    
    try:
        from src.hand_detection_visualizer import HandDetectionVisualizer
        
        visualizer = HandDetectionVisualizer(show_debug=not args.no_display)
        visualizer.visualize_video(
            video_path=args.video_path,
            output_path=args.output,
            save_frames=args.save_frames
        )
        
        print("✅ 시각화 완료")
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 시각화 중 오류 발생: {e}")

def run_tests(args):
    """테스트 실행"""
    print("🧪 핸드 감지 시스템 테스트 시작")
    
    try:
        if args.comprehensive:
            from test.test_hand_boundary_detection import run_comprehensive_test
            success = run_comprehensive_test()
        elif args.performance:
            from test.test_hand_boundary_detection import TestPerformanceMetrics
            test = TestPerformanceMetrics()
            test.test_processing_speed()
            test.test_memory_usage()
            success = True
        else:
            # 기본 테스트
            import pytest
            exit_code = pytest.main([
                "test/test_hand_boundary_detection.py", 
                "-v", "--tb=short"
            ])
            success = exit_code == 0
        
        if success:
            print("✅ 모든 테스트 통과!")
        else:
            print("❌ 일부 테스트 실패")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

def run_benchmark(args):
    """성능 벤치마크 실행"""
    if not Path(args.video_path).exists():
        print(f"❌ 비디오 파일을 찾을 수 없습니다: {args.video_path}")
        return
    
    print(f"⚡ 성능 벤치마크 시작: {args.video_path}")
    print(f"🔄 반복 횟수: {args.iterations}")
    
    try:
        from src.hand_boundary_detector import HandBoundaryDetector
        import time
        import cv2
        
        # 비디오 정보 확인
        cap = cv2.VideoCapture(args.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = frame_count / fps
        cap.release()
        
        print(f"📹 비디오 길이: {video_duration:.1f}초 ({frame_count} 프레임)")
        
        times = []
        results_count = []
        
        for i in range(args.iterations):
            print(f"\n🏃 실행 {i+1}/{args.iterations}")
            
            detector = HandBoundaryDetector()
            start_time = time.time()
            
            result_file = detector.analyze_video(args.video_path)
            
            end_time = time.time()
            processing_time = end_time - start_time
            times.append(processing_time)
            
            # 결과 개수 확인
            with open(result_file, 'r') as f:
                results = json.load(f)
            results_count.append(len(results))
            
            print(f"⏱️  처리 시간: {processing_time:.2f}초")
            print(f"🎲 감지된 핸드: {len(results)}개")
            print(f"🚀 처리 속도: {video_duration/processing_time:.2f}x 실시간")
            
            # 임시 파일 정리
            os.remove(result_file)
        
        # 통계 계산
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_results = sum(results_count) / len(results_count)
        
        print(f"\n📊 벤치마크 결과 ({args.iterations}회 평균)")
        print(f"⏱️  평균 처리 시간: {avg_time:.2f}초")
        print(f"⏱️  최소 처리 시간: {min_time:.2f}초")
        print(f"⏱️  최대 처리 시간: {max_time:.2f}초")
        print(f"🚀 평균 처리 속도: {video_duration/avg_time:.2f}x 실시간")
        print(f"🎲 평균 감지 핸드: {avg_results:.1f}개")
        print(f"📈 처리 안정성: {(1 - (max_time - min_time) / avg_time) * 100:.1f}%")
        
    except Exception as e:
        print(f"❌ 벤치마크 중 오류 발생: {e}")

def run_comparison(args):
    """기존 시스템과 비교"""
    if not Path(args.video_path).exists():
        print(f"❌ 비디오 파일을 찾을 수 없습니다: {args.video_path}")
        return
    
    print(f"⚖️  시스템 비교 시작: {args.video_path}")
    
    try:
        # 기존 시스템 (단순 버전)
        print("1️⃣  기존 시스템 실행...")
        from src.detect_hands import analyze_video as old_analyze
        
        import time
        start_time = time.time()
        old_analyze(args.video_path)  # 기존 시스템은 콘솔 출력만
        old_time = time.time() - start_time
        
        # 새 시스템
        print("2️⃣  새 시스템 실행...")
        from src.hand_boundary_detector import HandBoundaryDetector
        
        detector = HandBoundaryDetector()
        start_time = time.time()
        result_file = detector.analyze_video(args.video_path)
        new_time = time.time() - start_time
        
        # 결과 비교
        with open(result_file, 'r') as f:
            new_results = json.load(f)
        
        print(f"\n📊 비교 결과")
        print(f"⏱️  기존 시스템 처리 시간: {old_time:.2f}초")
        print(f"⏱️  새 시스템 처리 시간: {new_time:.2f}초")
        print(f"📈 속도 개선: {old_time/new_time:.2f}x")
        print(f"🎲 새 시스템 감지 핸드: {len(new_results)}개")
        
        if new_results:
            avg_confidence = sum(h['overall_confidence'] for h in new_results) / len(new_results)
            print(f"📈 평균 신뢰도: {avg_confidence:.1f}")
        
        # 기준 결과와 비교 (옵션)
        if args.baseline and Path(args.baseline).exists():
            with open(args.baseline, 'r') as f:
                baseline = json.load(f)
            
            print(f"\n🎯 기준 결과와 비교")
            print(f"📁 기준 파일: {args.baseline}")
            print(f"🎲 기준 핸드 수: {len(baseline)}개")
            print(f"🎲 새 시스템 핸드 수: {len(new_results)}개")
            print(f"📊 정확도: {min(len(new_results), len(baseline)) / max(len(new_results), len(baseline)) * 100:.1f}%")
        
        # 정리
        os.remove(result_file)
        
    except Exception as e:
        print(f"❌ 비교 중 오류 발생: {e}")

if __name__ == "__main__":
    main()