"""
UI 패턴 관리 시스템
UI 감지 로직을 체계적으로 저장하고 관리
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import numpy as np
from dataclasses import dataclass, asdict
import sqlite3

@dataclass
class UIPattern:
    """UI 패턴 데이터 구조"""
    pattern_id: str
    broadcaster: str
    ui_type: str  # 'stats', 'break', 'ad', 'tournament_info'
    features: Dict[str, float]
    timestamp_created: str
    confidence: float
    sample_count: int
    metadata: Dict

@dataclass
class FeatureSample:
    """개별 프레임 특징 샘플"""
    sample_id: str
    video_name: str
    timestamp: float
    features: Dict[str, float]
    is_ui: bool
    ui_type: Optional[str]
    confidence: float
    created_at: str

class UIPatternManager:
    """UI 패턴 저장 및 관리"""
    
    def __init__(self, data_dir: str = "ui_detection_data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "ui_patterns.db")
        self._init_directories()
        self._init_database()
        
    def _init_directories(self):
        """디렉토리 구조 초기화"""
        dirs = ['features', 'screenshots', 'models', 'patterns']
        for dir_name in dirs:
            os.makedirs(os.path.join(self.data_dir, dir_name), exist_ok=True)
    
    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # UI 패턴 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ui_patterns (
                pattern_id TEXT PRIMARY KEY,
                broadcaster TEXT,
                ui_type TEXT,
                features TEXT,
                confidence REAL,
                sample_count INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 특징 샘플 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_samples (
                sample_id TEXT PRIMARY KEY,
                video_name TEXT,
                timestamp REAL,
                features TEXT,
                is_ui INTEGER,
                ui_type TEXT,
                confidence REAL,
                created_at TEXT
            )
        ''')
        
        # 학습 히스토리 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_history (
                training_id TEXT PRIMARY KEY,
                model_name TEXT,
                accuracy REAL,
                sample_count INTEGER,
                feature_importance TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_feature_sample(self, video_name: str, timestamp: float, 
                          features: Dict, is_ui: bool, 
                          ui_type: Optional[str] = None) -> str:
        """특징 샘플 저장"""
        
        # 1. JSON 파일로 저장
        sample_id = f"{video_name}_{timestamp:.1f}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        sample = FeatureSample(
            sample_id=sample_id,
            video_name=video_name,
            timestamp=timestamp,
            features=features,
            is_ui=is_ui,
            ui_type=ui_type,
            confidence=features.get('ui_probability', 0.0),
            created_at=datetime.now().isoformat()
        )
        
        # JSON 파일 저장
        json_path = os.path.join(self.data_dir, 'features', f"{sample_id}.json")
        with open(json_path, 'w') as f:
            json.dump(asdict(sample), f, indent=2)
        
        # 2. 데이터베이스에도 저장
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feature_samples 
            (sample_id, video_name, timestamp, features, is_ui, ui_type, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sample.sample_id,
            sample.video_name,
            sample.timestamp,
            json.dumps(sample.features),
            1 if sample.is_ui else 0,
            sample.ui_type,
            sample.confidence,
            sample.created_at
        ))
        
        conn.commit()
        conn.close()
        
        return sample_id
    
    def create_ui_pattern(self, broadcaster: str, ui_type: str, 
                         samples: List[Dict]) -> UIPattern:
        """여러 샘플로부터 UI 패턴 생성"""
        
        # 평균 특징 계산
        avg_features = {}
        feature_keys = samples[0]['features'].keys()
        
        for key in feature_keys:
            values = [s['features'][key] for s in samples]
            avg_features[key] = float(np.mean(values))
            avg_features[f"{key}_std"] = float(np.std(values))
        
        # 패턴 ID 생성
        pattern_content = f"{broadcaster}_{ui_type}_{json.dumps(avg_features, sort_keys=True)}"
        pattern_id = hashlib.md5(pattern_content.encode()).hexdigest()[:12]
        
        pattern = UIPattern(
            pattern_id=pattern_id,
            broadcaster=broadcaster,
            ui_type=ui_type,
            features=avg_features,
            timestamp_created=datetime.now().isoformat(),
            confidence=float(np.mean([s.get('confidence', 0.8) for s in samples])),
            sample_count=len(samples),
            metadata={
                'sample_ids': [s.get('sample_id', '') for s in samples],
                'video_sources': list(set(s.get('video_name', '') for s in samples))
            }
        )
        
        # 저장
        self.save_ui_pattern(pattern)
        
        return pattern
    
    def save_ui_pattern(self, pattern: UIPattern):
        """UI 패턴 저장"""
        
        # 1. JSON 파일로 저장
        pattern_file = os.path.join(
            self.data_dir, 'patterns', 
            f"{pattern.broadcaster}_patterns.json"
        )
        
        # 기존 패턴 로드
        patterns = {}
        if os.path.exists(pattern_file):
            with open(pattern_file, 'r') as f:
                patterns = json.load(f)
        
        # 새 패턴 추가/업데이트
        patterns[pattern.pattern_id] = asdict(pattern)
        
        with open(pattern_file, 'w') as f:
            json.dump(patterns, f, indent=2)
        
        # 2. 데이터베이스에 저장
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ui_patterns
            (pattern_id, broadcaster, ui_type, features, confidence, 
             sample_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.pattern_id,
            pattern.broadcaster,
            pattern.ui_type,
            json.dumps(pattern.features),
            pattern.confidence,
            pattern.sample_count,
            pattern.timestamp_created,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def load_patterns_for_broadcaster(self, broadcaster: str) -> List[UIPattern]:
        """특정 방송사의 패턴 로드"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ui_patterns WHERE broadcaster = ?
        ''', (broadcaster,))
        
        patterns = []
        for row in cursor.fetchall():
            pattern = UIPattern(
                pattern_id=row[0],
                broadcaster=row[1],
                ui_type=row[2],
                features=json.loads(row[3]),
                confidence=row[4],
                sample_count=row[5],
                timestamp_created=row[6],
                metadata={}
            )
            patterns.append(pattern)
        
        conn.close()
        return patterns
    
    def match_pattern(self, features: Dict[str, float], 
                     threshold: float = 0.8) -> Optional[UIPattern]:
        """현재 특징과 가장 유사한 패턴 찾기"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ui_patterns')
        
        best_match = None
        best_similarity = 0
        
        for row in cursor.fetchall():
            pattern = UIPattern(
                pattern_id=row[0],
                broadcaster=row[1],
                ui_type=row[2],
                features=json.loads(row[3]),
                confidence=row[4],
                sample_count=row[5],
                timestamp_created=row[6],
                metadata={}
            )
            
            similarity = self._calculate_similarity(features, pattern.features)
            
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = pattern
        
        conn.close()
        return best_match
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """두 특징 벡터 간 유사도 계산"""
        common_keys = set(features1.keys()) & set(features2.keys())
        
        if not common_keys:
            return 0.0
        
        # 코사인 유사도
        vec1 = np.array([features1[k] for k in common_keys])
        vec2 = np.array([features2[k] for k in common_keys])
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def export_pattern_database(self, export_path: str):
        """전체 패턴 데이터베이스 내보내기"""
        export_data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'patterns': {},
            'statistics': {}
        }
        
        # 모든 패턴 로드
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT broadcaster FROM ui_patterns')
        broadcasters = [row[0] for row in cursor.fetchall()]
        
        for broadcaster in broadcasters:
            patterns = self.load_patterns_for_broadcaster(broadcaster)
            export_data['patterns'][broadcaster] = [
                asdict(p) for p in patterns
            ]
        
        # 통계 정보
        cursor.execute('SELECT COUNT(*) FROM feature_samples')
        total_samples = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ui_patterns')
        total_patterns = cursor.fetchone()[0]
        
        export_data['statistics'] = {
            'total_samples': total_samples,
            'total_patterns': total_patterns,
            'broadcasters': broadcasters
        }
        
        conn.close()
        
        # 저장
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def get_pattern_statistics(self) -> Dict:
        """패턴 데이터베이스 통계"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # 전체 통계
        cursor.execute('SELECT COUNT(*) FROM feature_samples')
        stats['total_samples'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ui_patterns')
        stats['total_patterns'] = cursor.fetchone()[0]
        
        # 방송사별 통계
        cursor.execute('''
            SELECT broadcaster, COUNT(*) as count 
            FROM ui_patterns 
            GROUP BY broadcaster
        ''')
        stats['patterns_by_broadcaster'] = dict(cursor.fetchall())
        
        # UI 타입별 통계
        cursor.execute('''
            SELECT ui_type, COUNT(*) as count 
            FROM ui_patterns 
            GROUP BY ui_type
        ''')
        stats['patterns_by_type'] = dict(cursor.fetchall())
        
        # 최근 학습 정보
        cursor.execute('''
            SELECT * FROM training_history 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        stats['recent_trainings'] = []
        for row in cursor.fetchall():
            stats['recent_trainings'].append({
                'training_id': row[0],
                'model_name': row[1],
                'accuracy': row[2],
                'sample_count': row[3],
                'created_at': row[5]
            })
        
        conn.close()
        return stats