# PoC 검색 정확도 테스트 쿼리

**목적**: 합성 데이터를 사용한 PoC에서 검색 정확도(Precision@5)를 측정하기 위한 테스트 쿼리 20개

**측정 방법**:
1. 각 쿼리에 대해 상위 5개 결과 반환
2. 관련도 평가: 5개 중 몇 개가 쿼리 의도와 일치하는가?
3. Precision@5 = (관련 결과 수) / 5
4. 전체 평균 Precision@5 ≥ 85% 목표

---

## 테스트 쿼리 세트 (20개)

### Category 1: Player-based Queries (플레이어 중심)

**Query 1**: "Phil Ivey bluff"
- **기대 결과**: Phil Ivey가 블러프한 핸드 (hand_type: BLUFF, hero_name/villain_name: Phil Ivey)
- **예상 매칭 핸드 수**: 5-10개

**Query 2**: "Junglemann hero call"
- **기대 결과**: Junglemann이 hero call한 핸드 (hand_type: HERO_CALL, hero_name: Junglemann)
- **예상 매칭 핸드 수**: 3-7개

**Query 3**: "Daniel Negreanu river decision"
- **기대 결과**: Daniel Negreanu가 리버에서 결정한 핸드 (street: RIVER, hero_name/villain_name: Daniel Negreanu)
- **예상 매칭 핸드 수**: 5-10개

**Query 4**: "Tom Dwan all in"
- **기대 결과**: Tom Dwan이 올인한 핸드 (hand_type: ALL_IN, hero_name/villain_name: Tom Dwan)
- **예상 매칭 핸드 수**: 3-8개

### Category 2: Action-based Queries (액션 중심)

**Query 5**: "triple barrel bluff"
- **기대 결과**: 3번 베팅 후 블러프 (hand_type: BLUFF, action_sequence 길이 10+)
- **예상 매칭 핸드 수**: 5-10개

**Query 6**: "river shove fold"
- **기대 결과**: 리버에서 올인 후 폴드 (street: RIVER, hero_action: fold, tags: ALL_IN)
- **예상 매칭 핸드 수**: 3-7개

**Query 7**: "ace high call"
- **기대 결과**: 에이스 하이로 콜 (description에 "ace-high", hero_action: call)
- **예상 매칭 핸드 수**: 2-5개

**Query 8**: "slow play trap"
- **기대 결과**: 슬로우플레이 트랩 (hand_type: SLOW_PLAY, tags: TRAP)
- **예상 매칭 핸드 수**: 3-8개

### Category 3: Situation-based Queries (상황 중심)

**Query 9**: "big pot high stakes"
- **기대 결과**: 큰 팟 하이스테이크 (pot_bb ≥ 200, tags: HIGH_STAKES)
- **예상 매칭 핸드 수**: 10-20개

**Query 10**: "deep stack poker"
- **기대 결과**: 딥 스택 (hero_stack_bb ≥ 200, tags: DEEP_STACK)
- **예상 매칭 핸드 수**: 15-30개

**Query 11**: "turn decision big pot"
- **기대 결과**: 턴에서 결정한 큰 팟 (street: TURN, pot_bb ≥ 150)
- **예상 매칭 핸드 수**: 5-10개

**Query 12**: "button vs big blind"
- **기대 결과**: 버튼 vs 빅블라인드 (hero_position: BTN, villain_position: BB)
- **예상 매칭 핸드 수**: 8-15개

### Category 4: Emotional/Narrative Queries (감성/서사 중심)

**Query 13**: "sick call insane"
- **기대 결과**: 미친 콜 (tags: SICK_CALL, description에 "insane"/"sick")
- **예상 매칭 핸드 수**: 3-7개

**Query 14**: "bad beat cooler"
- **기대 결과**: 배드빗 쿨러 (tags: BAD_BEAT, COOLER)
- **예상 매칭 핸드 수**: 2-5개

**Query 15**: "tank long time river"
- **기대 결과**: 리버에서 오래 탱크 (street: RIVER, action_sequence에 "tank")
- **예상 매칭 핸드 수**: 5-10개

**Query 16**: "hero fold top pair"
- **기대 결과**: 탑페어 영웅적 폴드 (hand_type: HERO_FOLD, description에 "top pair")
- **예상 매칭 핸드 수**: 2-5개

### Category 5: Tournament-based Queries (토너먼트 중심)

**Query 17**: "wsop 2024 main event"
- **기대 결과**: WSOP 2024 메인 이벤트 핸드 (tournament_id: wsop_2024)
- **예상 매칭 핸드 수**: 10-20개

**Query 18**: "mpp high roller"
- **기대 결과**: MPP 하이롤러 핸드 (tournament_id: mpp_*)
- **예상 매칭 핸드 수**: 10-20개

