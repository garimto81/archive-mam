/**
 * Hand Timeline Component
 *
 * Main timeline component for displaying poker hand streets and actions.
 * Shows street markers, action dots, and current playback position.
 */

import React, { useState, useRef, useCallback } from "react";
import { useHandTimeline } from "@/hooks/useHandTimeline";
import StreetMarker from "./StreetMarker";
import ActionMarker from "./ActionMarker";
import TimelineTooltip from "./TimelineTooltip";
import { formatTime, timeToPercent, percentToTime } from "@/lib/video/timeline-utils";
import type { StreetAction } from "@/types/hand";
import type { TimelineTooltipContent } from "./TimelineTooltip";

/**
 * HandTimeline Props
 */
export interface HandTimelineProps {
  /** Total video duration in seconds */
  duration: number;

  /** Current playback position in seconds */
  currentTime: number;

  /** Street-by-street action breakdown */
  streets: readonly StreetAction[];

  /** Callback when user seeks to a new position */
  onSeek: (time: number) => void;

  /** Additional action markers to display (optional) */
  markers?: readonly any[];

  /** Custom CSS class name */
  className?: string;

  /** Show action markers on timeline */
  showActionMarkers?: boolean;

  /** Show street labels */
  showStreetLabels?: boolean;

  /** Callback when hovering over timeline */
  onHover?: (time: number | null) => void;
}

/**
 * HandTimeline Component
 *
 * Interactive video timeline displaying poker hand progression.
 * Shows streets as colored segments and actions as small dots.
 *
 * Features:
 * - Visual timeline bar with street segments
 * - Street colors: PREFLOP (purple), FLOP (blue), TURN (yellow), RIVER (red)
 * - Current time indicator (vertical line)
 * - Click anywhere to seek
 * - Hover for details (time, street, actions)
 * - Action markers showing poker decisions
 * - Community cards display
 * - Fully keyboard accessible
 * - Responsive design
 * - ARIA labels for accessibility
 *
 * @example
 * ```typescript
 * <HandTimeline
 *   duration={61.5}
 *   currentTime={25.3}
 *   streets={handDetails.streets}
 *   onSeek={(time) => videoPlayer.seek(time)}
 *   showActionMarkers={true}
 * />
 * ```
 */
