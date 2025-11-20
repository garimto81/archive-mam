/**
 * Street Marker Component
 *
 * Displays a single poker street segment on the timeline.
 * Shows street name, duration, and community cards.
 */

import React, { useState } from "react";
import { getStreetLabel, getStreetAbbr } from "@/lib/video/timeline-utils";
import type { Street } from "@/types/hand";

/**
 * StreetMarker Props
 */
export interface StreetMarkerProps {
  /** Poker street type */
  street: Street;

  /** Starting position as percentage (0-100) */
  startPercent: number;

  /** Width as percentage (0-100) */
  widthPercent: number;

  /** Whether this street is currently active */
  isActive: boolean;

  /** Community cards for this street (if applicable) */
  communityCards?: readonly string[];

  /** Callback when street segment is clicked */
  onClick: () => void;

  /** Street background color class */
  color?: string;

  /** Custom CSS class name */
  className?: string;

  /** Show abbreviated street label on mobile */
  mobileCompact?: boolean;

  /** Callback when hover starts */
  onHoverStart?: () => void;

  /** Callback when hover ends */
  onHoverEnd?: () => void;
}

/**
 * StreetMarker Component
 *
 * Displays a colored segment on the timeline representing a poker street.
 * Includes street label, community cards, and interactive hover state.
 *
 * Features:
 * - Street-specific colors (PREFLOP=purple, FLOP=blue, TURN=yellow, RIVER=red)
 * - Shows community cards on hover or when expanded
 * - Keyboard accessible (Enter to activate)
 * - Responsive design (abbreviated labels on mobile)
 * - Active/highlight state
 * - ARIA labels for accessibility
 *
 * @example
 * ```typescript
 * <StreetMarker
 *   street="FLOP"
 *   startPercent={25}
 *   widthPercent={25}
 *   isActive={true}
 *   communityCards={["A♠", "K♥", "Q♦"]}
 *   color="bg-blue-500"
 *   onClick={() => seekToFlop()}
 * />
 * ```
 */
export function StreetMarker({
  street,
  startPercent,
  widthPercent,
  isActive,
  communityCards,
  onClick,
  color = "bg-gray-500",
  className,
  mobileCompact = true,
  onHoverStart,
  onHoverEnd,
}: StreetMarkerProps): React.ReactElement {
  const [isHovering, setIsHovering] = useState(false);
  const [showCards, setShowCards] = useState(false);

  const handleMouseEnter = () => {
    setIsHovering(true);
    onHoverStart?.();
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    onHoverEnd?.();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  };

  const streetLabel = getStreetLabel(street);
  const streetAbbr = getStreetAbbr(street);
  const hasCommunityCards = communityCards && communityCards.length > 0;

  return (
    <div
      className={`
        absolute
        h-full
        transition-all
        duration-200
        cursor-pointer
        group
        ${className || ""}
      `}
      style={{
        left: `${startPercent}%`,
        width: `${widthPercent}%`,
      }}
      role="button"
      tabIndex={0}
      aria-label={`${streetLabel}${hasCommunityCards ? `: ${communityCards.join(" ")}` : ""}`}
      aria-pressed={isActive}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Street segment background */}
      <div
        className={`
          h-full
          relative
          transition-all
          duration-200
          border-l
          border-r
          border-white/30
          ${color}
          ${isActive ? "opacity-100 shadow-lg" : "opacity-70 hover:opacity-85"}
          ${isHovering ? "shadow-md" : ""}
        `}
      >
        {/* Street label overlay */}
        <div
          className={`
            h-full
            flex
            flex-col
            items-center
            justify-center
            gap-0.5
            px-1
            transition-all
            duration-200
            text-white
          `}
        >
          {/* Desktop label (full name) */}
          <div
            className={`
              hidden
              sm:block
              text-xs
              font-bold
              tracking-wide
              text-white/90
              drop-shadow-sm
            `}
          >
            {streetLabel}
          </div>

          {/* Mobile label (abbreviation) */}
          {mobileCompact && (
            <div
              className={`
                sm:hidden
                text-xs
                font-bold
                text-white/90
                drop-shadow-sm
              `}
            >
              {streetAbbr}
            </div>
          )}

          {/* Community cards indicator */}
          {hasCommunityCards && (
            <div
              className="
                text-xs
                font-mono
                text-white/80
                drop-shadow-sm
                text-center
                leading-tight
              "
            >
              {communityCards.slice(0, 2).map((card) => card[0]).join("")}
            </div>
          )}
        </div>

        {/* Hover highlight */}
        {isHovering && (
          <div
            className="
              absolute
              inset-0
              bg-white/10
              pointer-events-none
            "
            aria-hidden="true"
          />
        )}

        {/* Active indicator (bottom bar) */}
        {isActive && (
          <div
            className="
              absolute
              bottom-0
              left-0
              right-0
              h-1
              bg-white
              shadow-lg
            "
            aria-hidden="true"
          />
        )}
      </div>

      {/* Community cards tooltip/popup */}
      {hasCommunityCards && (isHovering || showCards) && (
        <div
          className={`
            absolute
            z-10
            left-1/2
            transform
            -translate-x-1/2
            top-full
            mt-1
            bg-gray-900
            border
            border-gray-700
            rounded-lg
            px-2
            py-1
            backdrop-blur-sm
            pointer-events-none
            whitespace-nowrap
            text-xs
            font-mono
            font-semibold
            text-amber-300
            drop-shadow-lg
          `}
          role="tooltip"
        >
          <div className="flex gap-1">
            {communityCards.map((card, idx) => (
              <div
                key={idx}
                className="
                  px-1.5
                  py-0.5
                  rounded
                  bg-gray-800
                  border
                  border-gray-600
                "
              >
                {card}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default StreetMarker;