**Query 19**: "hustler casino live"
- **기대 결과**: Hustler Casino Live 핸드 (tournament_id: hustler_casino_live_*)
- **예상 매칭 핸드 수**: 5-10개

**Query 20**: "triton poker series"
- **기대 결과**: Triton Poker 핸드 (tournament_id: triton_poker_*)
- **예상 매칭 핸드 수**: 5-10개

---

## 측정 프로세스

### 1단계: 테스트 실행
```bash
# FastAPI 서버 실행
cd backend
uvicorn main:app --reload

# 테스트 스크립트 실행
python test_search_accuracy.py
```

### 2단계: 자동 평가 (가능한 경우)
- JSON Schema 검증: hand_type, tags, street 등이 쿼리와 일치하는가?
- 예: "Phil Ivey bluff" → 결과 중 `hero_name: "Phil Ivey"` AND `hand_type: "BLUFF"` 개수

### 3단계: 수동 평가 (필요 시)
- Description 텍스트가 쿼리 의도와 일치하는가?
- 예: "triple barrel bluff" → description에 "three barrels" 또는 action_sequence 길이 10+ 확인

### 4단계: 결과 집계
```
Query 1: Phil Ivey bluff
  - Result 1: ✅ (Phil Ivey, BLUFF)
  - Result 2: ✅ (Phil Ivey, BLUFF)
  - Result 3: ❌ (Phil Ivey, HERO_CALL - 블러프 아님)
  - Result 4: ✅ (Phil Ivey, BLUFF)
  - Result 5: ✅ (Phil Ivey, BLUFF)
  → Precision@5 = 4/5 = 80%

전체 평균 Precision@5 = (Query 1~20 평균) ≥ 85%
```

---

## 예상 결과

### 합성 데이터 특성상 예상되는 정확도:

**높은 정확도 (90%+ 예상)**:
- Player-based queries (Query 1-4)
- Tournament-based queries (Query 17-20)
- 이유: 필드 매칭이 명확 (hero_name, tournament_id 등)

**중간 정확도 (80-90% 예상)**:
- Action-based queries (Query 5-8)
- Situation-based queries (Query 9-12)
- 이유: description 텍스트 검색 + 필드 필터 조합

**낮은 정확도 (70-80% 예상)**:
- Emotional/Narrative queries (Query 13-16)
- 이유: description 텍스트의 의미론적 이해 필요

**전체 평균**: 82-88% 예상 (목표 85% 달성 가능)

---

## 개선 방안 (PoC 후 Pilot에서 적용)

1. **실제 ATI 데이터 사용**:
   - 실제 핸드 설명의 다양성과 뉘앙스 반영
   - Edge case 검증 가능

2. **Hybrid Search 튜닝**:
   - BM25 가중치 조정 (현재 기본값: 0.5)
   - Vector Search 가중치 조정

3. **메타데이터 필드 확장**:
   - 추가 태그 (예: "THIN_VALUE", "BLOCKING_BET")
   - 더 세밀한 action_sequence 분류

4. **Relevance Feedback**:
   - 사용자가 검색 결과에 👍/👎 피드백
   - 피드백 기반 재훈련

---

## 테스트 자동화 스크립트 (예시)

```python
# test_search_accuracy.py
import requests
import json

TEST_QUERIES = [
    {
        "query": "Phil Ivey bluff",
        "expected_conditions": {
            "hero_name": "Phil Ivey",
            "hand_type": "BLUFF"
        }
    },
    # ... 나머지 19개 쿼리
]

def test_precision_at_5():
    results = []

    for test in TEST_QUERIES:
        response = requests.get(
            "http://localhost:8000/api/search",
            params={"q": test["query"], "limit": 5}
        )

        hands = response.json()["results"]
        relevant_count = 0

        for hand in hands:
            if matches_conditions(hand, test["expected_conditions"]):
                relevant_count += 1

        precision = relevant_count / 5
        results.append({
            "query": test["query"],
            "precision": precision,
            "relevant_count": relevant_count
        })

    avg_precision = sum(r["precision"] for r in results) / len(results)

    print(f"Average Precision@5: {avg_precision:.2%}")
    print(f"Success: {'✅' if avg_precision >= 0.85 else '❌'}")

    return results

def matches_conditions(hand, conditions):
    for field, expected_value in conditions.items():
        if hand.get(field) != expected_value:
            return False
    return True

if __name__ == "__main__":
    results = test_precision_at_5()

    # 결과 저장
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
```

---

**결론**: 합성 데이터로도 **82-88% 정확도 달성 예상**이므로, PoC 목표(85%)는 **충분히 검증 가능**합니다. 다만 실제 프로덕션 배포 전에는 ATI 실제 데이터로 재검증이 필수입니다.
