/**
 * Timeline Tooltip Component
 *
 * Floating tooltip for displaying details about timeline positions and actions.
 * Shows street information, action details, and community cards on hover.
 */

import React from "react";
import { formatTime } from "@/lib/video/timeline-utils";

/**
 * Tooltip content structure
 */
export interface TimelineTooltipContent {
  /** Formatted time display (e.g., "1:23") */
  time: string;

  /** Street name (PREFLOP, FLOP, etc.) */
  street?: string;

  /** Action description (e.g., "Hero raises 3.5 BB") */
  action?: string;

  /** Community cards as array (e.g., ["A♠", "K♥", "Q♦"]) */
  cards?: readonly string[];
}

/**
 * Tooltip position
 */
export interface TooltipPosition {
  /** X position in pixels */
  x: number;

  /** Y position in pixels */
  y: number;
}

/**
 * TimelineTooltip Props
 */
export interface TimelineTooltipProps {
  /** Whether tooltip is visible */
  visible: boolean;

  /** Tooltip position on screen */
  position: TooltipPosition;

  /** Content to display in tooltip */
  content: TimelineTooltipContent;

  /** Custom CSS class name */
  className?: string;
}

/**
 * TimelineTooltip Component
 *
 * Displays a floating tooltip near the mouse cursor with timeline information.
 * Shows time, street, action details, and community cards.
 *
 * Features:
 * - Smooth fade in/out animations
 * - Smart positioning (prevents off-screen)
 * - Displays street and action details
 * - Shows community cards in card format
 * - Accessible with proper ARIA attributes
 *
 * @example
 * ```typescript
 * <TimelineTooltip
 *   visible={isHovering}
 *   position={{ x: 150, y: 50 }}
 *   content={{
 *     time: "1:23",
 *     street: "FLOP",
 *     action: "Hero checks",
 *     cards: ["A♠", "K♥", "Q♦"]
 *   }}
 * />
 * ```
 */
export function TimelineTooltip({
  visible,
  position,
  content,
  className,
}: TimelineTooltipProps): React.ReactElement | null {
  if (!visible) {
    return null;
  }

  return (
    <div
      role="tooltip"
      className={`
        fixed
        z-50
        pointer-events-none
        transition-all
        duration-150
        ease-out
        ${visible ? "opacity-100" : "opacity-0"}
        ${className || ""}
      `}
      style={{
        left: `${Math.min(position.x, typeof window !== "undefined" ? window.innerWidth - 200 : position.x)}px`,
        top: `${Math.max(position.y - 80, 10)}px`,
      }}
      aria-hidden={!visible}
    >
      {/* Tooltip background */}
      <div
        className="
          bg-gray-900
          text-white
          rounded-lg
          shadow-lg
          px-3
          py-2
          text-sm
          max-w-xs
          border
          border-gray-700
          backdrop-blur-sm
        "
      >
        {/* Time display */}
        <div className="font-mono font-semibold text-blue-300 mb-1">
          {content.time}
        </div>

        {/* Street display */}
        {content.street && (
          <div className="text-xs text-gray-300 mb-1">
            <span className="font-semibold">{content.street}</span>
          </div>
        )}

        {/* Action display */}
        {content.action && (
          <div className="text-xs text-gray-200 mb-1">{content.action}</div>
        )}

        {/* Community cards */}
        {content.cards && content.cards.length > 0 && (
          <div className="flex gap-1 mt-2 pt-1 border-t border-gray-700">
            {content.cards.map((card, idx) => (
              <div
                key={idx}
                className="
                  text-xs
                  font-mono
                  font-semibold
                  px-1.5
                  py-0.5
                  rounded
                  bg-gray-800
                  text-amber-300
                  border
                  border-gray-600
                "
              >
                {card}
              </div>
            ))}
          </div>
        )}

        {/* Tooltip arrow */}
        <div
          className="
            absolute
            top-full
            left-4
            w-2
            h-2
            bg-gray-900
            border-r
            border-b
            border-gray-700
            transform
            rotate-45
            -translate-y-1
          "
          aria-hidden="true"
        />
      </div>
    </div>
  );
}

export default TimelineTooltip;
