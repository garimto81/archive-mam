#!/usr/bin/env python
"""
성능 테스트 및 최적화 도구
"""
import time
import psutil
import httpx
import asyncio
import concurrent.futures
import json
import statistics
from datetime import datetime
from pathlib import Path

class PerformanceTester:
    """성능 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def measure_response_time(self, endpoint, method="GET", data=None, iterations=10):
        """응답 시간 측정"""
        times = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                with httpx.Client(timeout=30.0) as client:
                    if method == "GET":
                        response = client.get(f"{self.base_url}{endpoint}")
                    elif method == "POST":
                        response = client.post(f"{self.base_url}{endpoint}", json=data)
                    
                    if response.status_code == 200:
                        end_time = time.perf_counter()
                        times.append(end_time - start_time)
                    else:
                        print(f"❌ {endpoint}: HTTP {response.status_code}")
            
            except Exception as e:
                print(f"❌ {endpoint}: {e}")
        
        if times:
            return {
                "endpoint": endpoint,
                "method": method,
                "iterations": len(times),
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "median_time": statistics.median(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0
            }
        return None
    
    def test_concurrent_requests(self, endpoint, concurrent_users=10, requests_per_user=5):
        """동시 요청 테스트"""
        def make_requests():
            times = []
            for _ in range(requests_per_user):
                start_time = time.perf_counter()
                try:
                    with httpx.Client(timeout=10.0) as client:
                        response = client.get(f"{self.base_url}{endpoint}")
                        if response.status_code == 200:
                            end_time = time.perf_counter()
                            times.append(end_time - start_time)
                except:
                    pass
            return times
        
        print(f"동시성 테스트: {concurrent_users}명 사용자, 사용자당 {requests_per_user}개 요청")
        
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_requests) for _ in range(concurrent_users)]
            all_times = []
            
            for future in concurrent.futures.as_completed(futures):
                times = future.result()
                all_times.extend(times)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        if all_times:
            return {
                "endpoint": endpoint,
                "concurrent_users": concurrent_users,
                "total_requests": len(all_times),
                "total_time": total_time,
                "requests_per_second": len(all_times) / total_time,
                "avg_response_time": statistics.mean(all_times),
                "success_rate": len(all_times) / (concurrent_users * requests_per_user) * 100
            }
        return None
    
    def monitor_system_resources(self, duration=60):
        """시스템 리소스 모니터링"""
        print(f"시스템 리소스 모니터링 시작 ({duration}초)...")
        
        cpu_usage = []
        memory_usage = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            cpu_usage.append(psutil.cpu_percent(interval=1))
            memory_usage.append(psutil.virtual_memory().percent)
        
        return {
            "duration": duration,
            "cpu_avg": statistics.mean(cpu_usage),
            "cpu_max": max(cpu_usage),
            "memory_avg": statistics.mean(memory_usage),
            "memory_max": max(memory_usage)
        }
    
    def analyze_database_performance(self):
        """데이터베이스 성능 분석"""
        db_tests = [
            ("/hands/", "핸드 목록 조회"),
            ("/videos/", "영상 목록 조회"),
            ("/stats", "통계 조회"),
        ]
        
        results = []
        for endpoint, description in db_tests:
            print(f"DB 성능 테스트: {description}")
            result = self.measure_response_time(endpoint, iterations=20)
            if result:
                result["description"] = description
                results.append(result)
        
        return results
    
    def test_large_dataset_handling(self):
        """대용량 데이터 처리 테스트"""
        # 많은 핸드 검색 요청
        large_search = {
            "min_pot_size": 1,
            "max_pot_size": 999999
        }
        
        print("대용량 데이터 검색 테스트...")
        result = self.measure_response_time("/hands/search", "POST", large_search, 5)
        
        if result:
            result["description"] = "대용량 핸드 검색"
            if result["avg_time"] > 2.0:
                result["warning"] = "응답 시간이 2초를 초과합니다. 인덱싱 또는 페이지네이션 개선이 필요할 수 있습니다."
        
        return result
    
    def generate_performance_report(self):
        """성능 테스트 보고서 생성"""
        print("\n" + "=" * 60)
        print("성능 테스트 보고서 생성 중...")
        print("=" * 60)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        # 기본 응답 시간 테스트
        basic_endpoints = [
            "/",
            "/stats",
            "/videos/",
            "/hands/"
        ]
        
        for endpoint in basic_endpoints:
            result = self.measure_response_time(endpoint)
            if result:
                report["tests"].append(result)
        
        # 검색 성능 테스트
        search_result = self.measure_response_time("/hands/search", "POST", {"min_pot_size": 1000})
        if search_result:
            search_result["description"] = "핸드 검색"
            report["tests"].append(search_result)
        
        # 동시성 테스트
        concurrent_result = self.test_concurrent_requests("/stats", 5, 10)
        if concurrent_result:
            report["concurrent_test"] = concurrent_result
        
        # 대용량 데이터 테스트
        large_data_result = self.test_large_dataset_handling()
        if large_data_result:
            report["large_data_test"] = large_data_result
        
        # 시스템 리소스 모니터링 (30초)
        resource_result = self.monitor_system_resources(30)
        report["system_resources"] = resource_result
        
        return report
    
    def print_report(self, report):
        """보고서 출력"""
        print("\n📊 성능 테스트 결과")
        print("=" * 60)
        
        # 기본 응답 시간
        print("\n🔍 API 응답 시간:")
        for test in report["tests"]:
            status = "🟢" if test["avg_time"] < 0.5 else "🟡" if test["avg_time"] < 2.0 else "🔴"
            print(f"{status} {test['endpoint']}: {test['avg_time']:.3f}초 (평균)")
            print(f"    최소: {test['min_time']:.3f}초, 최대: {test['max_time']:.3f}초")
        
        # 동시성 테스트 결과
        if "concurrent_test" in report:
            concurrent = report["concurrent_test"]
            print(f"\n⚡ 동시성 테스트:")
            print(f"    RPS: {concurrent['requests_per_second']:.1f} 요청/초")
            print(f"    성공률: {concurrent['success_rate']:.1f}%")
            print(f"    평균 응답시간: {concurrent['avg_response_time']:.3f}초")
        
        # 대용량 데이터 테스트
        if "large_data_test" in report:
            large_data = report["large_data_test"]
            print(f"\n📊 대용량 데이터 처리:")
            print(f"    평균 응답시간: {large_data['avg_time']:.3f}초")
            if "warning" in large_data:
                print(f"    ⚠️  {large_data['warning']}")
        
        # 시스템 리소스
        if "system_resources" in report:
            resources = report["system_resources"]
            print(f"\n💻 시스템 리소스 사용량:")
            print(f"    CPU: 평균 {resources['cpu_avg']:.1f}%, 최대 {resources['cpu_max']:.1f}%")
            print(f"    메모리: 평균 {resources['memory_avg']:.1f}%, 최대 {resources['memory_max']:.1f}%")
        
        # 성능 권장사항
        print(f"\n💡 최적화 권장사항:")
        
        slow_endpoints = [t for t in report["tests"] if t["avg_time"] > 1.0]
        if slow_endpoints:
            print("    • 다음 엔드포인트의 응답 시간 개선 필요:")
            for endpoint in slow_endpoints:
                print(f"      - {endpoint['endpoint']}: {endpoint['avg_time']:.3f}초")
        
        if "concurrent_test" in report and report["concurrent_test"]["success_rate"] < 95:
            print("    • 동시 요청 처리 능력 개선 필요")
        
        if "system_resources" in report:
            if report["system_resources"]["cpu_max"] > 80:
                print("    • CPU 사용량 최적화 필요")
            if report["system_resources"]["memory_max"] > 80:
                print("    • 메모리 사용량 최적화 필요")


def main():
    """메인 함수"""
    try:
        # 서버 연결 확인
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:8000/")
            if response.status_code != 200:
                print("❌ 백엔드 서버에 연결할 수 없습니다.")
                print("run_test_server.bat를 실행해주세요.")
                return
    except Exception:
        print("❌ 백엔드 서버에 연결할 수 없습니다.")
        print("run_test_server.bat를 실행해주세요.")
        return
    
    tester = PerformanceTester()
    
    print("🚀 Poker MAM 성능 테스트 시작")
    print("=" * 60)
    
    # 성능 테스트 실행
    report = tester.generate_performance_report()
    
    # 결과 출력
    tester.print_report(report)
    
    # 결과를 파일로 저장
    report_file = Path("test/performance_report.json")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 상세 보고서가 {report_file}에 저장되었습니다.")


if __name__ == "__main__":
    main()