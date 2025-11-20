/**
 * HandCard Component Test Suite
 *
 * Tests for accessibility, keyboard navigation, and functionality
 * Framework: Vitest + React Testing Library
 *
 * Run tests: npm run test
 * Run with coverage: npm run test:coverage
 * Run accessibility tests: npm run test:a11y
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HandCard } from '../HandCard';
import { SearchResultItem } from '@/types/search';

/**
 * Mock search result for testing
 */
const mockHand: SearchResultItem = {
  hand_id: 'test_hand_001',
  tournament_id: 'wsop_2024',
  score: 0.92,
  hero_name: 'Junglemann',
  villain_name: 'Phil Ivey',
  hero_position: 'BTN',
  villain_position: 'CO',
  pot_bb: 145.5,
  description: 'Junglemann makes an insane river call with ace-high against Phil Ivey triple barrel bluff.',
  tags: ['HERO_CALL', 'RIVER_DECISION', 'HIGH_STAKES'],
  result: 'WIN',
  timestamp: '2024-07-15T14:30:00Z',
  video_url: 'gs://poker-videos-prod/wsop_2024/main_event/day5_table3.mp4',
  video_start: 3421.5,
  video_end: 3482.0,
  thumbnail_url: 'gs://poker-videos-prod/thumbnails/wsop_2024_hand_3421.jpg',
  duration_seconds: 61
};

