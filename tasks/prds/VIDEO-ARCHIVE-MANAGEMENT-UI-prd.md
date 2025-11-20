# PRD: Video Archive Management UI with Status Tracking

**Version**: 1.0.0
**Date**: 2025-01-20
**Status**: Draft
**Priority**: High
**Assignee**: Development Team

---

## 1. Executive Summary

포커 핸드 비디오 아카이브를 효과적으로 관리하고 검색할 수 있는 통합 UI 시스템을 구축합니다. 사용자는 어떤 비디오가 분석되었는지, 어떻게 검색되는지 명확하게 파악할 수 있어야 합니다.

### Problem Statement
현재 시스템은:
- ❌ 비디오 분석 상태를 시각적으로 확인하기 어려움
- ❌ 아카이브 전체 구조를 한눈에 파악하기 어려움
- ❌ 검색 결과와 원본 아카이브 간 연결성 부족
- ❌ 필터링 및 정렬 옵션 제한적

### Solution
GitHub 오픈소스 솔루션들의 장점을 통합한 Video Archive Management UI:
1. **MediaFlow** 참고: 실시간 상태 추적 UI 패턴
2. **React-Media-Library** 참고: WordPress 스타일 그리드 레이아웃
3. **video-library** 참고: TypeScript 기반 검색/필터 로직
4. **react-github-media-library** 참고: 고급 검색 및 카테고리 필터

### Success Metrics
- 비디오 분석 상태 식별 시간: **5초 이내**
- 특정 핸드 검색 시간: **10초 이내**
- 필터 적용 반응 시간: **< 500ms**
- 사용자 만족도: **≥ 4.5/5.0**

---

## 2. Background & Context

### Current State (As-Is)
```
SearchResults 컴포넌트
├── ResultsGrid (카드 뷰)
├── ArchiveTreeView (계층 구조)
└── Pagination

제한사항:
- 상태 추적 없음 (분석됨/분석 안 됨)
- 고급 필터 부족 (포지션, 액션 타입 등)
- 정렬 옵션 제한적
- 대시보드/통계 뷰 없음
```

### Desired State (To-Be)
```
Video Archive Management Dashboard
├── Status Overview (분석 상태 요약)
├── Advanced Filters (다층 필터)
├── Multiple View Modes
│   ├── Grid View (현재)
│   ├── List View (상세)
│   ├── Timeline View (시간순)
│   └── Tree View (계층)
├── Search Enhancement
│   ├── Autocomplete
│   ├── Recent Searches
│   └── Saved Filters
└── Bulk Actions (일괄 작업)
```

### User Personas

**Persona 1: 프로 코치 (Advanced User)**
- **Goal**: 특정 플레이어의 특정 상황 핸드만 빠르게 찾기
- **Pain Point**: 여러 필터를 조합해야 할 때 불편함
- **Need**: 저장된 필터 프리셋, 고급 검색

**Persona 2: 일반 플레이어 (Casual User)**
- **Goal**: 흥미로운 핸드 브라우징
- **Pain Point**: 어떤 비디오가 분석되었는지 모름
- **Need**: 시각적 상태 표시, 추천 핸드

**Persona 3: 콘텐츠 관리자 (Admin)**
- **Goal**: 아카이브 전체 상태 모니터링
- **Pain Point**: 분석 진행률 파악 어려움
- **Need**: 대시보드, 통계, 일괄 작업

---

## 3. Requirements

### 3.1 Functional Requirements

#### FR-1: Status Tracking System
**Priority**: P0 (Must Have)

**Description**: 각 비디오의 분석 상태를 실시간으로 표시

**Acceptance Criteria**:
- [ ] 상태 배지 표시 (분석됨, 분석 중, 대기 중, 실패)
- [ ] 프로그레스 바 (분석 진행률 %)
- [ ] 타임스탬프 (최근 분석 시간)
- [ ] 에러 메시지 (실패 시)

**UI Design** (MediaFlow 참고):
```tsx
<StatusBadge status={hand.analysisStatus}>
  {status === 'completed' && <CheckCircle />}
  {status === 'processing' && <Loader />}
  {status === 'failed' && <XCircle />}
  {status === 'pending' && <Clock />}
</StatusBadge>

<ProgressBar
  value={hand.analysisProgress}
  max={100}
  variant={getVariant(status)}
/>
```

