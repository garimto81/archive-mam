#!/usr/bin/env python3
"""BigQuery 데이터 확인 스크립트"""
from google.cloud import bigquery
import os

os.environ["GCP_PROJECT"] = "gg-poker-prod"
client = bigquery.Client(project="gg-poker-prod")

# 테이블 정보
table_id = "gg-poker-prod.poker_archive.hands"
table = client.get_table(table_id)

print(f"총 행 수: {table.num_rows}")

if table.num_rows > 0:
    # 최근 데이터 조회
    query = """
        SELECT hand_id, hero_name, pot_bb, created_at
        FROM `gg-poker-prod.poker_archive.hands`
        ORDER BY created_at DESC
        LIMIT 5
    """
    results = client.query(query).result()

    print("\n최근 삽입된 데이터:")
    print("-" * 80)
    for row in results:
        print(f"Hand ID: {row.hand_id}")
        print(f"Hero: {row.hero_name}")
        print(f"Pot (BB): {row.pot_bb}")
        print(f"Created: {row.created_at}")
        print("-" * 80)
else:
    print("테이블이 비어있습니다.")