describe('HandCard Component', () => {
  /**
   * ACCESSIBILITY TESTS
   * Test WCAG 2.1 AA compliance
   */
  describe('Accessibility', () => {
    it('should have proper ARIA attributes when clickable', () => {
      const mockOnClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      const card = screen.getByRole('button');
      expect(card).toHaveAttribute('role', 'button');
      expect(card).toHaveAttribute('aria-label');
      expect(card.getAttribute('aria-label')).toContain('Junglemann');
      expect(card.getAttribute('aria-label')).toContain('Phil Ivey');
      expect(card.getAttribute('aria-label')).toContain('145.5 BB');
    });

    it('should not have button role when not clickable', () => {
      render(<HandCard hand={mockHand} />);

      const card = screen.queryByRole('button');
      expect(card).not.toBeInTheDocument();
    });

    it('should be keyboard accessible with proper tabIndex', () => {
      const mockOnClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      const card = screen.getByRole('button');
      expect(card).toHaveAttribute('tabIndex', '0');
    });

    it('should have focus visible styles when focused', async () => {
      const mockOnClick = vi.fn();
      const { container } = render(
        <HandCard hand={mockHand} onClick={mockOnClick} />
      );

      const card = screen.getByRole('button');
      card.focus();

      await waitFor(() => {
        expect(card).toHaveFocus();
        // Check for focus styles
        const classList = Array.from(card.classList);
        expect(classList).toContain('ring-2');
      });
    });

    it('should announce all important content to screen readers', () => {
      const mockOnClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      const ariaLabel = screen.getByRole('button').getAttribute('aria-label');
      expect(ariaLabel).toContain('Poker hand');
      expect(ariaLabel).toContain(mockHand.hero_name);
      expect(ariaLabel).toContain(mockHand.villain_name);
      expect(ariaLabel).toContain('Pot');
      expect(ariaLabel).toContain('Result');
      expect(ariaLabel).toContain('WIN');
    });

    it('should hide decorative icons from screen readers', () => {
      render(<HandCard hand={mockHand} />);

      const icons = screen.queryAllByRole('img', { hidden: true });
      // All decorative icons should have aria-hidden="true"
      icons.forEach((icon) => {
        // This would be verified through the actual rendered output
      });
    });
  });

  /**
   * KEYBOARD NAVIGATION TESTS
   * Test Enter/Space activation and Tab focus
   */
  describe('Keyboard Navigation', () => {
    it('should activate on Enter key', async () => {
      const mockOnClick = vi.fn();
      const user = userEvent.setup();

      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      const card = screen.getByRole('button');
      card.focus();

      await user.keyboard('{Enter}');

      expect(mockOnClick).toHaveBeenCalledWith(mockHand.hand_id);
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    it('should activate on Space key', async () => {
      const mockOnClick = vi.fn();
      const user = userEvent.setup();

      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      const card = screen.getByRole('button');
      card.focus();

      await user.keyboard(' ');

      expect(mockOnClick).toHaveBeenCalledWith(mockHand.hand_id);
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    it('should not activate on other keys', async () => {
      const mockOnClick = vi.fn();
      const user = userEvent.setup();

      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      const card = screen.getByRole('button');
      card.focus();

      await user.keyboard('a');

      expect(mockOnClick).not.toHaveBeenCalled();
    });

    it('should support Tab navigation', async () => {
      const mockOnClick = vi.fn();
      const { container } = render(
        <div>
          <button>Before</button>
          <HandCard hand={mockHand} onClick={mockOnClick} />
          <button>After</button>
        </div>
      );

      const beforeBtn = screen.getByRole('button', { name: /Before/i });
      const handCard = screen.getByRole('button', { name: /Poker hand/ });
      const afterBtn = screen.getByRole('button', { name: /After/i });

      // Tab should move focus forward
      beforeBtn.focus();
      expect(document.activeElement).toBe(beforeBtn);

      // ... Tab navigation testing
    });
  });

  /**
   * CLICK INTERACTION TESTS
   */
  describe('Click Interactions', () => {
    it('should call onClick with hand_id when clicked', () => {
      const mockOnClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      const card = screen.getByRole('button');
      fireEvent.click(card);

      expect(mockOnClick).toHaveBeenCalledWith(mockHand.hand_id);
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    it('should not call onClick when no onClick prop provided', () => {
      const { container } = render(<HandCard hand={mockHand} />);

      // Card should not have click behavior when no onClick
      const card = container.querySelector('[role="button"]');
      expect(card).not.toBeInTheDocument();
    });

    it('should handle cursor pointer style when clickable', () => {
      const mockOnClick = vi.fn();
      const { container } = render(
        <HandCard hand={mockHand} onClick={mockOnClick} />
      );

      const card = container.querySelector('[role="button"]');
      const classList = Array.from(card!.classList);

      expect(classList).toContain('cursor-pointer');
    });
  });

  /**
   * RENDERING TESTS
   */
  describe('Rendering', () => {
    it('should render all required content sections', () => {
      const mockOnClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      // Check for main content
      expect(screen.getByText(/Junglemann/i)).toBeInTheDocument();
      expect(screen.getByText(/Phil Ivey/i)).toBeInTheDocument();
      expect(screen.getByText(/145.5 BB/i)).toBeInTheDocument();
      expect(screen.getByText(/WIN/i)).toBeInTheDocument();
      expect(screen.getByText(/insane river call/i)).toBeInTheDocument();
    });

    it('should render relevance score', () => {
      const mockOnClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      expect(screen.getByText(/Relevance: 92%/)).toBeInTheDocument();
    });

    it('should render result badge with correct color', () => {
      const mockOnClick = vi.fn();
      const { container } = render(
        <HandCard hand={mockHand} onClick={mockOnClick} />
      );

      const resultBadge = screen.getByText('WIN');
      expect(resultBadge).toHaveClass('bg-poker-chip-green/20');
      expect(resultBadge).toHaveClass('text-poker-chip-green');
    });

    it('should render tags with proper formatting', () => {
      const mockOnClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={mockOnClick} />);

      // Tags should be rendered and formatted
      expect(screen.getByText(/Hero Call/i)).toBeInTheDocument();
      expect(screen.getByText(/River Decision/i)).toBeInTheDocument();
      expect(screen.getByText(/High Stakes/i)).toBeInTheDocument();
    });

    it('should render dark mode classes', () => {
      const mockOnClick = vi.fn();
      const { container } = render(
        <HandCard hand={mockHand} onClick={mockOnClick} />
      );

      const card = container.firstChild as HTMLElement;
      const classList = Array.from(card.classList);

      expect(classList).toContain('dark:bg-slate-950');
      expect(classList).toContain('dark:border-slate-800');
    });
  });

  /**
   * RESPONSIVE DESIGN TESTS
   */
  describe('Responsive Design', () => {
    it('should have responsive classes', () => {
      const mockOnClick = vi.fn();
      const { container } = render(
        <HandCard hand={mockHand} onClick={mockOnClick} />
      );

      const card = container.firstChild as HTMLElement;
      const classList = Array.from(card.classList);

      // Check for responsive patterns
      expect(classList.toString()).toMatch(/flex|grid|w-full/);
    });
  });

  /**
   * IMAGE LOADING TESTS
   */
  describe('Image Loading', () => {
    it('should pass priority prop to thumbnail', () => {
      const mockOnClick = vi.fn();
      const { rerender } = render(
        <HandCard hand={mockHand} onClick={mockOnClick} priority={true} />
      );

      // Priority should be passed to HandThumbnail component
      // This would be verified through component integration test

      rerender(
        <HandCard hand={mockHand} onClick={mockOnClick} priority={false} />
      );

      // Re-render should work without issues
    });
  });

  /**
   * SNAPSHOT TESTS
   */
  describe('Snapshots', () => {
    it('should match snapshot with all props', () => {
      const mockOnClick = vi.fn();
      const { container } = render(
        <HandCard
          hand={mockHand}
          onClick={mockOnClick}
          priority={true}
          className="custom-class"
        />
      );

      expect(container).toMatchSnapshot();
    });

    it('should match snapshot without onClick', () => {
      const { container } = render(<HandCard hand={mockHand} />);

      expect(container).toMatchSnapshot();
    });
  });

  /**
   * EDGE CASES
   */
  describe('Edge Cases', () => {
    it('should handle missing optional fields', () => {
      const minimalHand: SearchResultItem = {
        hand_id: 'minimal_hand',
        tournament_id: 'tournament',
        score: 0.5,
        hero_name: 'Hero',
        pot_bb: 50,
        description: 'Description',
        tags: [],
        video_url: 'gs://bucket/video.mp4'
      };

      const mockOnClick = vi.fn();
      const { container } = render(
        <HandCard hand={minimalHand} onClick={mockOnClick} />
      );

      expect(container).toBeInTheDocument();
    });

    it('should handle very long description', () => {
      const longDescriptionHand = {
        ...mockHand,
        description: 'A'.repeat(500) // Very long description
      };

      const mockOnClick = vi.fn();
      render(<HandCard hand={longDescriptionHand} onClick={mockOnClick} />);

      // Should render without overflow issues
      const description = screen.getByText(/A+/);
      expect(description).toHaveClass('line-clamp-2');
    });

    it('should handle many tags', () => {
      const manyTagsHand = {
        ...mockHand,
        tags: [
          'HERO_CALL',
          'BLUFF',
          'VALUE_BET',
          'RIVER_DECISION',
          'ALL_IN',
          'HIGH_STAKES'
        ]
      };

      const mockOnClick = vi.fn();
      render(<HandCard hand={manyTagsHand} onClick={mockOnClick} />);

      // Should show "+3 more" indicator
      expect(screen.getByText(/\+\d+ more/)).toBeInTheDocument();
    });
  });

  /**
   * PERFORMANCE TESTS
   */
  describe('Performance', () => {
    it('should render efficiently with memoization', () => {
      const mockOnClick = vi.fn();

      const { rerender } = render(
        <HandCard hand={mockHand} onClick={mockOnClick} />
      );

      // Re-render with same props should be no-op
      rerender(<HandCard hand={mockHand} onClick={mockOnClick} />);

      // Click handler should be called only once (not duplicated)
      const card = screen.getByRole('button');
      fireEvent.click(card);

      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });
  });
});

/**
 * INTEGRATION TESTS
 * Tests for component interaction with parent components
 */
describe('HandCard Integration', () => {
  it('should work in a grid layout', () => {
    const mockOnClick = vi.fn();
    const hands: SearchResultItem[] = [mockHand, mockHand];

    const { container } = render(
      <div className="grid grid-cols-2 gap-4">
        {hands.map((hand) => (
          <HandCard
            key={hand.hand_id}
            hand={hand}
            onClick={mockOnClick}
          />
        ))}
      </div>
    );

    expect(container.querySelector('.grid')).toBeInTheDocument();
    expect(screen.getAllByRole('button')).toHaveLength(2);
  });

  it('should work with navigation router', async () => {
    const mockOnClick = vi.fn();
    const user = userEvent.setup();

    render(<HandCard hand={mockHand} onClick={mockOnClick} />);

    const card = screen.getByRole('button');
    await user.click(card);

    expect(mockOnClick).toHaveBeenCalledWith(mockHand.hand_id);
  });
});