#### FR-2: Advanced Filter System
**Priority**: P0 (Must Have)

**Description**: 다층 필터링 시스템으로 정확한 핸드 검색

**Acceptance Criteria**:
- [ ] 기본 필터: 플레이어, 토너먼트, 스트리트, 팟 사이즈
- [ ] 고급 필터: 포지션, 액션 타입, 결과, 태그
- [ ] 필터 조합 (AND/OR 로직)
- [ ] 필터 프리셋 저장/불러오기
- [ ] 필터 초기화 버튼

**UI Design** (react-github-media-library 참고):
```tsx
<FilterPanel>
  <FilterGroup label="기본 필터">
    <PlayerFilter />
    <TournamentFilter />
    <StreetFilter />
    <PotSizeFilter />
  </FilterGroup>

  <FilterGroup label="고급 필터" collapsible>
    <PositionFilter />
    <ActionTypeFilter />
    <ResultFilter />
    <TagFilter />
  </FilterGroup>

  <FilterActions>
    <SaveFilterPreset />
    <LoadFilterPreset />
    <ResetFilters />
  </FilterActions>
</FilterPanel>
```

#### FR-3: Multiple View Modes
**Priority**: P1 (Should Have)

**Description**: 사용자가 선호하는 방식으로 아카이브 탐색

**Acceptance Criteria**:
- [ ] Grid View (현재): 썸네일 카드 그리드
- [ ] List View: 상세 정보 리스트
- [ ] Timeline View: 시간순 타임라인
- [ ] Tree View (현재): 계층 구조

**UI Design** (React-Media-Library 참고):
```tsx
<ViewModeSwitcher>
  <ViewModeButton mode="grid" icon={<Grid />} />
  <ViewModeButton mode="list" icon={<List />} />
  <ViewModeButton mode="timeline" icon={<Calendar />} />
  <ViewModeButton mode="tree" icon={<Folder />} />
</ViewModeSwitcher>

{viewMode === 'grid' && <GridView results={results} />}
{viewMode === 'list' && <ListView results={results} />}
{viewMode === 'timeline' && <TimelineView results={results} />}
{viewMode === 'tree' && <TreeView results={results} />}
```

#### FR-4: Search Enhancement
**Priority**: P1 (Should Have)

**Description**: 검색 경험 개선

**Acceptance Criteria**:
- [ ] 자동완성 (플레이어, 토너먼트 이름)
- [ ] 최근 검색어 (최대 10개)
- [ ] 검색어 하이라이트 (결과에서)
- [ ] 오타 교정 제안

#### FR-5: Statistics Dashboard
**Priority**: P2 (Nice to Have)

**Description**: 아카이브 전체 통계 대시보드

**Acceptance Criteria**:
- [ ] 총 비디오 수, 분석 완료율
- [ ] 플레이어별 핸드 수
- [ ] 토너먼트별 핸드 수
- [ ] 최근 업로드/분석 활동

#### FR-6: Bulk Actions
**Priority**: P2 (Nice to Have)

**Description**: 일괄 작업 기능 (관리자용)

**Acceptance Criteria**:
- [ ] 다중 선택 (체크박스)
- [ ] 일괄 태그 추가/제거
- [ ] 일괄 재분석 요청
- [ ] 일괄 다운로드

### 3.2 Non-Functional Requirements

#### NFR-1: Performance
- 필터 적용 반응 시간: **< 500ms**
- 뷰 모드 전환 시간: **< 300ms**
- 검색 자동완성 지연: **< 200ms**
- 대시보드 로딩 시간: **< 2s**

#### NFR-2: Accessibility
- WCAG 2.1 AA 준수
- 키보드 네비게이션 완전 지원
- 스크린 리더 호환

#### NFR-3: Responsiveness
- 모바일 (< 768px): 단일 컬럼, 간소화된 필터
- 태블릿 (768px - 1024px): 2컬럼
- 데스크톱 (≥ 1024px): 3컬럼 레이아웃

#### NFR-4: Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## 4. Technical Architecture

### 4.1 Component Structure

