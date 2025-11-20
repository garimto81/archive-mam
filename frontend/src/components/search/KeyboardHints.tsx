"use client";

import React from "react";

/**
 * Keyboard Navigation Hints Component
 *
 * Displays keyboard shortcuts for autocomplete navigation.
 * Shows in the footer of the autocomplete dropdown.
 *
 * @example
 * ```tsx
 * <KeyboardHints />
 * ```
 */
export function KeyboardHints() {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
      <span>↑↓ Navigate</span>
      <span>•</span>
      <span>Enter Select</span>
      <span>•</span>
      <span>Esc Close</span>
    </div>
  );
}
