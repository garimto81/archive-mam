"use client";

import React, { useEffect, useRef } from "react";
import { Sparkles } from "lucide-react";
import { highlightMatch } from "@/lib/utils/highlight";
import { cn } from "@/lib/utils";
import type { Suggestion } from "@/types";

interface SuggestionItemProps {
  id: string;
  suggestion: Suggestion;
  query: string;
  isSelected: boolean;
  onClick: () => void;
  onMouseEnter: () => void;
}

/**
 * Autocomplete Suggestion Item Component
 *
 * Displays a single suggestion item in the autocomplete dropdown.
 * Handles keyboard navigation, highlighting, and typo correction indicators.
 *
 * Features:
 * - Auto-scroll into view when selected
 * - Query text highlighting
 * - Typo correction indicator
 * - Touch-friendly target size
 * - ARIA attributes for accessibility
 *
 * @example
 * ```tsx
 * <SuggestionItem
 *   id="suggestion-0"
 *   suggestion={{ text: "Junglemann", isTypoCorrected: false }}
 *   query="jung"
 *   isSelected={true}
 *   onClick={() => handleSelect(suggestion)}
 *   onMouseEnter={() => setSelectedIndex(0)}
 * />
 * ```
 */
export function SuggestionItem({
  id,
  suggestion,
  query,
  isSelected,
  onClick,
  onMouseEnter
}: SuggestionItemProps) {
  const itemRef = useRef<HTMLDivElement>(null);

  // Auto scroll into view when selected
  useEffect(() => {
    if (isSelected && itemRef.current) {
      itemRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
      });
    }
  }, [isSelected]);

  return (
    <div
      ref={itemRef}
      id={id}
      role="option"
      aria-selected={isSelected}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors",
        "min-h-[44px] sm:min-h-[40px]", // Touch target size (WCAG 2.1)
        isSelected
          ? "bg-accent text-accent-foreground"
          : "hover:bg-muted"
      )}
    >
      {suggestion.isTypoCorrected && (
        <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0" aria-label="Typo corrected" />
      )}

      <span className="text-sm">
        {highlightMatch(suggestion.text, query)}
      </span>
    </div>
  );
}