```
src/components/archive/
├── ArchiveManagementDashboard.tsx      # 메인 컨테이너
│   ├── StatusOverview.tsx              # 상태 요약 (FR-5)
│   ├── FilterPanel.tsx                 # 필터 패널 (FR-2)
│   ├── ViewModeSwitcher.tsx            # 뷰 모드 선택 (FR-3)
│   ├── SearchBar.tsx                   # 검색 바 (FR-4)
│   └── ResultsContainer.tsx            # 결과 컨테이너
│       ├── GridView.tsx                # 그리드 뷰 (기존)
│       ├── ListView.tsx                # 리스트 뷰 (신규)
│       ├── TimelineView.tsx            # 타임라인 뷰 (신규)
│       └── TreeView.tsx                # 트리 뷰 (기존)
│
├── status/
│   ├── StatusBadge.tsx                 # 상태 배지 (FR-1)
│   ├── ProgressBar.tsx                 # 프로그레스 바 (FR-1)
│   └── StatusFilter.tsx                # 상태 필터
│
├── filters/
│   ├── PlayerFilter.tsx
│   ├── TournamentFilter.tsx
│   ├── PositionFilter.tsx
│   ├── ActionTypeFilter.tsx
│   ├── FilterPreset.tsx                # 필터 프리셋
│   └── FilterCombinator.tsx            # AND/OR 로직
│
└── bulk/
    ├── BulkSelectCheckbox.tsx
    ├── BulkActionsToolbar.tsx
    └── BulkActionModal.tsx
```

### 4.2 Data Model Extensions

```typescript
// Extend SearchResultItem
export interface SearchResultItem {
  // ... 기존 필드

  // 새로운 필드 (FR-1: Status Tracking)
  readonly analysisStatus: 'completed' | 'processing' | 'pending' | 'failed';
  readonly analysisProgress?: number; // 0-100
  readonly analyzedAt?: string; // ISO timestamp
  readonly analysisError?: string;

  // 새로운 필드 (FR-2: Advanced Filters)
  readonly actionSequence?: string[]; // ["raise", "call", "bet"]
  readonly finalResult?: 'win' | 'loss' | 'chop';
  readonly positionDetail?: {
    hero: string;
    villain: string;
    effective: string; // "IP", "OOP"
  };
}

// 새로운 타입 (FR-2: Filter Presets)
export interface FilterPreset {
  readonly id: string;
  readonly name: string;
  readonly filters: SearchFilters;
  readonly createdAt: string;
  readonly userId: string;
}

// 새로운 타입 (FR-3: View Mode)
export type ViewMode = 'grid' | 'list' | 'timeline' | 'tree';

// 새로운 타입 (FR-5: Statistics)
export interface ArchiveStatistics {
  readonly totalHands: number;
  readonly analyzedHands: number;
  readonly analysisCompletionRate: number; // 0-100
  readonly byPlayer: Map<string, number>;
  readonly byTournament: Map<string, number>;
  readonly recentActivity: Activity[];
}

export interface Activity {
  readonly id: string;
  readonly type: 'upload' | 'analyze' | 'edit';
  readonly handId: string;
  readonly timestamp: string;
  readonly userId: string;
}
```

### 4.3 State Management

```typescript
// Zustand store for archive management
interface ArchiveStore {
  // View state
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;

  // Filter state
  filters: SearchFilters;
  setFilters: (filters: SearchFilters) => void;
  resetFilters: () => void;

  // Filter presets
  filterPresets: FilterPreset[];
  saveFilterPreset: (name: string) => void;
  loadFilterPreset: (id: string) => void;
  deleteFilterPreset: (id: string) => void;

  // Bulk selection
  selectedHandIds: Set<string>;
  toggleHandSelection: (handId: string) => void;
  selectAll: () => void;
  clearSelection: () => void;

  // Statistics
  statistics: ArchiveStatistics | null;
  fetchStatistics: () => Promise<void>;
}
```

### 4.4 API Extensions

