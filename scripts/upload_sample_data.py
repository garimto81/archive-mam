#!/usr/bin/env python3
"""
Upload Sample Data to BigQuery
Workaround for bq CLI encoding issues on Windows
"""
import json
from pathlib import Path
from google.cloud import bigquery

PROJECT_ID = "gg-poker-prod"
DATASET_ID = "prod"
MOCK_DATA_DIR = Path("mock_data/bigquery")

def load_json(file_path):
    """Load JSON file (array or JSONL)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        # Try JSON array first
        if content.startswith('['):
            return json.loads(content)
        # Fall back to JSONL
        else:
            data = []
            for line in content.split('\n'):
                if line.strip():
                    data.append(json.loads(line))
            return data

def main():
    client = bigquery.Client(project=PROJECT_ID)

    # Upload hand_summary
    print("Uploading hand_summary...")
    hand_file = MOCK_DATA_DIR / "hand_summary_real.json"
    if not hand_file.exists():
        hand_file = MOCK_DATA_DIR / "hand_summary_mock.json"

    if hand_file.exists():
        data = load_json(hand_file)
        table_id = f"{PROJECT_ID}.{DATASET_ID}.hand_summary"

        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        job = client.load_table_from_json(
            data, table_id, job_config=job_config
        )
        job.result()
        print(f"[OK] Uploaded {len(data)} hands")
    else:
        print(f"[SKIP] hand_summary file not found")

    # Upload video_files
    print("Uploading video_files...")
    video_file = MOCK_DATA_DIR / "video_files_real.json"
    if not video_file.exists():
        video_file = MOCK_DATA_DIR / "video_files_mock.json"

    if video_file.exists():
        data = load_json(video_file)
        table_id = f"{PROJECT_ID}.{DATASET_ID}.video_files"

        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        job = client.load_table_from_json(
            data, table_id, job_config=job_config
        )
        job.result()
        print(f"[OK] Uploaded {len(data)} videos")
    else:
        print(f"[SKIP] video_files file not found")

    # Upload embeddings
    print("Uploading hand_embeddings...")
    embed_file = Path("mock_data/embeddings/hand_embeddings_real.json")
    if not embed_file.exists():
        embed_file = Path("mock_data/embeddings/hand_embeddings_mock.json")

    if embed_file.exists():
        data = load_json(embed_file)
        table_id = f"{PROJECT_ID}.{DATASET_ID}.hand_embeddings"

        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        job = client.load_table_from_json(
            data, table_id, job_config=job_config
        )
        job.result()
        print(f"[OK] Uploaded {len(data)} embeddings")
    else:
        print(f"[SKIP] embeddings file not found, skipping")

    # Verify
    print("\n" + "="*50)
    print("Verification")
    print("="*50)

    tables = ["hand_summary", "video_files", "hand_embeddings"]
    for table_name in tables:
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`"
        result = list(client.query(query).result())
        count = result[0].count
        print(f"{table_name}: {count} rows")

    print("\n[SUCCESS] Sample data upload complete!")

if __name__ == "__main__":
    main()