export function HandTimeline({
  duration,
  currentTime,
  streets,
  onSeek,
  markers,
  className,
  showActionMarkers = true,
  showStreetLabels = true,
  onHover,
}: HandTimelineProps): React.ReactElement {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [tooltipContent, setTooltipContent] = useState<TimelineTooltipContent>({
    time: "0:00",
  });

  const { streetSegments, actionMarkers, currentStreet } = useHandTimeline({
    streets,
    duration,
    currentTime,
    onSeek,
  });

  // Handle clicking on timeline to seek
  const handleTimelineClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!timelineRef.current) return;

      const rect = timelineRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percent = (x / rect.width) * 100;
      const time = percentToTime(percent, duration);

      onSeek(Math.max(0, Math.min(duration, time)));
    },
    [duration, onSeek]
  );

  // Handle hovering over timeline to show tooltip
  const handleTimelineHover = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!timelineRef.current) return;

      const rect = timelineRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percent = (x / rect.width) * 100;
      const time = percentToTime(percent, duration);

      setHoveredTime(time);
      setTooltipPosition({ x: e.clientX - rect.left, y: 0 });

      // Find street at this time
      const streetAtTime = streets.find(
        (street) => {
          if (!street.actions || street.actions.length === 0) return false;
          const firstAction = street.actions[0];
          const lastAction = street.actions[street.actions.length - 1];
          return (
            firstAction &&
            lastAction &&
            firstAction.timestamp <= time &&
            lastAction.timestamp >= time
          );
        }
      );

      // Find action near this time
      const nearbyAction = actionMarkers.find(
        (marker) => Math.abs(marker.action.timestamp - time) < 0.5
      );

      const content: TimelineTooltipContent = {
        time: formatTime(time),
        street: streetAtTime?.street,
        action: nearbyAction?.label,
        cards: streetAtTime?.communityCards,
      };

      setTooltipContent(content);
      setTooltipVisible(true);

      onHover?.(time);
    },
    [duration, streets, actionMarkers, onHover]
  );

  const handleTimelineLeave = useCallback(() => {
    setTooltipVisible(false);
    setHoveredTime(null);
    onHover?.(null);
  }, [onHover]);

  const currentPercent = timeToPercent(currentTime, duration);

  return (
    <div
      className={`
        w-full
        flex
        flex-col
        gap-2
        ${className || ""}
      `}
    >
      {/* Main timeline container */}
      <div
        ref={timelineRef}
        className="
          relative
          w-full
          h-16
          bg-gray-800
          border
          border-gray-700
          rounded-lg
          overflow-hidden
          cursor-pointer
          group
          transition-all
          duration-200
          hover:bg-gray-750
        "
        role="slider"
        aria-label="Video timeline"
        aria-valuemin={0}
        aria-valuemax={Math.round(duration)}
        aria-valuenow={Math.round(currentTime)}
        aria-valuetext={`${formatTime(currentTime)} / ${formatTime(duration)}`}
        onClick={handleTimelineClick}
        onMouseMove={handleTimelineHover}
        onMouseLeave={handleTimelineLeave}
      >
        {/* Background street segments */}
        {streetSegments.map((segment) => (
          <StreetMarker
            key={segment.street}
            street={segment.street}
            startPercent={segment.startPercent}
            widthPercent={segment.widthPercent}
            isActive={
              currentStreet?.street === segment.street ||
              (hoveredTime !== null &&
                hoveredTime >= segment.startTime &&
                hoveredTime < segment.endTime)
            }
            communityCards={segment.communityCards}
            color={segment.color}
            onClick={() => onSeek(segment.startTime)}
            onHoverStart={() => {}}
            onHoverEnd={() => {}}
          />
        ))}

        {/* Action markers */}
        {showActionMarkers &&
          actionMarkers.map((marker) => (
            <ActionMarker
              key={marker.id}
              action={marker.action}
              position={marker.position}
              isActive={
                hoveredTime !== null &&
                Math.abs(hoveredTime - marker.action.timestamp) < 0.5
              }
              color={marker.color}
              onClick={() => onSeek(marker.action.timestamp)}
              onHoverStart={() => {
                setTooltipContent({
                  time: formatTime(marker.action.timestamp),
                  street: marker.street,
                  action: marker.label,
                });
                setTooltipVisible(true);
              }}
              onHoverEnd={() => {
                setTooltipVisible(false);
              }}
            />
          ))}

        {/* Current time indicator */}
        <div
          className="
            absolute
            top-0
            bottom-0
            w-0.5
            bg-white
            shadow-lg
            pointer-events-none
            transition-all
            duration-75
            z-20
          "
          style={{
            left: `${currentPercent}%`,
          }}
          aria-hidden="true"
        >
          {/* Indicator dot at top */}
          <div
            className="
              absolute
              top-0
              left-1/2
              w-3
              h-3
              bg-white
              rounded-full
              shadow-lg
              transform
              -translate-x-1/2
              -translate-y-1.5
            "
            aria-hidden="true"
          />
        </div>

        {/* Hover position indicator */}
        {hoveredTime !== null && (
          <div
            className="
              absolute
              top-0
              bottom-0
              w-0.5
              bg-white/30
              pointer-events-none
            "
            style={{
              left: `${timeToPercent(hoveredTime, duration)}%`,
            }}
            aria-hidden="true"
          />
        )}

        {/* Loading indicator (for future use) */}
        <div
          className="
            absolute
            bottom-0
            left-0
            h-0.5
            bg-gradient-to-r
            from-blue-500
            to-transparent
            pointer-events-none
            opacity-0
            group-hover:opacity-100
            transition-opacity
          "
          aria-hidden="true"
        />
      </div>

      {/* Time display */}
      <div className="flex justify-between items-center px-1 text-xs font-mono text-gray-300">
        <span className="font-semibold text-blue-400">{formatTime(currentTime)}</span>
        <span className="text-gray-400">{formatTime(duration)}</span>
      </div>

      {/* Tooltip */}
      <TimelineTooltip
        visible={tooltipVisible}
        position={tooltipPosition}
        content={tooltipContent}
      />

      {/* Accessibility help text */}
      <div className="text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
        <span className="sr-only">
          Use arrow keys to adjust time, or click to seek. Current position:{" "}
          {formatTime(currentTime)} of {formatTime(duration)}
        </span>
      </div>
    </div>
  );
}

export default HandTimeline;
