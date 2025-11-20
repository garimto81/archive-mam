#!/usr/bin/env python3
"""
BigQuery → Vertex AI Vector Search Embedding Upload
Open Hand History Specification - v1.0.0

Purpose: Generate embeddings from BigQuery hands_standard table and upload to Vertex AI
Architecture: TextEmbedding-004 (768D) + Batch processing + Cost optimization

Workflow:
  1. Query BigQuery hands_standard table for hand metadata
  2. Generate rich text descriptions from Open Hand History data
  3. Create embeddings using Vertex AI TextEmbedding-004
  4. Upload embeddings to Vertex AI Vector Search (100 hands per batch)
  5. Track progress and handle errors gracefully

Usage:
  python scripts/vertex-ai/upload_embeddings.py [--limit N] [--batch-size N] [--offset N]

Examples:
  # Test with 10 hands
  python scripts/vertex-ai/upload_embeddings.py --limit 10

  # Upload all hands
  python scripts/vertex-ai/upload_embeddings.py

  # Resume from offset 1000
  python scripts/vertex-ai/upload_embeddings.py --offset 1000 --limit 500
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import bigquery, aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT", "gg-poker-dev")
REGION = os.getenv("GCP_REGION", "us-central1")
BIGQUERY_DATASET = os.getenv("BQ_DATASET", "poker_archive_dev")
BIGQUERY_TABLE = "hands_standard"  # Open Hand History table

# Embedding Configuration
EMBEDDING_MODEL = "text-embedding-004"  # 768 dimensions
BATCH_SIZE = 100  # Vertex AI API batch limit
TASK_TYPE = "RETRIEVAL_DOCUMENT"  # Optimal for search


###############################################################################
# Helper Functions
###############################################################################


def log_info(msg: str):
    """Print info message"""
    print(f"[INFO] {msg}")


def log_success(msg: str):
    """Print success message"""
    print(f"[SUCCESS] {msg}")


def log_error(msg: str):
    """Print error message"""
    print(f"[ERROR] {msg}", file=sys.stderr)


def log_warn(msg: str):
    """Print warning message"""
    print(f"[WARNING] {msg}")


###############################################################################
# BigQuery Data Retrieval
###############################################################################


def build_search_text(row: bigquery.Row) -> str:
    """
    Build rich search text from Open Hand History data

    Combines multiple fields to create a comprehensive description for embedding:
    - Game metadata (game_number, game_type, table_name)
    - Players (names, positions, stack sizes)
    - Actions (preflop, flop, turn, river)
    - Results (winner, pot size, showdown)
    - Tournament info (if applicable)

    This rich text enables semantic search across all dimensions of hand history.
    """
    parts = []

    # Game identifier
    if row.game_number:
        parts.append(f"Hand {row.game_number}")

    # Game type and betting
    if row.game_type:
        parts.append(f"{row.game_type}")
    if row.bet_limit_type:
        parts.append(f"{row.bet_limit_type}")

    # Table/tournament info
    if row.table_name:
        parts.append(f"at {row.table_name}")
    if row.tournament_name:
        parts.append(f"({row.tournament_name})")

    # Players
    if row.players:
        try:
            players = json.loads(row.players) if isinstance(row.players, str) else row.players
            player_names = [p.get("name") or p.get("player_name") for p in players if p.get("name") or p.get("player_name")]
            if player_names:
                parts.append(f"Players: {', '.join(player_names[:6])}")  # Limit to 6 players
        except (json.JSONDecodeError, TypeError):
            pass

    # Hero/Villain (from legacy format)
    if row.hero_name:
        parts.append(f"Hero: {row.hero_name}")
    if row.villain_name:
        parts.append(f"Villain: {row.villain_name}")

    # Board cards
    if row.board_cards:
        try:
            cards = json.loads(row.board_cards) if isinstance(row.board_cards, str) else row.board_cards
            if cards:
                parts.append(f"Board: {' '.join(cards)}")
        except (json.JSONDecodeError, TypeError):
            pass

    # Pot and stakes
    if row.pot_size:
        parts.append(f"Pot: {row.pot_size}")

    # Actions summary
    if row.rounds:
        try:
            rounds = json.loads(row.rounds) if isinstance(row.rounds, str) else row.rounds
            for round_data in rounds:
                street = round_data.get("street", "unknown")
                actions = round_data.get("actions", [])
                if actions:
                    action_summary = f"{street}: {len(actions)} actions"
                    parts.append(action_summary)
        except (json.JSONDecodeError, TypeError):
            pass

    # Winner/result
    if row.winner:
        parts.append(f"Winner: {row.winner}")

    # Tags (for categorization)
    if row.tags:
        try:
            tags = json.loads(row.tags) if isinstance(row.tags, str) else row.tags
            if tags:
                parts.append(f"Tags: {', '.join(tags[:5])}")  # Limit to 5 tags
        except (json.JSONDecodeError, TypeError):
            pass

    # Description (if available)
    if row.description:
        parts.append(row.description)

    return ". ".join(parts)


def get_hands_from_bigquery(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
    """
    Query BigQuery hands_standard table for hand metadata

    Returns list of dicts with:
      - hand_id: unique identifier
      - search_text: rich description for embedding
    """
    log_info("=== BigQuery Data Retrieval ===")
    log_info(f"Dataset: {BIGQUERY_DATASET}")
    log_info(f"Table: {BIGQUERY_TABLE}")

    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"

    # Query all relevant fields for rich embedding
    query = f"""
        SELECT
            hand_id,
            game_number,
            game_type,
            bet_limit_type,
            table_name,
            tournament_name,
            players,  -- JSON array of player objects
            hero_name,  -- Legacy field
            villain_name,  -- Legacy field
            board_cards,  -- JSON array
            pot_size,
            rounds,  -- JSON array of round objects
            winner,
            tags,  -- JSON array
            description  -- Optional text description
        FROM `{table_id}`
        WHERE hand_id IS NOT NULL
        ORDER BY created_at DESC
    """

    if offset > 0:
        query += f" OFFSET {offset}"

    if limit:
        query += f" LIMIT {limit}"

    log_info(f"Executing query (offset={offset}, limit={limit or 'all'})...")
    results = client.query(query).result()

    hands = []
    for row in results:
        # Build rich search text
        search_text = build_search_text(row)

        hands.append({
            "hand_id": row.hand_id,
            "search_text": search_text
        })

    log_success(f"Retrieved {len(hands)} hands from BigQuery")
    return hands


###############################################################################
# Embedding Generation
###############################################################################


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using Vertex AI TextEmbedding-004

    Args:
        texts: List of text strings to embed

    Returns:
        List of 768-dimensional embedding vectors
    """
    # Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=REGION)

    # Load embedding model
    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)

    # Create TextEmbeddingInput objects
    inputs = [
        TextEmbeddingInput(text=text, task_type=TASK_TYPE)
        for text in texts
    ]

    # Generate embeddings
    embeddings = model.get_embeddings(inputs)

    # Extract vectors
    embedding_vectors = [emb.values for emb in embeddings]

    return embedding_vectors


