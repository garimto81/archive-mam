# Task List: Video Archive Management UI with Status Tracking

**PRD Reference**: tasks/prds/VIDEO-ARCHIVE-MANAGEMENT-UI-prd.md
**Version**: 1.0.0
**Created**: 2025-01-20
**Status**: In Progress

---

## Task 0.0: Setup (MUST COMPLETE FIRST)

### Task 0.0.1: Create Feature Branch
- [ ] Create branch: `feature/VIDEO-ARCHIVE-UI`
- [ ] Update CLAUDE.md with project context

### Task 0.0.2: Setup Project Structure
- [ ] Create `frontend/src/components/archive/` directory structure
- [ ] Create `frontend/src/components/status/` directory
- [ ] Create `frontend/src/components/filters/` directory
- [ ] Create `frontend/src/components/bulk/` directory
- [ ] Create `frontend/src/stores/archiveStore.ts` for state management

### Task 0.0.3: Install Dependencies
- [ ] Install `react-window` for virtualization
- [ ] Install `zustand` for state management (if not already installed)
- [ ] Install additional UI libraries if needed

**Estimated Duration**: 30 minutes
**Dependencies**: None

---

## Phase 1: Core Components (Week 1-2)

### Task 1.0: Status Tracking System (FR-1)

#### Task 1.0.1: Create StatusBadge Component
- [ ] Create `frontend/src/components/status/StatusBadge.tsx`
- [ ] Create `frontend/src/components/status/StatusBadge.test.tsx` (1:1 pair)
- [ ] Implement status variants: completed, processing, pending, failed
- [ ] Add icons for each status (CheckCircle, Loader, Clock, XCircle)
- [ ] Add tooltip for error messages
- [ ] Add accessibility attributes (aria-label, role)

**Acceptance Criteria**:
- [ ] Displays correct icon for each status
- [ ] Shows error tooltip on hover for failed status
- [ ] Passes WCAG 2.1 AA color contrast
- [ ] All tests pass

**Estimated Duration**: 2 hours
**Reference**: MediaFlow - frontend/components/StatusBadge.tsx

#### Task 1.0.2: Create ProgressBar Component
- [ ] Create `frontend/src/components/status/ProgressBar.tsx`
- [ ] Create `frontend/src/components/status/ProgressBar.test.tsx` (1:1 pair)
- [ ] Implement progress bar with 0-100 value
- [ ] Add color variants based on status
- [ ] Add animation for processing state
- [ ] Add accessibility (role="progressbar", aria-valuenow, aria-valuemin, aria-valuemax)

**Acceptance Criteria**:
- [ ] Shows accurate progress percentage
- [ ] Animates smoothly during processing
- [ ] Accessible to screen readers
- [ ] All tests pass

**Estimated Duration**: 1.5 hours
**Reference**: MediaFlow - progress bar patterns

#### Task 1.0.3: Integrate Status Components into HandCard
- [ ] Modify `frontend/src/components/search/HandCard.tsx`
- [ ] Add StatusBadge above thumbnail
- [ ] Add ProgressBar below StatusBadge (if processing)
- [ ] Add error tooltip for failed status
- [ ] Update HandCard tests

**Acceptance Criteria**:
- [ ] Status badge displays correctly on all cards
- [ ] Progress bar shows for processing cards
- [ ] Error tooltip appears for failed cards
- [ ] Tests verify all status types

**Estimated Duration**: 1 hour
**Dependencies**: Task 1.0.1, Task 1.0.2

---

### Task 1.1: Filter System (FR-2)

#### Task 1.1.1: Create FilterPanel Component
- [ ] Create `frontend/src/components/filters/FilterPanel.tsx`
- [ ] Create `frontend/src/components/filters/FilterPanel.test.tsx` (1:1 pair)
- [ ] Add collapsible sections (Basic Filters, Advanced Filters)
- [ ] Add reset filters button
- [ ] Integrate with archiveStore

**Estimated Duration**: 2 hours

#### Task 1.1.2: Create Individual Filter Components
- [ ] Create `frontend/src/components/filters/PlayerFilter.tsx` + test
- [ ] Create `frontend/src/components/filters/TournamentFilter.tsx` + test
- [ ] Create `frontend/src/components/filters/StreetFilter.tsx` + test
- [ ] Create `frontend/src/components/filters/PotSizeFilter.tsx` + test
- [ ] Create `frontend/src/components/filters/StatusFilter.tsx` + test