```typescript
// New API endpoints

// GET /api/archive/statistics
// Returns: ArchiveStatistics

// GET /api/archive/filter-presets
// Returns: FilterPreset[]

// POST /api/archive/filter-presets
// Body: { name: string, filters: SearchFilters }
// Returns: FilterPreset

// DELETE /api/archive/filter-presets/:id
// Returns: { success: boolean }

// POST /api/archive/bulk-action
// Body: { handIds: string[], action: 'tag' | 'reanalyze' | 'download', payload: any }
// Returns: { success: boolean, results: any[] }
```

---

## 5. Implementation Plan

### Phase 0: Planning (Current)
- [x] PRD 작성
- [ ] Task List 생성
- [ ] 디자인 시안 (Figma/Mockup)

### Phase 1: Core Features (Week 1-2)
- [ ] **Task 1.1**: StatusBadge 컴포넌트 구현
- [ ] **Task 1.2**: FilterPanel 컴포넌트 구현
- [ ] **Task 1.3**: ListView 컴포넌트 구현
- [ ] **Task 1.4**: TimelineView 컴포넌트 구현
- [ ] **Task 1.5**: ViewModeSwitcher 구현
- [ ] **Task 1.6**: ArchiveManagementDashboard 통합

### Phase 2: Testing (Week 2-3)
- [ ] **Task 2.1**: Unit Tests (각 컴포넌트)
- [ ] **Task 2.2**: Integration Tests (필터 + 뷰 모드)
- [ ] **Task 2.3**: E2E Tests (사용자 시나리오)
- [ ] **Task 2.4**: Performance Testing (필터 응답 시간)
- [ ] **Task 2.5**: Accessibility Audit (WCAG)

### Phase 3: Advanced Features (Week 3-4)
- [ ] **Task 3.1**: FilterPreset 기능 구현
- [ ] **Task 3.2**: Statistics Dashboard 구현
- [ ] **Task 3.3**: Bulk Actions 구현
- [ ] **Task 3.4**: Search Enhancement (자동완성)

### Phase 4: Polish & Deployment (Week 4-5)
- [ ] **Task 4.1**: UI/UX 개선 (피드백 반영)
- [ ] **Task 4.2**: 모바일 최적화
- [ ] **Task 4.3**: 문서화 (사용자 가이드)
- [ ] **Task 4.4**: Production 배포

---

## 6. Design Mockups

### 6.1 Main Dashboard (Grid View)

```
┌─────────────────────────────────────────────────────────────────┐
│ 📁 Archive Management Dashboard                    [Profile] [⚙] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📊 Statistics                                                    │
│  ┌──────────┬──────────┬──────────┬──────────┐                   │
│  │ 총 핸드   │ 분석완료  │ 분석 중  │ 대기 중  │                   │
│  │  1,247   │  892     │  155     │  200     │                   │
│  │          │  71.5%   │          │          │                   │
│  └──────────┴──────────┴──────────┴──────────┘                   │
│                                                                   │
│  🔍 Search: [________________________]  🔎                        │
│      Recent: "Phil Ivey bluff" | "WSOP 2023"                     │
│                                                                   │
│  🎛️ Filters: ┌────────────────────────────────────┐              │
│             │ Player: [All ▼]  Tournament: [All ▼]│              │
│             │ Street: [All ▼]  Status: [All ▼]    │              │
│             │ [+ Advanced Filters]                │              │
│             └────────────────────────────────────┘              │
│                                                                   │
│  👁️ View: [📊Grid] [📋List] [📅Timeline] [🌳Tree]                 │
│                                                                   │
│  Results: 892 hands                    Sort: [Latest ▼] [⚙️]      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │ │
│  │ │[✓]      │ │[✓]      │ │[⏳]     │ │[❌]     │            │ │
│  │ │ Video 1 │ │ Video 2 │ │ Video 3 │ │ Video 4 │            │ │
│  │ │ ███████ │ │ ███████ │ │ ███░░░░ │ │ ███████ │            │ │
│  │ │ Hero    │ │ Hero    │ │ Hero    │ │ Hero    │            │ │
│  │ │ 100BB   │ │ 250BB   │ │ 75BB    │ │ 180BB   │            │ │
│  │ │ ✅100%  │ │ ✅100%  │ │ ⏳45%   │ │ ❌Error │            │ │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │ │
│  │                                                               │ │
│  │ [Load More...]                                                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Bulk Actions: [🏷️ Add Tags] [🔄 Reanalyze] [⬇️ Download]         │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 List View

```
┌─────────────────────────────────────────────────────────────────┐
│ Results: 892 hands                    Sort: [Latest ▼]           │
├─────────────────────────────────────────────────────────────────┤
│ [☑] Hand #001 | WSOP 2023 Main Event                          │
│     👤 Phil Ivey vs Tom Dwan | 🃏 River | 💰 250BB | ✅ 100%     │
│     📅 2023-07-15 14:23 | 🏷️ BLUFF, VALUE                       │
│     ───────────────────────────────────────────────────────────  │
│ [☑] Hand #002 | WSOP 2023 Main Event                          │
│     👤 Daniel Negreanu vs Phil Hellmuth | 🃏 Turn | 💰 180BB    │
│     📅 2023-07-15 15:10 | 🏷️ CALL, FOLD | ✅ 100%               │
│     ───────────────────────────────────────────────────────────  │
│ [☐] Hand #003 | WPT Alpha8                                     │
│     👤 Tony G vs Viktor Blom | 🃏 Flop | 💰 75BB | ⏳ 45%        │
│     📅 2023-08-20 10:05 | 🏷️ RAISE, RERAISE                     │
│     ───────────────────────────────────────────────────────────  │
│ [☐] Hand #004 | EPT Barcelona                                  │
│     👤 Adrian Mateos vs Steve O'Dwyer | 🃏 Preflop | 💰 320BB   │
│     📅 2023-09-01 16:42 | 🏷️ 3BET, 4BET | ❌ Analysis Failed    │
│     ───────────────────────────────────────────────────────────  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Timeline View

