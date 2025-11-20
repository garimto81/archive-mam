#!/usr/bin/env python3
"""BigQuery 직접 쿼리"""
from google.cloud import bigquery
import os

os.environ["GCP_PROJECT"] = "gg-poker-prod"
client = bigquery.Client(project="gg-poker-prod")

# 직접 쿼리
query = """
    SELECT hand_id, hero_name, pot_bb, created_at
    FROM `gg-poker-prod.poker_archive.hands`
    ORDER BY created_at DESC
    LIMIT 10
"""

print("BigQuery 쿼리 실행 중...")
results = client.query(query).result()

count = 0
for row in results:
    count += 1
    print(f"\n{count}. Hand ID: {row.hand_id}")
    print(f"   Hero: {row.hero_name}")
    print(f"   Pot (BB): {row.pot_bb}")
    print(f"   Created: {row.created_at}")

if count == 0:
    print("\n결과 없음 - 테이블이 비어있거나 쿼리 실패")
else:
    print(f"\n총 {count}개 행 조회됨")