**Acceptance Criteria**:
- [ ] Each filter shows available options
- [ ] Filters update results in real-time (< 500ms)
- [ ] Multiple filters can be applied simultaneously
- [ ] All tests pass

**Estimated Duration**: 4 hours
**Reference**: react-github-media-library - SearchAndFilter.tsx

#### Task 1.1.3: Create Advanced Filter Components
- [ ] Create `frontend/src/components/filters/PositionFilter.tsx` + test
- [ ] Create `frontend/src/components/filters/ActionTypeFilter.tsx` + test
- [ ] Create `frontend/src/components/filters/ResultFilter.tsx` + test
- [ ] Create `frontend/src/components/filters/TagFilter.tsx` + test

**Estimated Duration**: 4 hours

#### Task 1.1.4: Implement Filter Logic
- [ ] Update `frontend/src/lib/utils/filterUtils.ts`
- [ ] Create `frontend/src/lib/utils/filterUtils.test.ts` (1:1 pair)
- [ ] Implement AND/OR filter combinations
- [ ] Add filter performance optimization (memoization)

**Acceptance Criteria**:
- [ ] Filters apply correctly with AND logic
- [ ] Filter application completes < 500ms for 1000+ items
- [ ] All edge cases covered in tests

**Estimated Duration**: 3 hours
**Reference**: video-library - filter logic patterns

---

### Task 1.2: Multiple View Modes (FR-3)

#### Task 1.2.1: Create ViewModeSwitcher Component
- [ ] Create `frontend/src/components/archive/ViewModeSwitcher.tsx`
- [ ] Create `frontend/src/components/archive/ViewModeSwitcher.test.tsx` (1:1 pair)
- [ ] Add buttons for: Grid, List, Timeline, Tree
- [ ] Add active state styling
- [ ] Integrate with archiveStore

**Estimated Duration**: 1.5 hours
**Reference**: React-Media-Library - view mode switcher

#### Task 1.2.2: Create ListView Component
- [ ] Create `frontend/src/components/archive/ListView.tsx`
- [ ] Create `frontend/src/components/archive/ListView.test.tsx` (1:1 pair)
- [ ] Display hands in detailed list format
- [ ] Show: thumbnail, title, metadata, tags, status
- [ ] Add hover effects
- [ ] Implement virtualization (react-window) for performance

**Acceptance Criteria**:
- [ ] Displays all hand metadata clearly
- [ ] Handles 1000+ items without lag
- [ ] Responsive on mobile (stacks vertically)
- [ ] All tests pass

**Estimated Duration**: 4 hours
**Reference**: React-Media-Library - list view implementation

#### Task 1.2.3: Create TimelineView Component
- [ ] Create `frontend/src/components/archive/TimelineView.tsx`
- [ ] Create `frontend/src/components/archive/TimelineView.test.tsx` (1:1 pair)
- [ ] Group hands by date (year > month > day)
- [ ] Add collapsible date sections
- [ ] Show status badges on timeline entries
- [ ] Add date range selector

**Acceptance Criteria**:
- [ ] Chronologically ordered (latest first)
- [ ] Date groupings expand/collapse correctly
- [ ] Shows status badges for each entry
- [ ] All tests pass

**Estimated Duration**: 4 hours

#### Task 1.2.4: Integrate View Modes into SearchResults
- [ ] Modify `frontend/src/components/search/SearchResults.tsx`
- [ ] Add ViewModeSwitcher component
- [ ] Conditionally render based on selected view mode
- [ ] Persist view mode preference (localStorage)
- [ ] Update tests

**Acceptance Criteria**:
- [ ] View mode switches correctly
- [ ] View mode persists on page refresh
- [ ] Switching completes < 300ms
- [ ] Tests verify all view modes

**Estimated Duration**: 2 hours
**Dependencies**: Task 1.2.1, Task 1.2.2, Task 1.2.3

---

### Task 1.3: Archive Management Dashboard (Integration)

#### Task 1.3.1: Create ArchiveManagementDashboard Component
- [ ] Create `frontend/src/components/archive/ArchiveManagementDashboard.tsx`
- [ ] Create `frontend/src/components/archive/ArchiveManagementDashboard.test.tsx` (1:1 pair)
- [ ] Integrate FilterPanel
- [ ] Integrate ViewModeSwitcher
- [ ] Integrate ResultsContainer (with all view modes)
- [ ] Add responsive layout (3-column desktop, 1-column mobile)