```
┌─────────────────────────────────────────────────────────────────┐
│ 2023                                                             │
│ ├─ November ─────────────────────────────────────────────────── │
│ │  ├─ 11/20 | Hand #123 | WSOP Europe | ✅                      │
│ │  ├─ 11/18 | Hand #122 | WSOP Europe | ✅                      │
│ │  └─ 11/15 | Hand #121 | WSOP Europe | ⏳                      │
│ ├─ October ──────────────────────────────────────────────────── │
│ │  ├─ 10/25 | Hand #120 | WPT Alpha8 | ✅                       │
│ │  ├─ 10/20 | Hand #119 | WPT Alpha8 | ✅                       │
│ │  └─ 10/15 | Hand #118 | WPT Alpha8 | ❌                       │
│ ├─ September ────────────────────────────────────────────────── │
│ │  ├─ 09/30 | Hand #117 | EPT Barcelona | ✅                    │
│ │  └─ 09/25 | Hand #116 | EPT Barcelona | ✅                    │
│ └─ August ───────────────────────────────────────────────────── │
│    ├─ 08/28 | Hand #115 | EPT Monte Carlo | ⏳                  │
│    └─ 08/20 | Hand #114 | EPT Monte Carlo | ✅                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Integration with Existing Code

### 7.1 참고할 오픈소스 코드

#### MediaFlow (상태 추적)
```typescript
// Reference: pointedsec/MediaFlow
// File: frontend/components/StatusBadge.tsx

// 적용할 패턴:
interface VideoStatus {
  status: 'completed' | 'processing' | 'pending' | 'failed';
  progress: number;
  error?: string;
}

// 컴포넌트 구조:
<StatusBadge status={video.status}>
  <Icon status={video.status} />
  <Label>{statusText}</Label>
  {video.progress && <ProgressBar value={video.progress} />}
</StatusBadge>
```

#### React-Media-Library (그리드 레이아웃)
```typescript
// Reference: Richard1320/React-Media-Library
// File: src/components/MediaLibrary.tsx

// 적용할 패턴:
const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

<ViewSwitcher>
  <Button onClick={() => setViewMode('grid')}>Grid</Button>
  <Button onClick={() => setViewMode('list')}>List</Button>
</ViewSwitcher>

{viewMode === 'grid' && <GridView items={items} />}
{viewMode === 'list' && <ListView items={items} />}
```

#### video-library (검색/필터)
```typescript
// Reference: ArjunGTX/video-library
// File: src/components/VideoLibrary.tsx

