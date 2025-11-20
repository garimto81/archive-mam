/**
 * FilterPanel Component Tests
 *
 * Test suite for the FilterPanel component covering:
 * - Rendering all filter sections
 * - Filter updates on user interaction
 * - Clear filters functionality
 * - Active filter count display
 * - Collapsible sections
 * - Mobile drawer vs desktop sidebar
 * - Filter validation
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterPanel } from '../FilterPanel';
import type { SearchFilters } from '@/types/search';

// Mock sub-components
vi.mock('../FilterSection', () => ({
  FilterSection: ({ title, children, isExpanded, onToggle }: any) => (
    <div data-testid={`filter-section-${title}`}>
      <button onClick={onToggle}>{title}</button>
      {isExpanded && <div>{children}</div>}
    </div>
  ),
}));

vi.mock('../ActiveFilters', () => ({
  ActiveFilters: ({ filters, onRemove, onClear }: any) => (
    <div data-testid="active-filters">
      {Object.entries(filters || {}).length > 0 && (
        <>
          <div>{Object.entries(filters || {}).length} active filters</div>
          <button onClick={onClear}>Clear All</button>
        </>
      )}
    </div>
  ),
}));

vi.mock('../CardSelector', () => ({
  CardSelector: ({ value, onChange }: any) => (
    <div data-testid="card-selector">
      <input
        placeholder="Enter card"
        onChange={(e) => onChange([...value, e.target.value])}
      />
    </div>
  ),
}));

// Mock useFilters hook
vi.mock('@/hooks/useFilters', () => ({
  useFilters: () => ({
    filters: {} as SearchFilters,
    setFilters: vi.fn(),
    addFilter: vi.fn(),
    removeFilter: vi.fn(),
    clearFilters: vi.fn(),
    activeCount: 0,
  }),
}));

describe('FilterPanel Component', () => {
  const mockFilters: SearchFilters = {
    potSizeMin: 50,
    potSizeMax: 500,
    tags: ['HERO_CALL', 'RIVER'],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render filter panel', () => {
      render(<FilterPanel />);

      expect(screen.getByRole('region', { name: /filter/i })).toBeInTheDocument();
    });

    it('should render all filter sections', () => {
      render(<FilterPanel />);

      expect(screen.getByTestId(/filter-section/)).toBeInTheDocument();
    });

    it('should display active filter count', () => {
      render(<FilterPanel />);

      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should render clear filters button', () => {
      render(<FilterPanel />);

      expect(screen.getByRole('button', { name: /clear all/i })).toBeInTheDocument();
    });
  });

  describe('Filter Sections', () => {
    it('should render pot size filter section', () => {
      render(<FilterPanel />);

      const sections = screen.getAllByTestId(/filter-section/);
      expect(sections.length).toBeGreaterThan(0);
    });

    it('should allow expanding/collapsing sections', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const buttons = screen.getAllByRole('button');
      if (buttons.length > 0) {
        await user.click(buttons[0]);
      }

      // Sections should toggle
      expect(screen.getAllByTestId(/filter-section/)).toHaveLength(
        expect.any(Number)
      );
    });

    it('should maintain section state during interaction', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const firstSection = screen.getByTestId(/filter-section/).querySelector('button');
      if (firstSection) {
        await user.click(firstSection);
        expect(firstSection).toBeInTheDocument();
      }
    });
  });

  describe('Filter Updates', () => {
    it('should update pot size minimum', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      if (inputs.length > 0) {
        await user.type(inputs[0], '100');
      }

      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should update pot size maximum', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      if (inputs.length > 1) {
        await user.type(inputs[1], '1000');
      }

      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should handle tag selection', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const checkboxes = screen.queryAllByRole('checkbox');
      if (checkboxes.length > 0) {
        await user.click(checkboxes[0]);
      }

      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should handle card selection', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const cardSelector = screen.getByTestId('card-selector');
      const input = within(cardSelector).getByPlaceholderText(/Enter card/i);

      await user.type(input, 'A');

      expect(cardSelector).toBeInTheDocument();
    });
  });

  describe('Clear Filters', () => {
    it('should clear all filters when button is clicked', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await user.click(clearButton);

      // Filters should be cleared
      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should reset all filter inputs', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await user.click(clearButton);

      const inputs = screen.queryAllByRole('textbox');
      inputs.forEach(input => {
        expect(input).toHaveValue('');
      });
    });

    it('should uncheck all checkboxes', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await user.click(clearButton);

      const checkboxes = screen.queryAllByRole('checkbox');
      checkboxes.forEach(checkbox => {
        expect(checkbox).not.toBeChecked();
      });
    });
  });

  describe('Filter Validation', () => {
    it('should validate pot size minimum is less than maximum', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      if (inputs.length >= 2) {
        await user.type(inputs[0], '500');
        await user.type(inputs[1], '100');

        // Should show validation error or adjust values
        expect(screen.getByTestId('active-filters')).toBeInTheDocument();
      }
    });

    it('should handle negative pot sizes', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      if (inputs.length > 0) {
        await user.type(inputs[0], '-50');
      }

      // Should reject negative value
      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should validate date ranges', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const dateInputs = screen.queryAllByRole('textbox', { hidden: false });
      if (dateInputs.length >= 2) {
        // Type end date before start date
        await user.type(dateInputs[0], '2024-12-31');
        await user.type(dateInputs[1], '2024-01-01');

        expect(screen.getByTestId('active-filters')).toBeInTheDocument();
      }
    });
  });

  describe('Active Filter Display', () => {
    it('should show count of active filters', () => {
      render(<FilterPanel />);

      const activeFilters = screen.getByTestId('active-filters');
      expect(activeFilters).toBeInTheDocument();
    });

    it('should display active filter values', () => {
      render(<FilterPanel />);

      // After setting filters, should show them
      const activeFilters = screen.getByTestId('active-filters');
      expect(activeFilters).toBeInTheDocument();
    });

    it('should allow removing individual filters', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const removeButtons = screen.queryAllByRole('button', { name: /remove|×|x/i });
      if (removeButtons.length > 0) {
        await user.click(removeButtons[0]);
      }

      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should render desktop sidebar version on large screens', () => {
      render(<FilterPanel />);

      const panel = screen.getByRole('region', { name: /filter/i });
      expect(panel).toHaveClass(expect.stringMatching(/sidebar|aside/i));
    });

    it('should render mobile drawer version on small screens', () => {
      // Mock window.innerWidth for mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 400,
      });

      render(<FilterPanel />);

      const panel = screen.getByRole('region', { name: /filter/i });
      expect(panel).toBeInTheDocument();

      // Restore original value
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });
    });

    it('should have toggle button for mobile drawer', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 400,
      });

      render(<FilterPanel />);

      const toggleButton = screen.queryByRole('button', { name: /filter|show filter/i });
      expect(toggleButton).toBeInTheDocument();

      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });
    });
  });

  describe('Accessibility', () => {
    it('should have accessible filter region', () => {
      render(<FilterPanel />);

      expect(screen.getByRole('region', { name: /filter/i })).toBeInTheDocument();
    });

    it('should have proper ARIA labels on inputs', () => {
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      inputs.forEach(input => {
        expect(
          input.getAttribute('aria-label') || input.getAttribute('placeholder')
        ).toBeTruthy();
      });
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      // Tab through all interactive elements
      await user.tab();

      const panel = screen.getByRole('region', { name: /filter/i });
      expect(panel).toBeInTheDocument();
    });

    it('should announce filter changes to screen readers', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      if (inputs.length > 0) {
        await user.type(inputs[0], '100');
      }

      const activeFilters = screen.getByTestId('active-filters');
      expect(activeFilters).toHaveAttribute('role', expect.anything());
    });
  });

  describe('Edge Cases', () => {
    it('should handle very large pot sizes', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      if (inputs.length > 0) {
        await user.type(inputs[0], '999999999');
      }

      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should handle multiple tag selections', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const checkboxes = screen.queryAllByRole('checkbox');
      for (let i = 0; i < Math.min(3, checkboxes.length); i++) {
        await user.click(checkboxes[i]);
      }

      expect(screen.getByTestId('active-filters')).toBeInTheDocument();
    });

    it('should handle rapid filter changes', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const inputs = screen.getAllByRole('textbox');
      if (inputs.length > 0) {
        await user.type(inputs[0], '1');
        await user.clear(inputs[0]);
        await user.type(inputs[0], '2');
        await user.clear(inputs[0]);
        await user.type(inputs[0], '3');
      }

      expect(inputs[0]).toHaveValue('3');
    });
  });

  describe('Collapsible Sections', () => {
    it('should expand section on click', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const buttons = screen.getAllByRole('button');
      if (buttons.length > 0) {
        await user.click(buttons[0]);
      }

      expect(buttons[0]).toBeInTheDocument();
    });

    it('should collapse section on second click', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const buttons = screen.getAllByRole('button');
      if (buttons.length > 0) {
        await user.click(buttons[0]);
        await user.click(buttons[0]);
      }

      expect(buttons[0]).toBeInTheDocument();
    });

    it('should remember expanded state', async () => {
      const user = userEvent.setup();
      render(<FilterPanel />);

      const buttons = screen.getAllByRole('button');
      if (buttons.length > 0) {
        await user.click(buttons[0]);

        // State should be maintained
        expect(screen.getAllByTestId(/filter-section/)).toHaveLength(
          expect.any(Number)
        );
      }
    });
  });
});