**Estimated Duration**: 3 hours

#### Task 1.3.2: Create Zustand Store
- [ ] Create `frontend/src/stores/archiveStore.ts`
- [ ] Create `frontend/src/stores/archiveStore.test.ts` (1:1 pair)
- [ ] Add state: viewMode, filters, selectedHandIds
- [ ] Add actions: setViewMode, setFilters, resetFilters, toggleHandSelection
- [ ] Add computed values: filteredResults, selectedCount

**Acceptance Criteria**:
- [ ] State updates trigger re-renders correctly
- [ ] Store is accessible from all components
- [ ] All tests pass

**Estimated Duration**: 2 hours

---

## Phase 2: Testing (Week 2-3)

### Task 2.0: Unit Tests

#### Task 2.0.1: Component Unit Tests
- [ ] Verify all components have 1:1 test pairs
- [ ] Ensure ≥ 80% code coverage for components
- [ ] Test all component props and variants
- [ ] Test error states and edge cases

**Estimated Duration**: 4 hours

#### Task 2.0.2: Utility Function Tests
- [ ] Test filterUtils.ts thoroughly
- [ ] Test treeBuilder.ts with various data structures
- [ ] Test edge cases (empty arrays, null values, etc.)

**Estimated Duration**: 2 hours

---

### Task 2.1: Integration Tests

#### Task 2.1.1: Filter + View Mode Integration Tests
- [ ] Test filter changes update all view modes
- [ ] Test view mode changes preserve filter state
- [ ] Test multiple filters applied simultaneously

**Estimated Duration**: 3 hours

#### Task 2.1.2: Dashboard Integration Tests
- [ ] Test full dashboard workflow (search → filter → view mode → select)
- [ ] Test state persistence (localStorage)
- [ ] Test responsive behavior

**Estimated Duration**: 3 hours

---

### Task 2.2: E2E Tests (Playwright)

#### Task 2.2.1: Create E2E Test Spec
- [ ] Create `frontend/tests/e2e/archive-management.spec.ts`
- [ ] Test: Search and filter hands
- [ ] Test: Switch view modes
- [ ] Test: Select and deselect hands
- [ ] Test: Mobile responsiveness

**Acceptance Criteria**:
- [ ] All critical user flows covered
- [ ] Tests pass in Chrome, Firefox, Safari
- [ ] Mobile tests pass

**Estimated Duration**: 4 hours
**Reference**: PRD Section 8.3 E2E Tests

#### Task 2.2.2: Performance Testing
- [ ] Test filter application < 500ms
- [ ] Test view mode switch < 300ms
- [ ] Test dashboard load < 2s
- [ ] Test with 1000+ items

**Estimated Duration**: 2 hours

---

### Task 2.3: Accessibility Audit

#### Task 2.3.1: WCAG 2.1 AA Compliance Check
- [ ] Run axe-core accessibility tests
- [ ] Verify keyboard navigation works for all interactive elements
- [ ] Test with screen reader (NVDA/JAWS)
- [ ] Verify color contrast ratios (≥ 4.5:1)

**Estimated Duration**: 3 hours

---

## Phase 3: Advanced Features (Week 3-4)

### Task 3.0: Filter Presets (FR-2 Extension)

#### Task 3.0.1: Create FilterPreset Component
- [ ] Create `frontend/src/components/filters/FilterPreset.tsx`
- [ ] Create `frontend/src/components/filters/FilterPreset.test.tsx` (1:1 pair)
- [ ] Add save preset button
- [ ] Add load preset dropdown
- [ ] Add delete preset button
- [ ] Store presets in localStorage (Phase 1) or backend (Phase 3+)

**Acceptance Criteria**:
- [ ] Can save current filters as preset
- [ ] Can load saved presets
- [ ] Can delete presets
- [ ] Presets persist on page refresh

**Estimated Duration**: 3 hours

---

### Task 3.1: Statistics Dashboard (FR-5)

#### Task 3.1.1: Create StatusOverview Component
- [ ] Create `frontend/src/components/archive/StatusOverview.tsx`
- [ ] Create `frontend/src/components/archive/StatusOverview.test.tsx` (1:1 pair)
- [ ] Display: Total hands, Analyzed, Processing, Pending, Failed
- [ ] Add progress bar for analysis completion rate
- [ ] Add refresh button

**Estimated Duration**: 3 hours

