#!/usr/bin/env python3
"""
Create BigQuery Dataset and Tables
Workaround for bq CLI encoding issues on Windows
"""
import os
from google.cloud import bigquery

# Set project
PROJECT_ID = "gg-poker-prod"
DATASET_ID = "prod"
LOCATION = "us-central1"

def main():
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)

    # 1. Create dataset
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = LOCATION
    dataset.description = "POKER-BRAIN Production Dataset"

    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"✓ Dataset {dataset_id} created")
    except Exception as e:
        print(f"✗ Dataset creation failed: {e}")
        return

    # 2. Create tables
    tables_schema = {
        "hand_summary": [
            bigquery.SchemaField("hand_id", "STRING"),
            bigquery.SchemaField("event_id", "STRING"),
            bigquery.SchemaField("tournament_id", "STRING"),
            bigquery.SchemaField("table_id", "STRING"),
            bigquery.SchemaField("hand_number", "INTEGER"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("summary_text", "STRING"),
            bigquery.SchemaField("player_names", "STRING"),
            bigquery.SchemaField("pot_size_usd", "FLOAT"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
        "video_files": [
            bigquery.SchemaField("file_id", "STRING"),
            bigquery.SchemaField("video_path", "STRING"),
            bigquery.SchemaField("proxy_path", "STRING"),
            bigquery.SchemaField("duration_seconds", "FLOAT"),
            bigquery.SchemaField("resolution", "STRING"),
            bigquery.SchemaField("codec", "STRING"),
            bigquery.SchemaField("file_size_bytes", "INTEGER"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
        "timecode_validation": [
            bigquery.SchemaField("validation_id", "STRING"),
            bigquery.SchemaField("hand_id", "STRING"),
            bigquery.SchemaField("video_path", "STRING"),
            bigquery.SchemaField("sync_score", "FLOAT"),
            bigquery.SchemaField("vision_confidence", "FLOAT"),
            bigquery.SchemaField("suggested_offset", "INTEGER"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
        "hand_embeddings": [
            bigquery.SchemaField("hand_id", "STRING"),
            bigquery.SchemaField("summary_text", "STRING"),
            bigquery.SchemaField("embedding", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
        "clipping_requests": [
            bigquery.SchemaField("request_id", "STRING"),
            bigquery.SchemaField("hand_id", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("output_gcs_path", "STRING"),
            bigquery.SchemaField("download_url", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("completed_at", "TIMESTAMP"),
        ],
    }

    for table_name, schema in tables_schema.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)

        try:
            table = client.create_table(table, exists_ok=True)
            print(f"✓ Table {table_name} created")
        except Exception as e:
            print(f"✗ Table {table_name} failed: {e}")

    print("\n✅ All BigQuery resources created successfully!")

    # Verify
    print("\nDataset info:")
    dataset = client.get_dataset(dataset_id)
    print(f"  Location: {dataset.location}")
    print(f"  Tables: {len(list(client.list_tables(dataset)))}")

if __name__ == "__main__":
    main()
