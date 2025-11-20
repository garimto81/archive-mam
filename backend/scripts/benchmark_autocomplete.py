#!/usr/bin/env python
"""
Autocomplete API 성능 벤치마크
목표: p95 < 100ms
"""

import asyncio
import time
import statistics
import httpx
from typing import List, Tuple
import argparse
from tabulate import tabulate
import json


async def measure_request(client: httpx.AsyncClient, query: str, limit: int = 5) -> Tuple[float, int, str]:
    """
    단일 요청 측정

    Returns:
        (response_time_ms, status_code, source)
    """
    start = time.perf_counter()

    try:
        response = await client.get(
            "/api/autocomplete",
            params={"q": query, "limit": limit},
            timeout=5.0
        )

        duration = (time.perf_counter() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            source = data.get("source", "unknown")
            return duration, response.status_code, source
        else:
            return duration, response.status_code, "error"

    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return duration, -1, str(e)


async def run_benchmark(
    base_url: str,
    queries: List[str],
    num_requests: int = 100,
    concurrent_users: int = 10
) -> dict:
    """
    벤치마크 실행

    Args:
        base_url: API 서버 URL
        queries: 테스트 쿼리 목록
        num_requests: 총 요청 수
        concurrent_users: 동시 사용자 수

    Returns:
        벤치마크 결과 딕셔너리
    """
    results = {
        "response_times": [],
        "status_codes": {},
        "sources": {},
        "errors": []
    }

    async with httpx.AsyncClient(base_url=base_url) as client:
        # Warmup
        print("Warming up...")
        for _ in range(5):
            await measure_request(client, "warmup")

        print(f"Running benchmark: {num_requests} requests with {concurrent_users} concurrent users...")

        # Create tasks
        tasks = []
        for i in range(num_requests):
            query = queries[i % len(queries)]
            tasks.append(measure_request(client, query))

            # Control concurrency
            if len(tasks) >= concurrent_users:
                batch_results = await asyncio.gather(*tasks)

                for duration, status, source in batch_results:
                    results["response_times"].append(duration)
                    results["status_codes"][status] = results["status_codes"].get(status, 0) + 1

                    if status == 200:
                        results["sources"][source] = results["sources"].get(source, 0) + 1
                    elif status != 200:
                        results["errors"].append((duration, status, source))

                tasks = []

        # Process remaining tasks
        if tasks:
            batch_results = await asyncio.gather(*tasks)
            for duration, status, source in batch_results:
                results["response_times"].append(duration)
                results["status_codes"][status] = results["status_codes"].get(status, 0) + 1

                if status == 200:
                    results["sources"][source] = results["sources"].get(source, 0) + 1
                elif status != 200:
                    results["errors"].append((duration, status, source))

    return results


def analyze_results(results: dict) -> dict:
    """
    결과 분석 및 통계 계산

    Returns:
        분석된 통계 딕셔너리
    """
    response_times = results["response_times"]

    if not response_times:
        return {"error": "No successful requests"}

    # Sort for percentile calculation
    sorted_times = sorted(response_times)

    stats = {
        "total_requests": len(response_times),
        "min_ms": min(response_times),
        "max_ms": max(response_times),
        "mean_ms": statistics.mean(response_times),
        "median_ms": statistics.median(response_times),
        "stdev_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0,
        "p50_ms": sorted_times[int(len(sorted_times) * 0.50)],
        "p75_ms": sorted_times[int(len(sorted_times) * 0.75)],
        "p90_ms": sorted_times[int(len(sorted_times) * 0.90)],
        "p95_ms": sorted_times[int(len(sorted_times) * 0.95)],
        "p99_ms": sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 100 else sorted_times[-1],
        "status_codes": results["status_codes"],
        "sources": results["sources"],
        "error_count": len(results["errors"])
    }

    # Calculate success rate
    success_count = results["status_codes"].get(200, 0)
    stats["success_rate"] = (success_count / len(response_times)) * 100

    # Check SLA compliance
    stats["sla_p95_100ms"] = stats["p95_ms"] < 100
    stats["sla_p99_200ms"] = stats["p99_ms"] < 200

    return stats


def print_results(stats: dict):
    """결과 출력"""
    print("\n" + "="*60)
    print("AUTOCOMPLETE API PERFORMANCE BENCHMARK RESULTS")
    print("="*60)

    # Response Time Statistics
    time_table = [
        ["Metric", "Value (ms)", "Status"],
        ["Min", f"{stats['min_ms']:.2f}", "✅" if stats['min_ms'] < 10 else "⚠️"],
        ["Median (p50)", f"{stats['median_ms']:.2f}", "✅" if stats['median_ms'] < 50 else "⚠️"],
        ["Mean", f"{stats['mean_ms']:.2f}", ""],
        ["p75", f"{stats['p75_ms']:.2f}", "✅" if stats['p75_ms'] < 75 else "⚠️"],
        ["p90", f"{stats['p90_ms']:.2f}", "✅" if stats['p90_ms'] < 90 else "⚠️"],
        ["p95", f"{stats['p95_ms']:.2f}", "✅" if stats['p95_ms'] < 100 else "❌"],
        ["p99", f"{stats['p99_ms']:.2f}", "✅" if stats['p99_ms'] < 200 else "❌"],
        ["Max", f"{stats['max_ms']:.2f}", ""],
    ]

    print("\n📊 Response Time Statistics:")
    print(tabulate(time_table, headers="firstrow", tablefmt="grid"))

    # Status Codes
    print("\n📈 Status Code Distribution:")
    status_table = [[code, count, f"{(count/stats['total_requests']*100):.1f}%"]
                    for code, count in stats['status_codes'].items()]
    status_table.insert(0, ["Status Code", "Count", "Percentage"])
    print(tabulate(status_table, headers="firstrow", tablefmt="grid"))

    # Data Sources
    if stats['sources']:
        print("\n🔍 Data Source Distribution:")
        source_table = [[source, count, f"{(count/sum(stats['sources'].values())*100):.1f}%"]
                       for source, count in stats['sources'].items()]
        source_table.insert(0, ["Source", "Count", "Percentage"])
        print(tabulate(source_table, headers="firstrow", tablefmt="grid"))

    # SLA Compliance
    print("\n✅ SLA Compliance:")
    sla_table = [
        ["Metric", "Target", "Actual", "Status"],
        ["p95 < 100ms", "< 100ms", f"{stats['p95_ms']:.2f}ms", "✅ PASS" if stats['sla_p95_100ms'] else "❌ FAIL"],
        ["p99 < 200ms", "< 200ms", f"{stats['p99_ms']:.2f}ms", "✅ PASS" if stats['sla_p99_200ms'] else "❌ FAIL"],
        ["Success Rate", "> 99%", f"{stats['success_rate']:.1f}%", "✅ PASS" if stats['success_rate'] > 99 else "⚠️ WARNING"],
    ]
    print(tabulate(sla_table, headers="firstrow", tablefmt="grid"))

    # Summary
    print("\n📋 Summary:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Success Rate: {stats['success_rate']:.1f}%")
    print(f"  Error Count: {stats['error_count']}")
    print(f"  Standard Deviation: {stats['stdev_ms']:.2f}ms")

    # Final verdict
    print("\n🎯 Final Verdict:")
    if stats['sla_p95_100ms'] and stats['success_rate'] > 99:
        print("  ✅ EXCELLENT - All SLA targets met!")
    elif stats['sla_p95_100ms'] and stats['success_rate'] > 95:
        print("  ⚠️  GOOD - p95 target met, but watch success rate")
    elif stats['p95_ms'] < 150:
        print("  ⚠️  ACCEPTABLE - Close to target, needs optimization")
    else:
        print("  ❌ NEEDS IMPROVEMENT - SLA targets not met")


def main():
    parser = argparse.ArgumentParser(description="Autocomplete API Performance Benchmark")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent users")
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    # Test queries (realistic poker player names)
    test_queries = [
        "Phil",       # Common prefix
        "Tom",        # Short query
        "Daniel",     # Medium query
        "Jung",       # Typo scenario
        "river",      # Action query
        "bluff",      # Strategy query
        "Phil Iv",    # Partial name
        "Hellmuth",   # Last name
        "Doug Po",    # Partial full name
        "GTO",        # Acronym
        "high stakes", # Multi-word
        "all-in",     # With hyphen
        "3-bet",      # Number + hyphen
        "AA",         # Card notation
        "texas"       # Tournament name
    ]

    # Run async benchmark
    results = asyncio.run(run_benchmark(
        args.url,
        test_queries,
        args.requests,
        args.concurrent
    ))

    # Analyze results
    stats = analyze_results(results)

    # Print results
    print_results(stats)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "config": {
                    "url": args.url,
                    "total_requests": args.requests,
                    "concurrent_users": args.concurrent
                },
                "stats": stats,
                "raw_response_times": results["response_times"][:100]  # Save first 100 for analysis
            }, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")


if __name__ == "__main__":
    main()