// 적용할 패턴:
const [searchTerm, setSearchTerm] = useState('');
const [categoryFilter, setCategoryFilter] = useState('all');
const [sortBy, setSortBy] = useState<'latest' | 'oldest'>('latest');

const filteredVideos = useMemo(() => {
  return videos
    .filter(v => v.title.includes(searchTerm))
    .filter(v => categoryFilter === 'all' || v.category === categoryFilter)
    .sort((a, b) => sortBy === 'latest'
      ? b.timestamp - a.timestamp
      : a.timestamp - b.timestamp
    );
}, [videos, searchTerm, categoryFilter, sortBy]);
```

#### react-github-media-library (고급 검색)
```typescript
// Reference: ivenms/react-github-media-library
// File: src/components/SearchAndFilter.tsx

// 적용할 패턴:
<FilterPanel>
  <SearchInput
    placeholder="Search media..."
    onChange={handleSearch}
  />
  <CategoryFilter
    categories={categories}
    onChange={handleCategoryChange}
  />
  <TagFilter
    tags={tags}
    onChange={handleTagChange}
  />
</FilterPanel>
```

### 7.2 기존 컴포넌트 수정

#### SearchResults.tsx
```typescript
// Before: 단순 그리드 뷰
<ResultsGrid results={results} />

// After: 뷰 모드 지원
<ArchiveManagementDashboard
  results={results}
  defaultViewMode="grid"
  showStatistics={true}
  showFilters={true}
  showBulkActions={user.isAdmin}
/>
```

#### HandCard.tsx
```typescript
// Before: 상태 표시 없음
<Card>
  <Thumbnail />
  <Title />
  <Metadata />
</Card>

// After: 상태 배지 추가
<Card>
  <StatusBadge status={hand.analysisStatus} progress={hand.analysisProgress} />
  <Thumbnail />
  <Title />
  <Metadata />
  {hand.analysisError && <ErrorTooltip error={hand.analysisError} />}
</Card>
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```typescript
// StatusBadge.test.tsx
describe('StatusBadge', () => {
  it('renders completed status correctly', () => {
    render(<StatusBadge status="completed" progress={100} />);
    expect(screen.getByTestId('check-icon')).toBeInTheDocument();
  });

  it('renders processing status with progress bar', () => {
    render(<StatusBadge status="processing" progress={45} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '45');
  });

  it('renders error status with error message', () => {
    render(<StatusBadge status="failed" error="Analysis timeout" />);
    expect(screen.getByText(/Analysis timeout/i)).toBeInTheDocument();
  });
});

// FilterPanel.test.tsx
describe('FilterPanel', () => {
  it('applies multiple filters correctly', async () => {
    const onFilterChange = jest.fn();
    render(<FilterPanel onFilterChange={onFilterChange} />);

    await userEvent.selectOptions(screen.getByLabelText(/Player/i), 'Phil Ivey');
    await userEvent.selectOptions(screen.getByLabelText(/Street/i), 'River');

    expect(onFilterChange).toHaveBeenCalledWith({
      player: 'Phil Ivey',
      street: 'River'
    });
  });

  it('saves and loads filter presets', async () => {
    render(<FilterPanel />);

    // Set filters
    await userEvent.selectOptions(screen.getByLabelText(/Player/i), 'Phil Ivey');
    await userEvent.click(screen.getByText(/Save Preset/i));

    // Load preset
    await userEvent.selectOptions(screen.getByLabelText(/Load Preset/i), 'Preset 1');

    expect(screen.getByLabelText(/Player/i)).toHaveValue('Phil Ivey');
  });
});
```

### 8.2 Integration Tests

```typescript
// ArchiveManagementDashboard.test.tsx
describe('ArchiveManagementDashboard Integration', () => {
  it('changes view mode and displays correctly', async () => {
    render(<ArchiveManagementDashboard results={mockResults} />);

    // Default grid view
    expect(screen.getAllByTestId('grid-item')).toHaveLength(20);

    // Switch to list view
    await userEvent.click(screen.getByLabelText(/List View/i));
    expect(screen.getAllByTestId('list-item')).toHaveLength(20);

    // Switch to timeline view
    await userEvent.click(screen.getByLabelText(/Timeline View/i));
    expect(screen.getByTestId('timeline-container')).toBeInTheDocument();
  });

  it('filters results and updates statistics', async () => {
    render(<ArchiveManagementDashboard results={mockResults} />);

    // Initial stats
    expect(screen.getByText(/Total: 1247/i)).toBeInTheDocument();

    // Apply filter
    await userEvent.selectOptions(screen.getByLabelText(/Status/i), 'completed');

    // Updated stats
    expect(screen.getByText(/Total: 892/i)).toBeInTheDocument();
  });
});
```

