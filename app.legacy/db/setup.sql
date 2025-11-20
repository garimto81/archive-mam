-- ==================================================
-- 포커 아카이브 검색 시스템 - PostgreSQL 스키마
-- pgvector + pgvectorscale 기반 하이브리드 검색
-- ==================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS vectorscale;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Trigram for fuzzy search

-- ==================================================
-- 1. Hands Table (핵심 검색 대상)
-- ==================================================
CREATE TABLE hands (
    id TEXT PRIMARY KEY,
    tournament_id TEXT NOT NULL,
    hand_number INTEGER NOT NULL,

    -- 시간 정보
    timestamp TIMESTAMPTZ NOT NULL,
    duration_seconds INTEGER,

    -- 핸드 정보
    street TEXT,  -- PREFLOP, FLOP, TURN, RIVER
    pot_bb FLOAT,
    hero_position TEXT,
    villain_position TEXT,

    -- 플레이어 정보
    hero_name TEXT,
    villain_name TEXT,
    hero_stack_bb FLOAT,
    villain_stack_bb FLOAT,

    -- 액션 정보
    action_sequence TEXT[],  -- ['RAISE', 'CALL', 'BET', ...]
    hero_action TEXT,
    result TEXT,  -- WIN, LOSE, SPLIT

    -- 태그 & 분류
    tags TEXT[],  -- ['BLUFF', 'HERO_CALL', 'BAD_BEAT', ...]
    hand_type TEXT,  -- ALL_IN, BIG_POT, RIVER_DECISION 등

    -- 자연어 설명 (ATI 분석 결과)
    description TEXT,
    language_tokens tsvector,  -- Full-text search를 위한 토큰

    -- 멀티모달 임베딩 (voyage-multimodal-3 또는 CLIP)
    embedding vector(1024),  -- 텍스트+영상 통합 벡터

    -- 영상 메타데이터
    video_file_path TEXT,
    video_start_time FLOAT,
    video_end_time FLOAT,
    thumbnail_url TEXT,

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 인덱스
    CONSTRAINT valid_pot CHECK (pot_bb >= 0),
    CONSTRAINT valid_duration CHECK (duration_seconds > 0)
);

-- ==================================================
-- 2. Tournaments Table
-- ==================================================
CREATE TABLE tournaments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    event_type TEXT,  -- WSOP, MPP, APL
    start_date DATE,
    end_date DATE,
    location TEXT,
    buy_in INTEGER,
    total_entries INTEGER,

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================================================
-- 3. Players Table
-- ==================================================
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    nickname TEXT[],  -- ['정글맨', 'Junglemann', ...]
    country TEXT,

    -- 통계
    total_hands INTEGER DEFAULT 0,
    famous_hands TEXT[],  -- hand_id references

    -- 임베딩 (플레이어 스타일 벡터)
    player_embedding vector(512),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================================================
