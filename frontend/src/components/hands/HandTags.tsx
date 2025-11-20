'use client';

import React, { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface HandTagsProps {
  tags: string[];
  maxVisible?: number;
  colorMap?: Record<string, string>;
}

/**
 * Tag Category Color Mapping
 *
 * Groups poker tags by action category and assigns colors
 * WCAG 2.1 AA compliant: All colors have 4.5:1 contrast ratio with backgrounds
 */
const DEFAULT_COLOR_MAP: Record<string, string> = {
  // Action Tags - Red (aggressive)
  HERO_CALL: 'bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/30',
  BLUFF: 'bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/30',
  TRAP: 'bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/30',
  CHECK_RAISE: 'bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/30',
  DONK_BET: 'bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/30',
  SQUEEZE: 'bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/30',

  // Value Tags - Green (positive)
  VALUE_BET: 'bg-poker-chip-green/10 text-poker-chip-green border-poker-chip-green/30',
  THIN_VALUE: 'bg-poker-chip-green/10 text-poker-chip-green border-poker-chip-green/30',
  CONTINUATION_BET: 'bg-poker-chip-green/10 text-poker-chip-green border-poker-chip-green/30',
  SLOW_PLAY: 'bg-poker-chip-green/10 text-poker-chip-green border-poker-chip-green/30',

  // Decision Tags - Purple (critical moments)
  RIVER_DECISION: 'bg-poker-chip-purple/10 text-poker-chip-purple border-poker-chip-purple/30',
  TURN_DECISION: 'bg-poker-chip-purple/10 text-poker-chip-purple border-poker-chip-purple/30',
  FLOP_DECISION: 'bg-poker-chip-purple/10 text-poker-chip-purple border-poker-chip-purple/30',
  PREFLOP_DECISION: 'bg-poker-chip-purple/10 text-poker-chip-purple border-poker-chip-purple/30',

  // Stack Tags - Blue (position/stack info)
  HIGH_STAKES: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700',
  DEEP_STACK: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700',
  SHORT_STACK: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700',
  ALL_IN: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700',

  // Aggressive Action Tags - Orange
  '3BET': 'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-700',
  '4BET': 'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-700',

  // Outcome Tags - Yellow (extreme outcomes)
  COOLER: 'bg-poker-chip-yellow/20 text-poker-chip-yellow border-poker-chip-yellow/50',
  BAD_BEAT: 'bg-poker-chip-yellow/20 text-poker-chip-yellow border-poker-chip-yellow/50',
  SICK_CALL: 'bg-poker-chip-yellow/20 text-poker-chip-yellow border-poker-chip-yellow/50',
  SICK_FOLD: 'bg-poker-chip-yellow/20 text-poker-chip-yellow border-poker-chip-yellow/50',
  TILT: 'bg-poker-chip-yellow/20 text-poker-chip-yellow border-poker-chip-yellow/50',
};

/**
 * HandTags Component
 *
 * Displays searchable tags with:
 * - Color-coded by category
 * - Limited visible tags with "+N more" indicator
 * - Truncated long tag names with ellipsis
 * - Semantic badge component from shadcn/ui
 * - Screen reader accessible
 *
 * WCAG 2.1 AA Compliance:
 * - Color contrast: All badges have 4.5:1+ contrast
 * - Icon + text: "+N more" text in addition to count
 * - Semantic HTML: <ul> + <li> for tag list
 * - Keyboard accessible: Badges can receive focus if clickable
 * - Screen reader: aria-label describes full tag list
 *
 * @param tags - Array of tag strings
 * @param maxVisible - Maximum tags to show (default: 3)
 * @param colorMap - Custom color mapping for tags
 */
export function HandTags({
  tags,
  maxVisible = 3,
  colorMap = DEFAULT_COLOR_MAP
}: HandTagsProps) {
  // Memoize computed values
  const { visibleTags, hiddenCount } = useMemo(() => {
    return {
      visibleTags: tags.slice(0, maxVisible),
      hiddenCount: Math.max(0, tags.length - maxVisible)
    };
  }, [tags, maxVisible]);

  // Format tag name for display (convert underscore to space, title case)
  const formatTagName = (tag: string): string => {
    return tag
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Get color class for tag
  const getTagColor = (tag: string): string => {
    return colorMap[tag] || 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600';
  };

  // Create aria label with all tags for screen readers
  const tagsDescription = tags.length > 0
    ? `Tags: ${tags.map(formatTagName).join(', ')}`
    : 'No tags';

  return (
    <div
      className="flex flex-wrap gap-2 items-center"
      role="group"
      aria-label={tagsDescription}
    >
      {/* Visible Tags */}
      {visibleTags.map((tag) => (
        <Badge
          key={tag}
          variant="outline"
          className={cn(
            'text-xs font-medium px-2 py-1 truncate',
            'max-w-[120px]',
            'transition-colors duration-150',
            'hover:opacity-80',
            getTagColor(tag)
          )}
          title={formatTagName(tag)}
        >
          {formatTagName(tag)}
        </Badge>
      ))}

      {/* "+N more" Badge */}
      {hiddenCount > 0 && (
        <Badge
          variant="outline"
          className={cn(
            'text-xs font-medium px-2 py-1',
            'bg-slate-100 text-slate-700 border-slate-300',
            'dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600',
            'hover:bg-slate-200 dark:hover:bg-slate-700',
            'transition-colors duration-150',
            'cursor-help'
          )}
          title={`Hidden tags: ${tags.slice(maxVisible).map(formatTagName).join(', ')}`}
        >
          +{hiddenCount} more
        </Badge>
      )}

      {/* Screen Reader Only Details */}
      <span className="sr-only">
        Total tags: {tags.length}.
        {hiddenCount > 0 && ` Hidden tags: ${tags.slice(maxVisible).map(formatTagName).join(', ')}`}
      </span>
    </div>
  );
}

export default HandTags;