#### Task 3.1.2: Create StatisticsCard Components
- [ ] Create `frontend/src/components/archive/PlayerStatistics.tsx` + test
- [ ] Create `frontend/src/components/archive/TournamentStatistics.tsx` + test
- [ ] Create `frontend/src/components/archive/RecentActivity.tsx` + test
- [ ] Display top players by hand count
- [ ] Display top tournaments by hand count
- [ ] Display recent uploads/analyses

**Estimated Duration**: 4 hours

#### Task 3.1.3: Integrate Statistics into Dashboard
- [ ] Add StatusOverview to ArchiveManagementDashboard
- [ ] Add collapsible statistics section
- [ ] Fetch statistics data from API (mock for now)

**Estimated Duration**: 2 hours

---

### Task 3.2: Bulk Actions (FR-6)

#### Task 3.2.1: Create BulkSelectCheckbox Component
- [ ] Create `frontend/src/components/bulk/BulkSelectCheckbox.tsx`
- [ ] Create `frontend/src/components/bulk/BulkSelectCheckbox.test.tsx` (1:1 pair)
- [ ] Add checkbox to each hand card
- [ ] Add "Select All" checkbox in header
- [ ] Sync with archiveStore.selectedHandIds

**Estimated Duration**: 2 hours

#### Task 3.2.2: Create BulkActionsToolbar Component
- [ ] Create `frontend/src/components/bulk/BulkActionsToolbar.tsx`
- [ ] Create `frontend/src/components/bulk/BulkActionsToolbar.test.tsx` (1:1 pair)
- [ ] Add buttons: Add Tags, Remove Tags, Reanalyze, Download
- [ ] Show selected count
- [ ] Add clear selection button

**Estimated Duration**: 2 hours

#### Task 3.2.3: Create BulkActionModal Component
- [ ] Create `frontend/src/components/bulk/BulkActionModal.tsx`
- [ ] Create `frontend/src/components/bulk/BulkActionModal.test.tsx` (1:1 pair)
- [ ] Add tag input for bulk tag operations
- [ ] Add confirmation step
- [ ] Show progress for bulk operations

**Estimated Duration**: 3 hours

#### Task 3.2.4: Implement Bulk Action Logic
- [ ] Create `frontend/src/lib/api/bulkActions.ts`
- [ ] Create `frontend/src/lib/api/bulkActions.test.ts` (1:1 pair)
- [ ] Implement bulk tag add/remove
- [ ] Implement bulk reanalyze request
- [ ] Implement bulk download (zip file)

**Estimated Duration**: 4 hours

---

### Task 3.3: Search Enhancement (FR-4)

#### Task 3.3.1: Add Autocomplete to SearchBar
- [ ] Modify `frontend/src/components/search/SearchBar.tsx`
- [ ] Add autocomplete dropdown
- [ ] Fetch suggestions from API (players, tournaments)
- [ ] Add keyboard navigation (arrow keys, enter, esc)
- [ ] Debounce autocomplete requests (200ms)

**Estimated Duration**: 3 hours

#### Task 3.3.2: Add Recent Searches
- [ ] Store recent searches in localStorage
- [ ] Display recent searches below search bar
- [ ] Add clear recent searches button
- [ ] Limit to 10 most recent

**Estimated Duration**: 2 hours

#### Task 3.3.3: Add Search Highlighting
- [ ] Highlight search terms in results
- [ ] Use `<mark>` tag for semantic highlighting
- [ ] Add CSS for highlight styling

**Estimated Duration**: 1.5 hours

---

## Phase 4: Polish & Deployment (Week 4-5)

### Task 4.0: UI/UX Improvements

#### Task 4.0.1: User Feedback Implementation
- [ ] Conduct user testing session (5 users)
- [ ] Collect feedback on filter usability
- [ ] Collect feedback on view mode preferences
- [ ] Implement top 3 requested improvements

**Estimated Duration**: 6 hours

#### Task 4.0.2: Loading States & Skeletons
- [ ] Add skeleton loaders for all view modes
- [ ] Add loading spinners for filter operations
- [ ] Add optimistic UI updates for bulk actions

**Estimated Duration**: 3 hours

#### Task 4.0.3: Error Handling & Messages
- [ ] Add error boundaries for each major component
- [ ] Add user-friendly error messages
- [ ] Add retry buttons for failed operations
- [ ] Add toast notifications for success/error

**Estimated Duration**: 3 hours

---

### Task 4.1: Mobile Optimization

