"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

/**
 * Props for FilterSection component
 */
interface FilterSectionProps {
  /** Section title */
  title: string;

  /** Optional icon to display before title */
  icon?: React.ReactNode;

  /** Section content (filter controls) */
  children: React.ReactNode;

  /** Whether section should be open by default (default: false) */
  defaultOpen?: boolean;

  /** Optional badge count to show active filters in this section */
  badge?: number;

  /** Custom CSS class name */
  className?: string;
}

/**
 * Filter Section Component
 *
 * Collapsible section for organizing filter controls within FilterPanel.
 * Uses smooth accordion animation and keyboard accessibility.
 *
 * Features:
 * - Collapsible with chevron icon animation
 * - Badge count for active filters in section
 * - Keyboard accessible (Enter/Space to toggle)
 * - Smooth height animation
 * - Optional icon support
 *
 * @example
 * ```tsx
 * <FilterSection
 *   title="Pot Size (BB)"
 *   defaultOpen={true}
 *   badge={1}
 * >
 *   <RangeSlider min={0} max={500} />
 * </FilterSection>
 * ```
 */
export function FilterSection({
  title,
  icon,
  children,
  defaultOpen = false,
  badge,
  className
}: FilterSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setIsOpen(!isOpen);
    }
  };

  return (
    <div className={cn("border border-gray-200 rounded-lg overflow-hidden", className)}>
      {/* Header / Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
        aria-expanded={isOpen}
        aria-controls={`${title.toLowerCase().replace(/\s+/g, "-")}-content`}
      >
        <div className="flex items-center gap-3 min-w-0">
          {icon && <span className="flex-shrink-0 text-gray-500">{icon}</span>}
          <h3 className="text-sm font-semibold text-gray-900 truncate">{title}</h3>
          {badge !== undefined && badge > 0 && (
            <Badge variant="secondary" className="ml-2">
              {badge}
            </Badge>
          )}
        </div>

        {/* Chevron Icon */}
        <ChevronDown
          className={cn(
            "w-4 h-4 flex-shrink-0 text-gray-500 transition-transform duration-200 ease-out",
            isOpen && "transform rotate-180"
          )}
          aria-hidden="true"
        />
      </button>

      {/* Content Area */}
      <div
        id={`${title.toLowerCase().replace(/\s+/g, "-")}-content`}
        className={cn(
          "transition-all duration-200 ease-out overflow-hidden",
          isOpen ? "max-h-96" : "max-h-0"
        )}
      >
        <div className="px-4 py-4 bg-white border-t border-gray-200">
          {children}
        </div>
      </div>
    </div>
  );
}