###############################################################################
# Vector Search Upload
###############################################################################


def upload_to_vector_search(hands: List[Dict], batch_size: int = BATCH_SIZE):
    """
    Upload embeddings to Vertex AI Vector Search

    Args:
        hands: List of hand dicts with hand_id and search_text
        batch_size: Number of hands to process per batch
    """
    log_info("=== Vertex AI Vector Search Upload ===")

    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=REGION)

    # Load endpoint
    endpoint_id_file = Path(__file__).parent / "endpoint_id.txt"
    if not endpoint_id_file.exists():
        raise FileNotFoundError(
            f"Endpoint ID file not found: {endpoint_id_file}\n"
            f"Please run 'python scripts/vertex-ai/deploy_index.py' first."
        )

    with open(endpoint_id_file, "r") as f:
        endpoint_name = f.read().strip()

    endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=endpoint_name
    )

    # Load index
    index_id_file = Path(__file__).parent / "index_id.txt"
    with open(index_id_file, "r") as f:
        index_name = f.read().strip()

    index = aiplatform.MatchingEngineIndex(index_name=index_name)

    log_info(f"Index: {index_name}")
    log_info(f"Endpoint: {endpoint_name}")
    log_info(f"Total hands: {len(hands)}")

    # Process in batches
    total_batches = (len(hands) + batch_size - 1) // batch_size
    log_info(f"Batch size: {batch_size}")
    log_info(f"Total batches: {total_batches}")

    success_count = 0
    error_count = 0

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(hands))
        batch_hands = hands[start_idx:end_idx]

        log_info(f"\n[{batch_idx + 1}/{total_batches}] Processing batch...")
        log_info(f"  Hand range: {start_idx} - {end_idx}")

        try:
            # 1. Generate embeddings
            search_texts = [hand["search_text"] for hand in batch_hands]
            embeddings = generate_embeddings(search_texts)

            log_success(f"  Generated {len(embeddings)} embeddings")

            # 2. Create datapoints
            datapoints = []
            for hand, embedding in zip(batch_hands, embeddings):
                datapoints.append({
                    "datapoint_id": hand["hand_id"],
                    "feature_vector": embedding
                })

            # 3. Upload to Vertex AI
            log_info(f"  Uploading to Vertex AI...")
            index.upsert_datapoints(datapoints=datapoints)

            log_success(f"  Batch upload complete")
            success_count += len(batch_hands)

        except Exception as e:
            log_error(f"  Batch failed: {e}")
            error_count += len(batch_hands)

            # Continue with next batch
            continue

        # Rate limiting (60 requests per minute)
        if batch_idx < total_batches - 1:
            time.sleep(1)

    log_info(f"\n=== Upload Summary ===")
    log_success(f"Successfully uploaded: {success_count} hands")
    if error_count > 0:
        log_error(f"Failed uploads: {error_count} hands")

    return success_count, error_count


###############################################################################
# Main Entry Point
###############################################################################


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload Open Hand History embeddings to Vertex AI Vector Search"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of hands to upload (default: all)"
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset for resuming upload (default: 0)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size for processing (default: {BATCH_SIZE})"
    )

    args = parser.parse_args()

    try:
        # 1. Retrieve hands from BigQuery
        log_info(f"Starting embedding upload...")
        hands = get_hands_from_bigquery(limit=args.limit, offset=args.offset)

        if not hands:
            log_warn("No hands found in BigQuery")
            return

        # 2. Upload embeddings to Vertex AI
        success_count, error_count = upload_to_vector_search(
            hands,
            batch_size=args.batch_size
        )

        # 3. Summary
        log_info("\n" + "=" * 60)
        log_success("Embedding upload complete!")
        log_info(f"Total processed: {len(hands)}")
        log_info(f"Successful: {success_count}")
        log_info(f"Failed: {error_count}")
        log_info("=" * 60 + "\n")

        if error_count > 0:
            log_warn("Some uploads failed. Check logs above for details.")
            sys.exit(1)

    except Exception as e:
        log_error(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
