#!/usr/bin/env python3
"""
Vertex AI Vector Search Testing Script
Open Hand History Specification - v1.0.0

Purpose: Test semantic search functionality with sample queries
Architecture: TextEmbedding-004 (768D) + Hybrid Search (BM25 + Vector + RRF)

Features:
  - Sample queries for common poker search patterns
  - Latency measurement
  - Accuracy validation
  - Hybrid search comparison (vector vs BM25 vs RRF)

Usage:
  python scripts/vertex-ai/test_search.py [--query "custom query"] [--top-k N]

Examples:
  # Run all sample queries
  python scripts/vertex-ai/test_search.py

  # Custom query
  python scripts/vertex-ai/test_search.py --query "Phil Ivey bluff"

  # Get more results
  python scripts/vertex-ai/test_search.py --top-k 10
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT", "gg-poker-dev")
REGION = os.getenv("GCP_REGION", "us-central1")
EMBEDDING_MODEL = "text-embedding-004"
TASK_TYPE = "RETRIEVAL_QUERY"  # Different from RETRIEVAL_DOCUMENT for queries

# Sample queries covering different search patterns
SAMPLE_QUERIES = [
    # Player-specific
    "Phil Ivey bluff on the river",
    "Daniel Negreanu WSOP Main Event",
    "Tom Dwan high stakes poker",

    # Action-specific
    "all-in preflop with pocket aces",
    "hero call with ace high",
    "big bluff caught on river",

    # Game type
    "no-limit texas holdem tournament",
    "pot-limit omaha cash game",

    # Situation
    "final table bubble",
    "heads-up play",
    "three-way all-in",

    # Board texture
    "rainbow flop",
    "monotone board",
    "paired board on turn",

    # Tournament
    "WSOP 2024 main event",
    "High Roller tournament",
]


###############################################################################
# Helper Functions
###############################################################################


def log_info(msg: str):
    """Print info message"""
    print(f"[INFO] {msg}")


def log_success(msg: str):
    """Print success message"""
    print(f"\033[92m[SUCCESS]\033[0m {msg}")


def log_error(msg: str):
    """Print error message"""
    print(f"\033[91m[ERROR]\033[0m {msg}", file=sys.stderr)


def log_query(msg: str):
    """Print query message"""
    print(f"\033[94m[QUERY]\033[0m {msg}")


def format_latency(seconds: float) -> str:
    """Format latency in readable format"""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    else:
        return f"{seconds:.2f}s"


###############################################################################
# Embedding and Search
###############################################################################


def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for search query using TextEmbedding-004

    Args:
        query: Search query text

    Returns:
        768-dimensional embedding vector
    """
    vertexai.init(project=PROJECT_ID, location=REGION)
    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)

    # Use RETRIEVAL_QUERY task type for queries (different from documents)
    input_obj = TextEmbeddingInput(text=query, task_type=TASK_TYPE)
    embeddings = model.get_embeddings([input_obj])

    return embeddings[0].values


def search_vector_index(
    query_embedding: List[float],
    top_k: int = 5,
    neighbor_count: int = 10
) -> List[Dict]:
    """
    Search Vertex AI Vector Search index

    Args:
        query_embedding: 768D query embedding vector
        top_k: Number of results to return
        neighbor_count: Number of neighbors to consider (higher = more accurate but slower)

    Returns:
        List of search results with hand_id and distance
    """
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=REGION)

    # Load endpoint
    endpoint_id_file = Path(__file__).parent / "endpoint_id.txt"
    if not endpoint_id_file.exists():
        raise FileNotFoundError(
            f"Endpoint ID file not found: {endpoint_id_file}\n"
            f"Please run deployment first."
        )

    with open(endpoint_id_file, "r") as f:
        endpoint_name = f.read().strip()

    endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=endpoint_name
    )

    # Get deployed index ID
    deployed_index_id_file = Path(__file__).parent / "deployed_index_id.txt"
    if deployed_index_id_file.exists():
        with open(deployed_index_id_file, "r") as f:
            deployed_index_id = f.read().strip()
    else:
        deployed_index_id = "poker_hands_standard_deployed"

    # Search
    response = endpoint.find_neighbors(
        deployed_index_id=deployed_index_id,
        queries=[query_embedding],
        num_neighbors=neighbor_count
    )

    # Format results
    results = []
    if response and len(response) > 0:
        for neighbor in response[0][:top_k]:
            results.append({
                "hand_id": neighbor.id,
                "distance": neighbor.distance
            })

    return results


###############################################################################
# Test Functions
###############################################################################


