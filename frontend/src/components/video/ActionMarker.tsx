/**
 * Action Marker Component
 *
 * Displays a single action marker on the timeline.
 * Shows small dots/icons at specific timestamps indicating poker actions.
 */

import React, { useState } from "react";
import { formatAction } from "@/lib/video/timeline-utils";
import type { Action } from "@/types/hand";

/**
 * ActionMarker Props
 */
export interface ActionMarkerProps {
  /** Action that this marker represents */
  action: Action;

  /** Horizontal position as percentage (0-100) */
  position: number;

  /** Whether this marker is currently active/highlighted */
  isActive: boolean;

  /** Callback when marker is clicked */
  onClick: () => void;

  /** Tailwind color class for the marker */
  color?: string;

  /** Custom CSS class name */
  className?: string;

  /** Show tooltip on hover */
  showTooltip?: boolean;

  /** Callback when hover starts */
  onHoverStart?: () => void;

  /** Callback when hover ends */
  onHoverEnd?: () => void;
}

/**
 * Get icon for action type
 *
 * @param actionType - Type of action
 * @returns SVG icon path
 */
function getActionIcon(actionType: string): string {
  const type = actionType.toUpperCase();
  switch (type) {
    case "FOLD":
      return "M8 12L12 8M12 8L8 4"; // X
    case "CHECK":
      return "M4 8L8 12L16 4"; // Checkmark
    case "CALL":
      return "M6 8C6 5.239 8.239 3 11 3C13.761 3 16 5.239 16 8"; // Arc
    case "RAISE":
      return "M8 4V16M4 8H12"; // Plus
    case "BET":
      return "M8 4V16M4 8H12"; // Plus (same as raise)
    case "ALL_IN":
      return "M8 2V14M2 8H14M5 5L11 11M11 5L5 11"; // X with circle
    default:
      return "M8 8m-6 0a6 6 0 1 0 12 0a6 6 0 1 0 -12 0"; // Circle
  }
}

/**
 * Get size for action type marker
 *
 * @param actionType - Type of action
 * @returns Size in pixels
 */
function getMarkerSize(actionType: string): number {
  const type = actionType.toUpperCase();
  switch (type) {
    case "ALL_IN":
      return 10;
    case "RAISE":
      return 8;
    default:
      return 6;
  }
}

/**
 * ActionMarker Component
 *
 * Displays a clickable marker on the timeline indicating a poker action.
 * Supports different colors and sizes based on action type.
 *
 * Features:
 * - Color-coded by action type (fold=red, call=green, raise=orange, etc.)
 * - Animated on hover/active state
 * - Displays action details on hover
 * - Keyboard accessible (Enter to activate)
 * - ARIA labels for screen readers
 *
 * @example
 * ```typescript
 * <ActionMarker
 *   action={{ player: "hero", actionType: "RAISE", amount: 25, timestamp: 15.5 }}
 *   position={42.5}
 *   isActive={false}
 *   color="bg-orange-500"
 *   onClick={() => seekTo(15.5)}
 *   onHoverStart={() => showTooltip()}
 *   onHoverEnd={() => hideTooltip()}
 * />
 * ```
 */
export function ActionMarker({
  action,
  position,
  isActive,
  onClick,
  color = "bg-gray-400",
  className,
  showTooltip = true,
  onHoverStart,
  onHoverEnd,
}: ActionMarkerProps): React.ReactElement {
  const [isHovering, setIsHovering] = useState(false);

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

  const markerSize = getMarkerSize(action.actionType);
  const ariaLabel = formatAction(action);

  return (
    <div
      className={`absolute top-1/2 transform -translate-y-1/2 -translate-x-1/2 cursor-pointer flex items-center justify-center transition-all duration-150 ${className || ""}`}
      style={{
        left: `${position}%`,
        width: `${Math.max(20, markerSize * 3)}px`,
        height: `${Math.max(20, markerSize * 3)}px`,
      }}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel}
      aria-pressed={isActive}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Hover/Active ring */}
      {(isHovering || isActive) && (
        <div
          className={`absolute inset-0 rounded-full border-2 border-current opacity-50 scale-150 ${color}`}
          aria-hidden="true"
        />
      )}

      {/* Main marker dot */}
      <div
        className={`
          rounded-full
          transition-all
          duration-150
          ${color}
          ${isActive ? "shadow-lg scale-125" : "shadow"}
          ${isHovering ? "scale-110" : "scale-100"}
        `}
        style={{
          width: `${markerSize}px`,
          height: `${markerSize}px`,
        }}
        aria-hidden="true"
      />

      {/* Tooltip hint */}
      {showTooltip && isHovering && (
        <div
          className="
            absolute
            bottom-full
            mb-2
            left-1/2
            transform
            -translate-x-1/2
            whitespace-nowrap
            text-xs
            font-semibold
            text-white
            bg-gray-900
            px-2
            py-1
            rounded
            pointer-events-none
            border
            border-gray-700
          "
          role="tooltip"
        >
          {ariaLabel}
        </div>
      )}
    </div>
  );
}

export default ActionMarker;