-- 4. Video Files Table
-- ==================================================
CREATE TABLE video_files (
    id SERIAL PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    tournament_id TEXT REFERENCES tournaments(id),

    -- 파일 정보
    file_size_bytes BIGINT,
    duration_seconds INTEGER,
    resolution TEXT,  -- 1080p, 720p, etc.
    codec TEXT,

    -- 처리 상태
    processing_status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    indexed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================================================
-- 5. Search Queries Log (검색 분석용)
-- ==================================================
CREATE TABLE search_queries (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_embedding vector(1024),

    -- 검색 파라미터
    filters JSONB,
    search_method TEXT,  -- hybrid, vector_only, bm25_only

    -- 결과
    result_count INTEGER,
    top_result_id TEXT,
    avg_score FLOAT,

    -- 사용자 피드백
    clicked_result_id TEXT,
    feedback_score INTEGER,  -- 1-5 rating

    -- 성능 메트릭
    latency_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================================================
-- Indexes
-- ==================================================

-- 1. Vector Search (HNSW)
CREATE INDEX hands_embedding_idx ON hands
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 2. Full-text Search (GIN)
CREATE INDEX hands_language_tokens_idx ON hands
USING gin(language_tokens);

-- 3. Trigram for fuzzy player search
CREATE INDEX players_name_trgm_idx ON players
USING gin(name gin_trgm_ops);

-- 4. Common queries
CREATE INDEX hands_tournament_idx ON hands(tournament_id);
CREATE INDEX hands_timestamp_idx ON hands(timestamp DESC);
CREATE INDEX hands_tags_idx ON hands USING gin(tags);
CREATE INDEX hands_pot_bb_idx ON hands(pot_bb DESC);

-- 5. Foreign keys
CREATE INDEX video_files_tournament_idx ON video_files(tournament_id);

-- ==================================================
-- Functions & Triggers
-- ==================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_hands_updated_at BEFORE UPDATE ON hands
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tournaments_updated_at BEFORE UPDATE ON tournaments
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update language_tokens from description
CREATE OR REPLACE FUNCTION update_language_tokens()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.description IS NOT NULL THEN
        -- Korean + English 처리
        NEW.language_tokens = to_tsvector('simple', NEW.description);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_hands_language_tokens
BEFORE INSERT OR UPDATE OF description ON hands
FOR EACH ROW EXECUTE FUNCTION update_language_tokens();

-- ==================================================
-- Sample Data Insert (테스트용)
-- ==================================================

-- Sample Tournament
INSERT INTO tournaments (id, name, event_type, start_date, buy_in, total_entries)
VALUES
    ('wsop_2024_main', 'WSOP 2024 Main Event', 'WSOP', '2024-07-01', 10000, 8773),
    ('mpp_2024_s1', 'Million Poker Pot S1', 'MPP', '2024-03-15', 5000, 256)
ON CONFLICT DO NOTHING;

-- Sample Players
INSERT INTO players (name, nickname, country)
VALUES
    ('정글맨', ARRAY['Junglemann', '정글'], 'KR'),
    ('헬뮤스', ARRAY['Hellmuth', 'Phil'], 'US'),
    ('아이비', ARRAY['Ivey', 'Phil Ivey'], 'US')
ON CONFLICT DO NOTHING;

-- ==================================================
-- Views (자주 사용하는 쿼리)
-- ==================================================

-- 최근 핸드 뷰
CREATE OR REPLACE VIEW recent_hands AS
SELECT
    h.id,
    h.hand_number,
    h.hero_name,
    h.villain_name,
    h.pot_bb,
    h.result,
    h.tags,
    h.description,
    t.name as tournament_name,
    h.timestamp
FROM hands h
LEFT JOIN tournaments t ON h.tournament_id = t.id
ORDER BY h.timestamp DESC;

-- 인기 핸드 뷰 (검색 횟수 기준)
CREATE OR REPLACE VIEW popular_hands AS
SELECT
    h.id,
    h.description,
    COUNT(sq.id) as search_count,
    h.tags,
    h.hero_name,
    h.pot_bb
FROM hands h
LEFT JOIN search_queries sq ON sq.top_result_id = h.id
GROUP BY h.id
ORDER BY search_count DESC;

-- ==================================================
-- Comments
-- ==================================================

COMMENT ON TABLE hands IS '포커 핸드 메타데이터 및 벡터 임베딩';
COMMENT ON COLUMN hands.embedding IS 'voyage-multimodal-3 또는 CLIP 임베딩 (1024차원)';
COMMENT ON COLUMN hands.language_tokens IS 'PostgreSQL Full-text search를 위한 tsvector';
COMMENT ON COLUMN hands.tags IS 'BLUFF, HERO_CALL, BAD_BEAT 등 분류 태그';

COMMENT ON TABLE search_queries IS '검색 쿼리 로그 (분석 및 개선용)';
COMMENT ON INDEX hands_embedding_idx IS 'HNSW 벡터 인덱스 (코사인 유사도)';
