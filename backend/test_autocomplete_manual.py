#!/usr/bin/env python
"""
Manual test script for autocomplete endpoint
Run the FastAPI server first: uvicorn app.main:app --reload
Then run this script: python test_autocomplete_manual.py
"""

import httpx
import json
from typing import List, Dict


def test_autocomplete(query: str, limit: int = 5) -> Dict:
    """Test single autocomplete request"""
    url = "http://localhost:8000/api/autocomplete"
    params = {"q": query, "limit": limit}

    print(f"\n🔍 Testing: '{query}' (limit={limit})")
    print("-" * 50)

    try:
        with httpx.Client() as client:
            response = client.get(url, params=params, timeout=5.0)

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Source: {data['source']}")
                print(f"Response Time: {data['response_time_ms']}ms")
                print(f"Total Results: {data['total']}")
                print(f"Suggestions:")
                for i, suggestion in enumerate(data['suggestions'], 1):
                    print(f"  {i}. {suggestion}")
            else:
                print(f"Error: {response.text}")

            return response.json() if response.status_code == 200 else {"error": response.text}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}


def test_validation_errors():
    """Test validation error cases"""
    print("\n" + "="*60)
    print("TESTING VALIDATION ERRORS")
    print("="*60)

    test_cases = [
        ("P", 5, "Query too short"),
        ("a" * 101, 5, "Query too long"),
        ("Phil<script>", 5, "Invalid characters"),
        ("Phil'; DROP TABLE", 5, "SQL injection attempt"),
        ("Phil", 0, "Invalid limit (too low)"),
        ("Phil", 20, "Invalid limit (too high)"),
    ]

    for query, limit, description in test_cases:
        print(f"\n❌ Test: {description}")
        print(f"   Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        print(f"   Limit: {limit}")

        url = "http://localhost:8000/api/autocomplete"
        params = {"q": query, "limit": limit}

        try:
            with httpx.Client() as client:
                response = client.get(url, params=params, timeout=5.0)
                print(f"   Status: {response.status_code}")

                if response.status_code != 200:
                    error_data = response.json()
                    if "detail" in error_data:
                        if isinstance(error_data["detail"], list):
                            # FastAPI validation error format
                            for err in error_data["detail"]:
                                print(f"   Error: {err.get('msg', err)}")
                        else:
                            print(f"   Error: {error_data['detail']}")

        except Exception as e:
            print(f"   Connection Error: {e}")


def test_rate_limiting():
    """Test rate limiting (100 req/min)"""
    print("\n" + "="*60)
    print("TESTING RATE LIMITING")
    print("="*60)

    url = "http://localhost:8000/api/autocomplete"
    params = {"q": "Phil", "limit": 5}

    print("\n⏱️ Sending 105 rapid requests to test rate limiting...")

    success_count = 0
    rate_limited_count = 0

    with httpx.Client() as client:
        for i in range(105):
            try:
                response = client.get(url, params=params, timeout=1.0)

                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
                    if rate_limited_count == 1:
                        print(f"\n🛑 Rate limit hit at request #{i+1}")
                        error_data = response.json()
                        print(f"   Error: {error_data['detail']['message']}")

            except Exception as e:
                print(f"   Request #{i+1} failed: {e}")

    print(f"\n📊 Results:")
    print(f"   Successful: {success_count}")
    print(f"   Rate Limited: {rate_limited_count}")
    print(f"   Expected: ~100 successful, ~5 rate limited")


def test_two_tier_strategy():
    """Test two-tier search strategy"""
    print("\n" + "="*60)
    print("TESTING TWO-TIER SEARCH STRATEGY")
    print("="*60)

    # Test cases that might trigger different tiers
    test_cases = [
        ("Phil", 5, "Common prefix - should use BigQuery cache"),
        ("Junglman", 3, "Typo - might need Vertex AI"),
        ("xyz123", 5, "No results - will try both tiers"),
        ("river call", 5, "Multi-word - semantic search helpful"),
        ("3-bet", 5, "Special term - might need semantic"),
    ]

    for query, limit, description in test_cases:
        print(f"\n🔬 {description}")
        result = test_autocomplete(query, limit)

        if "source" in result:
            tier_emoji = {
                "bigquery_cache": "⚡",
                "vertex_ai": "🧠",
                "hybrid": "🔄"
            }.get(result["source"], "❓")
            print(f"   Tier Used: {tier_emoji} {result['source']}")


def main():
    """Run all manual tests"""
    print("="*60)
    print("AUTOCOMPLETE ENDPOINT MANUAL TEST")
    print("="*60)

    # Test normal cases
    print("\n" + "="*60)
    print("TESTING NORMAL CASES")
    print("="*60)

    normal_cases = [
        ("Phil", 5),
        ("Tom", 3),
        ("Daniel Neg", 5),
        ("river", 10),
        ("all-in", 5),
    ]

    for query, limit in normal_cases:
        test_autocomplete(query, limit)

    # Test validation errors
    test_validation_errors()

    # Test two-tier strategy
    test_two_tier_strategy()

    # Test rate limiting (optional - sends many requests)
    print("\n" + "="*60)
    response = input("\n⚠️ Test rate limiting? This will send 105 requests (y/n): ")
    if response.lower() == 'y':
        test_rate_limiting()

    print("\n" + "="*60)
    print("✅ Manual testing complete!")
    print("="*60)


if __name__ == "__main__":
    main()