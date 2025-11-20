"use client";

/**
 * Tree Node Component
 *
 * Recursive component for rendering a single node in the archive tree.
 * Supports expand/collapse, click handling, and nested children.
 */

import React, { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { ChevronRight, ChevronDown } from "lucide-react";
import type { TreeNode as TreeNodeType } from "@/types/tree";

export interface TreeNodeProps {
  /** Node data to render */
  node: TreeNodeType;

  /** Current nesting level (for indentation) */
  level?: number;

  /** Callback when node is clicked */
  onNodeClick?: (node: TreeNodeType) => void;

  /** Callback when expand/collapse is toggled */
  onToggle?: (nodeId: string, isExpanded: boolean) => void;

  /** Whether this node is currently selected */
  isSelected?: boolean;

  /** Custom CSS class name */
  className?: string;
}

/**
 * TreeNode Component
 *
 * Renders a single tree node with expand/collapse functionality.
 * Recursively renders child nodes when expanded.
 *
 * Features:
 * - Expand/collapse chevron icon
 * - Emoji/icon support
 * - Item count badge
 * - Hover effects
 * - Keyboard accessibility
 * - Indentation based on nesting level
 * - Click handling
 * - Selection highlighting
 *
 * @example
 * ```tsx
 * <TreeNode
 *   node={tournamentNode}
 *   level={0}
 *   onNodeClick={(node) => console.log("Clicked:", node.label)}
 *   onToggle={(id, expanded) => console.log("Toggle:", id, expanded)}
 * />
 * ```
 */
export function TreeNode({
  node,
  level = 0,
  onNodeClick,
  onToggle,
  isSelected = false,
  className,
}: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(node.isExpanded || false);

  const hasChildren = node.children && node.children.length > 0;
  const indent = level * 16; // 16px per level

  /**
   * Handle expand/collapse toggle
   */
  const handleToggle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation(); // Prevent node click
      const newExpanded = !isExpanded;
      setIsExpanded(newExpanded);
      onToggle?.(node.id, newExpanded);
    },
    [isExpanded, node.id, onToggle]
  );

  /**
   * Handle node click
   */
  const handleClick = useCallback(() => {
    onNodeClick?.(node);
  }, [node, onNodeClick]);

  /**
   * Handle keyboard events
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      } else if (e.key === "ArrowRight" && hasChildren && !isExpanded) {
        e.preventDefault();
        handleToggle(e as any);
      } else if (e.key === "ArrowLeft" && hasChildren && isExpanded) {
        e.preventDefault();
        handleToggle(e as any);
      }
    },
    [handleClick, handleToggle, hasChildren, isExpanded]
  );

  /**
   * Get node icon
   */
  const getNodeIcon = () => {
    if (node.icon) {
      return node.icon;
    }

    // Default icons based on type
    switch (node.type) {
      case "root":
        return "📁";
      case "tournament":
        return "🏆";
      case "hand":
        return "🃏";
      case "player":
        return "👤";
      case "action":
        return "🎬";
      case "tag":
        return "🏷️";
      default:
        return "📄";
    }
  };

  /**
   * Get node color class
   */
  const getNodeColor = () => {
    switch (node.type) {
      case "tournament":
        return "text-poker-chip-green";
      case "hand":
        return "text-poker-chip-purple";
      case "player":
        return "text-blue-500";
      case "tag":
        return "text-poker-chip-red";
      default:
        return "text-gray-700 dark:text-gray-300";
    }
  };

  return (
    <div className={cn("select-none", className)}>
      {/* Node row */}
      <div
        className={cn(
          "flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors",
          "hover:bg-gray-100 dark:hover:bg-gray-800",
          isSelected && "bg-poker-chip-green/10 border-l-2 border-poker-chip-green",
          "group"
        )}
        style={{ paddingLeft: `${indent + 8}px` }}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label={`${node.label}${node.count ? ` (${node.count} items)` : ""}`}
        aria-expanded={hasChildren ? isExpanded : undefined}
      >
        {/* Expand/collapse chevron */}
        {hasChildren ? (
          <button
            onClick={handleToggle}
            className={cn(
              "flex-shrink-0 w-4 h-4 flex items-center justify-center",
              "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300",
              "transition-transform"
            )}
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        ) : (
          <div className="w-4 h-4 flex-shrink-0" />
        )}

        {/* Icon */}
        <span className="flex-shrink-0 text-base" aria-hidden="true">
          {getNodeIcon()}
        </span>

        {/* Label */}
        <span
          className={cn(
            "flex-1 text-sm font-medium truncate",
            getNodeColor()
          )}
          title={node.label}
        >
          {node.label}
        </span>

        {/* Count badge */}
        {node.count !== undefined && node.count > 0 && (
          <span
            className={cn(
              "flex-shrink-0 px-1.5 py-0.5 rounded-full text-xs font-semibold",
              "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
            )}
          >
            {node.count}
          </span>
        )}
      </div>

      {/* Description tooltip (on hover) */}
      {node.description && (
        <div className="hidden group-hover:block absolute z-10 px-2 py-1 text-xs bg-gray-900 text-white rounded shadow-lg pointer-events-none">
          {node.description}
        </div>
      )}

      {/* Children (recursive) */}
      {hasChildren && isExpanded && (
        <div role="group">
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onNodeClick={onNodeClick}
              onToggle={onToggle}
              isSelected={isSelected}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default TreeNode;
