/**
 * Text Highlighting Utilities
 *
 * Provides functions to highlight matching text in suggestions.
 * Used by autocomplete components to visually indicate query matches.
 */

import React from "react";

/**
 * Highlights matching portions of text based on a query
 *
 * @param text - The full text to highlight
 * @param query - The search query to match
 * @returns React element with highlighted matches
 *
 * @example
 * ```tsx
 * highlightMatch("Junglemann bluff", "jung")
 * // Returns: <span><strong>Jung</strong>lemann bluff</span>
 * ```
 */
export function highlightMatch(text: string, query: string): React.ReactElement {
  if (!query || !text) {
    return <>{text}</>;
  }

  // Escape special regex characters in query
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  // Case-insensitive match
  const regex = new RegExp(`(${escapedQuery})`, "gi");

  const parts = text.split(regex);

  return (
    <>
      {parts.map((part, index) => {
        const isMatch = regex.test(part);

        // Reset regex lastIndex for next iteration
        regex.lastIndex = 0;

        if (isMatch) {
          return (
            <strong key={index} className="font-semibold text-foreground">
              {part}
            </strong>
          );
        }

        return <span key={index}>{part}</span>;
      })}
    </>
  );
}

/**
 * Gets the first matching portion of text
 *
 * @param text - The full text
 * @param query - The search query
 * @returns The matched portion or empty string
 */
export function getMatchedPortion(text: string, query: string): string {
  if (!query || !text) {
    return "";
  }

  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(escapedQuery, "i");
  const match = text.match(regex);

  return match ? match[0] : "";
}

/**
 * Calculates match score based on position and coverage
 *
 * @param text - The full text
 * @param query - The search query
 * @returns Score from 0 to 1
 */
export function calculateMatchScore(text: string, query: string): number {
  if (!query || !text) {
    return 0;
  }

  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();

  // Exact match gets highest score
  if (lowerText === lowerQuery) {
    return 1.0;
  }

  // Starts with query gets high score
  if (lowerText.startsWith(lowerQuery)) {
    return 0.9;
  }

  // Contains query gets medium score
  if (lowerText.includes(lowerQuery)) {
    const position = lowerText.indexOf(lowerQuery);
    const coverage = lowerQuery.length / lowerText.length;

    // Earlier position and higher coverage = better score
    const positionScore = 1 - (position / lowerText.length);
    const coverageScore = coverage;

    return (positionScore * 0.4 + coverageScore * 0.6) * 0.7;
  }

  return 0;
}
