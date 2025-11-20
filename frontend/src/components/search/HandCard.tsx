"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { VideoPreviewThumbnail } from "@/components/video/VideoPreviewThumbnail";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ProgressBar } from "@/components/status/ProgressBar";
import type { SearchResultItem } from "@/types/search";

interface HandCardProps {
  /** Search result item to display */
  result: SearchResultItem;

  /** Callback when card is clicked */
  onClick?: () => void;

  /** Custom CSS class name */
  className?: string;
}

/**
 * Hand Card Component
 *
 * Displays a single poker hand search result as a card.
 *
 * Features:
 * - Thumbnail image
 * - Player names and positions
 * - Pot size and street
 * - Classification tags
 * - Relevance score
 * - Result indicator (WIN/LOSE/SPLIT)
 * - Click handling for navigation
 * - Hover effects and animations
 *
 * @example
 * ```tsx
 * <HandCard
 *   result={searchResult}
 *   onClick={() => router.push(`/hands/${searchResult.handId}`)}
 * />
 * ```
 */
export function HandCard({
  result,
  onClick,
  className
}: HandCardProps) {
  /**
   * Get result color indicator
   */
  const getResultColor = (result: SearchResultItem["result"]) => {
    switch (result) {
      case "WIN":
        return "bg-green-500/10 text-green-600 border-green-500/20";
      case "LOSE":
        return "bg-red-500/10 text-red-600 border-red-500/20";
      case "SPLIT":
        return "bg-yellow-500/10 text-yellow-600 border-yellow-500/20";
      default:
        return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    }
  };

  /**
   * Get relevance badge color
   */
  const getRelevanceColor = (score: number) => {
    if (score >= 0.9) return "bg-poker-chip-green/10 text-poker-chip-green border-poker-chip-green/20";
    if (score >= 0.8) return "bg-poker-chip-purple/10 text-poker-chip-purple border-poker-chip-purple/20";
    if (score >= 0.7) return "bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/20";
    return "bg-muted text-muted-foreground border-border";
  };

  return (
    <article
      onClick={onClick}
      data-testid="hand-card"
      className={cn(
        "w-full h-full text-left cursor-pointer",
        "rounded-lg border border-border bg-card",
        "overflow-hidden transition-all duration-300",
        "hover:border-poker-chip-green hover:shadow-lg hover:shadow-poker-chip-green/20",
        "focus:outline-none focus:ring-2 focus:ring-poker-chip-green focus:ring-offset-2",
        "group",
        className
      )}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
      aria-label={`Hand ${result.handId} - ${result.hero_name} vs ${result.villain_name}`}
    >
      {/* Thumbnail section with video preview */}
      <div
        className="relative w-full aspect-video bg-gradient-to-br from-muted to-muted/50 overflow-hidden"
        data-testid="hand-thumbnail"
      >
        {/* Video preview with hover */}
        <VideoPreviewThumbnail
          handId={result.handId}
          videoUrl={result.videoUrl}
          thumbnailUrl={result.thumbnail_url}
          startTime={0}
          endTime={result.durationSeconds}
          hoverDelay={300}
        />

        {/* Relevance score badge */}
        {result.score !== undefined && (
          <div className="absolute top-2 right-2 z-10">
            <Badge
              className={cn(
                "border font-semibold text-xs",
                getRelevanceColor(result.score)
              )}
            >
              {(result.score * 100).toFixed(0)}%
            </Badge>
          </div>
        )}

        {/* Result indicator */}
        <div className="absolute top-2 left-2 z-10">
          <Badge
            className={cn(
              "border font-semibold text-xs",
              getResultColor(result.result)
            )}
          >
            {result.result}
          </Badge>
        </div>

        {/* Analysis status badge */}
        {result.analysisStatus && (
          <div className="absolute bottom-2 left-2 z-10">
            <StatusBadge
              status={result.analysisStatus}
              progress={result.analysisProgress}
              error={result.analysisError}
              compact={true}
            />
          </div>
        )}

        {/* Progress bar for processing status */}
        {result.analysisStatus === 'processing' && result.analysisProgress !== undefined && (
          <div className="absolute bottom-10 left-2 right-2 z-10">
            <ProgressBar
              value={result.analysisProgress}
              variant="processing"
              size="sm"
              animated={true}
            />
          </div>
        )}
      </div>

      {/* Content section */}
      <div className="p-4 space-y-3" data-testid="hand-metadata">
        {/* Players section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-foreground">
                {result.hero_name}
              </p>
              <p className="text-xs text-muted-foreground">Hero</p>
            </div>
            <div className="h-0.5 flex-1 bg-border" />
            <div className="text-right">
              <p className="text-sm font-semibold text-foreground">
                {result.villain_name}
              </p>
              <p className="text-xs text-muted-foreground">Villain</p>
            </div>
          </div>
        </div>

        {/* Hand details */}
        <div className="grid grid-cols-2 gap-3 py-2 border-t border-b border-border">
          <div>
            <p className="text-xs text-muted-foreground">Pot Size</p>
            <p className="text-sm font-semibold">
              {result.pot_bb !== undefined ? `${result.pot_bb.toFixed(1)}bb` : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Street</p>
            <p className="text-sm font-semibold">{result.street || 'N/A'}</p>
          </div>
        </div>

        {/* Tags section */}
        {result.tags && result.tags.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-muted-foreground">Tags</p>
            <div className="flex flex-wrap gap-1">
              {result.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {result.tags.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{result.tags.length - 3}
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* View indicator - removed button to fix nested button issue */}
        <div
          className={cn(
            "w-full mt-2 text-center py-2 px-4 rounded-md",
            "bg-poker-chip-green/10 text-poker-chip-green",
            "text-sm font-semibold",
            "group-hover:bg-poker-chip-green group-hover:text-white",
            "transition-colors duration-200"
          )}
        >
          Click to View Hand Details
        </div>
      </div>
    </article>
  );
}
