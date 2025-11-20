/**
 * HandCard Component Tests
 *
 * Test suite for the HandCard component covering:
 * - Hand metadata rendering
 * - Thumbnail image display
 * - Tag rendering with colors
 * - Click handler with handId
 * - Keyboard navigation (Enter, Space)
 * - Accessibility attributes
 * - Responsive layout
 * - Focus states
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HandCard } from '../HandCard';
import type { SearchResultItem } from '@/types/search';

// Mock sub-components
vi.mock('../HandThumbnail', () => ({
  HandThumbnail: ({ url, alt, priority }: any) => (
    <img src={url} alt={alt} data-testid="hand-thumbnail" data-priority={priority} />
  ),
}));

vi.mock('../HandMetadata', () => ({
  HandMetadata: ({ hand }: any) => (
    <div data-testid="hand-metadata">
      <div>{hand.hero_name} vs {hand.villain_name}</div>
      <div>{hand.pot_bb} BB</div>
    </div>
  ),
}));

vi.mock('../HandTags', () => ({
  HandTags: ({ tags }: any) => (
    <div data-testid="hand-tags">
      {tags.map((tag: string) => (
        <span key={tag} className="tag">
          {tag}
        </span>
      ))}
    </div>
  ),
}));

describe('HandCard Component', () => {
  const mockHand: SearchResultItem = {
    handId: 'wsop_2024_main_event_hand_3421',
    hero_name: 'Junglemann',
    villain_name: 'Phil Ivey',
    pot_bb: 145.5,
    score: 0.92,
    street: 'RIVER' as const,
    result: 'WIN' as const,
    tags: ['HERO_CALL', 'RIVER_DECISION', 'HIGH_STAKES'],
    thumbnail_url: 'https://example.com/thumb.jpg',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render hand card with metadata', () => {
      render(<HandCard hand={mockHand} />);

      expect(screen.getByTestId('hand-metadata')).toBeInTheDocument();
      expect(screen.getByText(/Junglemann vs Phil Ivey/)).toBeInTheDocument();
      expect(screen.getByText(/145.5 BB/)).toBeInTheDocument();
    });

    it('should render thumbnail image', () => {
      render(<HandCard hand={mockHand} />);

      const thumbnail = screen.getByTestId('hand-thumbnail');
      expect(thumbnail).toBeInTheDocument();
      expect(thumbnail).toHaveAttribute('src', mockHand.thumbnail_url);
    });

    it('should render tags', () => {
      render(<HandCard hand={mockHand} />);

      expect(screen.getByTestId('hand-tags')).toBeInTheDocument();
      expect(screen.getByText('HERO_CALL')).toBeInTheDocument();
      expect(screen.getByText('RIVER_DECISION')).toBeInTheDocument();
      expect(screen.getByText('HIGH_STAKES')).toBeInTheDocument();
    });

    it('should render as button when onClick is provided', () => {
      const onClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      expect(card).toBeInTheDocument();
      expect(card).toHaveAttribute('role', 'button');
    });

    it('should not have button role when onClick is not provided', () => {
      render(<HandCard hand={mockHand} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('div');
      expect(card?.getAttribute('role')).not.toBe('button');
    });
  });

  describe('Image Priority', () => {
    it('should pass priority prop to thumbnail', () => {
      render(<HandCard hand={mockHand} priority={true} />);

      const thumbnail = screen.getByTestId('hand-thumbnail');
      expect(thumbnail).toHaveAttribute('data-priority', 'true');
    });

    it('should default to non-priority', () => {
      render(<HandCard hand={mockHand} />);

      const thumbnail = screen.getByTestId('hand-thumbnail');
      expect(thumbnail).toHaveAttribute('data-priority', 'false');
    });
  });

  describe('Click Handler', () => {
    it('should call onClick with handId when card is clicked', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      if (card) {
        await user.click(card);
      }

      expect(onClick).toHaveBeenCalledWith(mockHand.handId);
    });

    it('should not call onClick if not provided', async () => {
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('div');
      if (card) {
        await user.click(card);
      }

      // Should not throw or cause issues
      expect(card).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('should trigger click on Enter key', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      if (card) {
        card.focus();
        await user.keyboard('{Enter}');
      }

      expect(onClick).toHaveBeenCalledWith(mockHand.handId);
    });

    it('should trigger click on Space key', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      if (card) {
        card.focus();
        await user.keyboard(' ');
      }

      expect(onClick).toHaveBeenCalledWith(mockHand.handId);
    });

    it('should not trigger on other keys', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      if (card) {
        card.focus();
        await user.keyboard('a');
      }

      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe('Focus States', () => {
    it('should be focusable when clickable', () => {
      const onClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      expect(card).toHaveAttribute('tabIndex', '0');
    });

    it('should not be focusable when not clickable', () => {
      render(<HandCard hand={mockHand} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('div');
      expect(card).not.toHaveAttribute('tabIndex');
    });

    it('should handle focus/blur events', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      if (card) {
        await user.click(card);
        card.focus();
        card.blur();
      }

      // Should handle events without errors
      expect(card).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have descriptive aria-label', () => {
      const onClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      expect(card).toHaveAttribute('aria-label');

      const ariaLabel = card?.getAttribute('aria-label') || '';
      expect(ariaLabel).toContain(mockHand.hero_name);
      expect(ariaLabel).toContain(mockHand.villain_name);
    });

    it('should announce pot size in accessibility info', () => {
      const onClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      const ariaLabel = card?.getAttribute('aria-label') || '';
      expect(ariaLabel).toContain(mockHand.pot_bb.toString());
    });

    it('should indicate keyboard interaction in accessibility info', () => {
      const onClick = vi.fn();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      const ariaLabel = card?.getAttribute('aria-label') || '';
      expect(ariaLabel.toLowerCase()).toMatch(/press|enter|space/i);
    });

    it('should be keyboard accessible with tab navigation', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      await user.tab();

      expect(card).toHaveFocus();
    });
  });

  describe('Custom Styling', () => {
    it('should accept custom className', () => {
      const customClass = 'custom-card-class';
      render(
        <HandCard
          hand={mockHand}
          className={customClass}
        />
      );

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[class*="custom"]');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing thumbnail URL gracefully', () => {
      const handWithoutThumb: SearchResultItem = {
        ...mockHand,
        thumbnail_url: '',
      };

      render(<HandCard hand={handWithoutThumb} />);

      const thumbnail = screen.getByTestId('hand-thumbnail');
      expect(thumbnail).toHaveAttribute('src', '');
    });

    it('should handle cards without tags', () => {
      const handWithoutTags: SearchResultItem = {
        ...mockHand,
        tags: [],
      };

      render(<HandCard hand={handWithoutTags} />);

      const tags = screen.getByTestId('hand-tags');
      expect(tags).toBeInTheDocument();
      expect(tags.children.length).toBe(0);
    });

    it('should handle very long player names', () => {
      const longNameHand: SearchResultItem = {
        ...mockHand,
        hero_name: 'A'.repeat(100),
        villain_name: 'B'.repeat(100),
      };

      render(<HandCard hand={longNameHand} />);

      expect(screen.getByTestId('hand-metadata')).toBeInTheDocument();
    });

    it('should handle multiple rapid clicks', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      render(<HandCard hand={mockHand} onClick={onClick} />);

      const card = screen.getByText(/Junglemann vs Phil Ivey/).closest('[role="button"]');
      if (card) {
        await user.click(card);
        await user.click(card);
        await user.click(card);
      }

      expect(onClick).toHaveBeenCalledTimes(3);
    });
  });

  describe('Score Display', () => {
    it('should handle different score ranges', () => {
      const scores = [0, 0.5, 0.95, 1.0];

      scores.forEach(score => {
        const { unmount } = render(
          <HandCard
            hand={{ ...mockHand, score }}
          />
        );

        expect(screen.getByTestId('hand-metadata')).toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('Results Handling', () => {
    it('should display different result types', () => {
      const results: Array<'WIN' | 'LOSE' | 'SPLIT'> = ['WIN', 'LOSE', 'SPLIT'];

      results.forEach(result => {
        const { unmount } = render(
          <HandCard
            hand={{ ...mockHand, result }}
          />
        );

        expect(screen.getByTestId('hand-metadata')).toBeInTheDocument();
        unmount();
      });
    });
  });
});