### 8.3 E2E Tests (Playwright)

```typescript
// archive-management.spec.ts
test.describe('Archive Management Dashboard', () => {
  test('user can search and filter hands', async ({ page }) => {
    await page.goto('/archive');

    // Enter search term
    await page.fill('[placeholder*="Search"]', 'Phil Ivey bluff');
    await page.waitForTimeout(500);

    // Apply filters
    await page.selectOption('[aria-label="Player"]', 'Phil Ivey');
    await page.selectOption('[aria-label="Street"]', 'River');

    // Verify results
    const results = await page.locator('[data-testid="hand-card"]').count();
    expect(results).toBeGreaterThan(0);

    // Verify all results contain "Phil Ivey" and "River"
    const cards = await page.locator('[data-testid="hand-card"]').all();
    for (const card of cards) {
      await expect(card).toContainText('Phil Ivey');
      await expect(card).toContainText('River');
    }
  });

  test('admin can perform bulk actions', async ({ page }) => {
    await page.goto('/archive');
    await page.evaluate(() => localStorage.setItem('user', JSON.stringify({ role: 'admin' })));

    // Select multiple hands
    await page.check('[data-testid="hand-card-1"] input[type="checkbox"]');
    await page.check('[data-testid="hand-card-2"] input[type="checkbox"]');
    await page.check('[data-testid="hand-card-3"] input[type="checkbox"]');

    // Perform bulk tag action
    await page.click('[aria-label="Bulk Actions"]');
    await page.click('text=Add Tags');
    await page.fill('[placeholder*="Enter tags"]', 'BLUFF, HERO_CALL');
    await page.click('button:has-text("Apply")');

    // Verify tags were added
    await expect(page.locator('[data-testid="hand-card-1"]')).toContainText('BLUFF');
    await expect(page.locator('[data-testid="hand-card-2"]')).toContainText('BLUFF');
  });

  test('statistics dashboard updates in real-time', async ({ page }) => {
    await page.goto('/archive');

    // Check initial statistics
    const totalHandsInitial = await page.textContent('[data-testid="total-hands"]');

    // Upload new hand (mock)
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('hand-uploaded', {
        detail: { handId: 'new-hand-123' }
      }));
    });

    // Wait for statistics to update
    await page.waitForTimeout(1000);

    // Verify statistics updated
    const totalHandsFinal = await page.textContent('[data-testid="total-hands"]');
    expect(parseInt(totalHandsFinal!)).toBeGreaterThan(parseInt(totalHandsInitial!));
  });
});
```

### 8.4 Performance Tests

```typescript
// performance.test.ts
describe('Performance Tests', () => {
  it('filter application responds within 500ms', async () => {
    const { rerender } = render(<FilterPanel onFilterChange={jest.fn()} />);

    const startTime = performance.now();

    // Apply filter
    await userEvent.selectOptions(screen.getByLabelText(/Player/i), 'Phil Ivey');

    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(duration).toBeLessThan(500);
  });

  it('view mode switch responds within 300ms', async () => {
    const { rerender } = render(<ArchiveManagementDashboard results={mockResults} />);

    const startTime = performance.now();

    // Switch view mode
    await userEvent.click(screen.getByLabelText(/List View/i));

    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(duration).toBeLessThan(300);
  });

  it('handles 1000+ items without performance degradation', async () => {
    const largeDataset = generateMockResults(1000);

    const startTime = performance.now();
    render(<ArchiveManagementDashboard results={largeDataset} />);
    const endTime = performance.now();

    const renderTime = endTime - startTime;
    expect(renderTime).toBeLessThan(2000); // < 2s for 1000 items
  });
});
```

---

## 9. Risks & Mitigation

### Risk 1: Performance Degradation with Large Datasets
**Likelihood**: High
**Impact**: High