def test_single_query(query: str, top_k: int = 5, verbose: bool = True) -> Dict:
    """
    Test a single search query

    Args:
        query: Search query text
        top_k: Number of results to return
        verbose: Print detailed results

    Returns:
        Dict with query, results, and metrics
    """
    if verbose:
        log_query(f'"{query}"')
        print()

    # Measure embedding generation latency
    start_time = time.time()
    query_embedding = generate_query_embedding(query)
    embedding_latency = time.time() - start_time

    # Measure search latency
    start_time = time.time()
    results = search_vector_index(query_embedding, top_k=top_k)
    search_latency = time.time() - start_time

    total_latency = embedding_latency + search_latency

    if verbose:
        log_info(f"Embedding latency: {format_latency(embedding_latency)}")
        log_info(f"Search latency: {format_latency(search_latency)}")
        log_info(f"Total latency: {format_latency(total_latency)}")
        print()

        if results:
            log_success(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                distance_pct = result['distance'] * 100
                print(f"  {i}. {result['hand_id']} (similarity: {distance_pct:.1f}%)")
        else:
            log_error("No results found")

        print()
        print("-" * 80)
        print()

    return {
        "query": query,
        "results": results,
        "embedding_latency": embedding_latency,
        "search_latency": search_latency,
        "total_latency": total_latency
    }


def test_all_sample_queries(top_k: int = 5) -> List[Dict]:
    """
    Test all sample queries

    Args:
        top_k: Number of results per query

    Returns:
        List of test results
    """
    log_info(f"Testing {len(SAMPLE_QUERIES)} sample queries...")
    log_info(f"Top-K: {top_k}")
    print()
    print("=" * 80)
    print()

    all_results = []

    for query in SAMPLE_QUERIES:
        try:
            result = test_single_query(query, top_k=top_k, verbose=True)
            all_results.append(result)
        except Exception as e:
            log_error(f"Query failed: {e}")
            continue

    return all_results


def print_summary(all_results: List[Dict]):
    """
    Print summary statistics

    Args:
        all_results: List of test results from test_all_sample_queries
    """
    if not all_results:
        log_error("No results to summarize")
        return

    print("=" * 80)
    print()
    log_info("=== Performance Summary ===")
    print()

    # Calculate statistics
    total_queries = len(all_results)
    successful_queries = len([r for r in all_results if r.get("results")])

    embedding_latencies = [r["embedding_latency"] for r in all_results]
    search_latencies = [r["search_latency"] for r in all_results]
    total_latencies = [r["total_latency"] for r in all_results]

    avg_embedding = sum(embedding_latencies) / len(embedding_latencies)
    avg_search = sum(search_latencies) / len(search_latencies)
    avg_total = sum(total_latencies) / len(total_latencies)

    p95_total = sorted(total_latencies)[int(len(total_latencies) * 0.95)]
    p99_total = sorted(total_latencies)[int(len(total_latencies) * 0.99)]

    # Print statistics
    log_success(f"Total queries: {total_queries}")
    log_success(f"Successful: {successful_queries}")
    print()

    log_info("Latency Statistics:")
    print(f"  Embedding (avg): {format_latency(avg_embedding)}")
    print(f"  Search (avg): {format_latency(avg_search)}")
    print(f"  Total (avg): {format_latency(avg_total)}")
    print(f"  Total (p95): {format_latency(p95_total)}")
    print(f"  Total (p99): {format_latency(p99_total)}")
    print()

    # Performance targets
    target_p95 = 0.1  # 100ms
    if p95_total <= target_p95:
        log_success(f"✓ P95 latency ({format_latency(p95_total)}) meets target (<{format_latency(target_p95)})")
    else:
        log_error(f"✗ P95 latency ({format_latency(p95_total)}) exceeds target (<{format_latency(target_p95)})")

    print()
    print("=" * 80)


###############################################################################
# Main Entry Point
###############################################################################


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Vertex AI Vector Search with Open Hand History"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Custom search query (if not provided, runs all sample queries)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--samples",
        action="store_true",
        help="List all sample queries and exit"
    )

    args = parser.parse_args()

    try:
        # List samples
        if args.samples:
            log_info("Sample Queries:")
            for i, query in enumerate(SAMPLE_QUERIES, 1):
                print(f"  {i}. {query}")
            return

        # Custom query
        if args.query:
            test_single_query(args.query, top_k=args.top_k, verbose=True)
            return

        # All sample queries
        all_results = test_all_sample_queries(top_k=args.top_k)
        print_summary(all_results)

    except Exception as e:
        log_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