#### Task 4.1.1: Mobile Filter Panel
- [ ] Make filter panel collapsible on mobile
- [ ] Add bottom sheet for filters (slide up from bottom)
- [ ] Optimize touch targets (≥ 44px)

**Estimated Duration**: 3 hours

#### Task 4.1.2: Mobile View Modes
- [ ] Optimize grid view for mobile (1-2 columns)
- [ ] Optimize list view for mobile (stacked cards)
- [ ] Hide timeline view on mobile (or simplify)

**Estimated Duration**: 2 hours

#### Task 4.1.3: Mobile Responsiveness Testing
- [ ] Test on iOS Safari (iPhone 12, iPhone SE)
- [ ] Test on Android Chrome (Samsung Galaxy, Pixel)
- [ ] Test on tablet (iPad, Samsung Tab)
- [ ] Fix any layout issues

**Estimated Duration**: 3 hours

---

### Task 4.2: Documentation

#### Task 4.2.1: User Guide
- [ ] Create `docs/USER_GUIDE_ARCHIVE_UI.md`
- [ ] Document how to use filters
- [ ] Document how to switch view modes
- [ ] Document how to use bulk actions
- [ ] Add screenshots/GIFs

**Estimated Duration**: 4 hours

#### Task 4.2.2: API Documentation
- [ ] Document new API endpoints (if added)
- [ ] Update OpenAPI spec
- [ ] Add request/response examples

**Estimated Duration**: 2 hours

#### Task 4.2.3: Component Documentation
- [ ] Add JSDoc comments to all components
- [ ] Document component props
- [ ] Add usage examples to Storybook (if available)

**Estimated Duration**: 3 hours

---

### Task 4.3: Production Deployment

#### Task 4.3.1: Code Review
- [ ] Request code review from team
- [ ] Address all review comments
- [ ] Get approval from at least 2 reviewers

**Estimated Duration**: Varies

#### Task 4.3.2: Performance Audit
- [ ] Run Lighthouse audit (score ≥ 90)
- [ ] Check bundle size (should not increase > 10%)
- [ ] Optimize images and assets
- [ ] Add lazy loading for heavy components

**Estimated Duration**: 3 hours

#### Task 4.3.3: Deployment
- [ ] Merge to main branch
- [ ] Deploy to staging environment
- [ ] Run smoke tests on staging
- [ ] Deploy to production
- [ ] Monitor for errors (first 24 hours)

**Estimated Duration**: 2 hours + monitoring

---

## Task Dependencies Visualization

```
Task 0.0 (Setup)
  ↓
Task 1.0 (Status System) → Task 1.0.3 (Integrate into HandCard)
  ↓
Task 1.1 (Filter System) ──┐
  ↓                        │
Task 1.2 (View Modes) ─────┼→ Task 1.3 (Dashboard Integration)
  ↓                        │
Task 1.3.2 (Zustand Store)─┘
  ↓
Task 2.0-2.3 (All Testing)
  ↓
Task 3.0-3.3 (Advanced Features)
  ↓
Task 4.0-4.3 (Polish & Deploy)
```

---

## Success Metrics Checklist

### Phase 1 Complete
- [ ] All core components implemented
- [ ] Unit tests pass (≥ 80% coverage)
- [ ] Integration tests pass
- [ ] View mode switching < 300ms
- [ ] Filter application < 500ms

### Phase 2 Complete
- [ ] E2E tests pass on all browsers
- [ ] Performance benchmarks met
- [ ] WCAG 2.1 AA compliant
- [ ] No critical bugs

### Phase 3 Complete
- [ ] Filter presets functional
- [ ] Statistics dashboard accurate
- [ ] Bulk actions work correctly
- [ ] Search autocomplete functional

### Phase 4 Complete
- [ ] User testing feedback implemented
- [ ] Mobile responsive
- [ ] Documentation complete
- [ ] Production deployment successful
- [ ] Zero critical bugs in first week

---

## Risk Mitigation Checklist

- [ ] **Performance**: Virtualization implemented for large datasets
- [ ] **Filter Logic**: Comprehensive unit tests for filter combinations
- [ ] **Integration**: Feature flags for gradual rollout
- [ ] **Browser Compatibility**: Cross-browser testing in CI/CD

---

**Total Estimated Duration**: 4-5 weeks (160-200 hours)
**Team Size**: 2-3 developers
**Next Review**: End of Week 1 (after Phase 1 core components)