**Mitigation**:
- Implement virtualization for list/grid views (react-window)
- Pagination with infinite scroll
- Debounce filter inputs (300ms)
- Lazy load thumbnails
- Cache filter results

### Risk 2: Complex Filter Logic
**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- Start with basic filters (Phase 1)
- Add advanced filters incrementally (Phase 3)
- Extensive unit tests for filter combinations
- User testing for filter UX

### Risk 3: Integration Conflicts with Existing Code
**Likelihood**: Medium
**Impact**: High

**Mitigation**:
- Incremental refactoring
- Backward compatibility layer
- Comprehensive integration tests
- Feature flags for gradual rollout

### Risk 4: Browser Compatibility Issues
**Likelihood**: Low
**Impact**: Medium

**Mitigation**:
- Use polyfills for modern features
- Cross-browser testing in CI/CD
- Progressive enhancement approach
- Fallback UI for unsupported browsers

---

## 10. Success Criteria

### Phase 1 Success Criteria
- [ ] Status badges display correctly for all status types
- [ ] Basic filters work (player, tournament, street, status)
- [ ] List view and Timeline view implemented
- [ ] View mode switching works smoothly (< 300ms)
- [ ] All unit tests pass (≥ 80% coverage)

### Phase 2 Success Criteria
- [ ] Integration tests pass (≥ 90% coverage)
- [ ] E2E tests cover critical user flows
- [ ] Performance targets met (filter < 500ms, view switch < 300ms)
- [ ] WCAG 2.1 AA compliance verified

### Phase 3 Success Criteria
- [ ] Filter presets save/load correctly
- [ ] Statistics dashboard shows accurate data
- [ ] Bulk actions work for selected hands
- [ ] Search autocomplete functional

### Phase 4 Success Criteria (Production Ready)
- [ ] User acceptance testing passed
- [ ] Mobile responsiveness verified
- [ ] Documentation complete (user guide, API docs)
- [ ] Production deployment successful
- [ ] Zero critical bugs in first week

---

## 11. Future Enhancements (Post-MVP)

### V2.0 Features
- **AI-Powered Recommendations**: "You might be interested in..."
- **Advanced Analytics**: Hand strength distribution, EV calculations
- **Collaborative Features**: Share filters, comment on hands
- **Export Options**: PDF reports, CSV exports
- **Offline Mode**: PWA with service worker

### V3.0 Features
- **Video Editing Integration**: Trim, annotate videos in-app
- **Live Analysis**: Real-time hand analysis as video plays
- **Multi-Language Support**: i18n for global users
- **Custom Dashboards**: User-configurable widget layout

---

## 12. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **Analysis Status** | 비디오 분석 진행 상태 (completed, processing, pending, failed) |
| **Filter Preset** | 저장된 필터 조합 (빠른 재사용) |
| **Bulk Action** | 여러 핸드에 대한 일괄 작업 |
| **View Mode** | 결과 표시 방식 (grid, list, timeline, tree) |
| **Archive Tree** | 토너먼트 > 핸드 > 플레이어 계층 구조 |

### B. References

- **MediaFlow**: https://github.com/pointedsec/MediaFlow
- **React-Media-Library**: https://github.com/Richard1320/React-Media-Library
- **video-library**: https://github.com/ArjunGTX/video-library
- **react-github-media-library**: https://github.com/ivenms/react-github-media-library
- **VGrid**: https://github.com/scanner-research/vgrid
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/

### C. Open Questions

1. **Q**: 필터 프리셋 저장 위치는 로컬 스토리지? 백엔드 DB?
   **A**: Phase 1은 localStorage, Phase 3에서 backend로 마이그레이션

2. **Q**: 통계 대시보드 데이터 갱신 주기는?
   **A**: 실시간 (WebSocket) or 30초 polling?

3. **Q**: Bulk action 권한 제어는?
   **A**: Admin role check + audit logging

4. **Q**: 타임라인 뷰 그룹핑 기준은?
   **A**: 일별? 주별? 월별? → 사용자 선택 가능하게

---

**Document Version**: 1.0.0
**Last Updated**: 2025-01-20
**Next Review**: 2025-01-27
**Approved By**: [Pending]
