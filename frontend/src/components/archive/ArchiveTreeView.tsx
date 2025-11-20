"use client";

/**
 * Archive Tree View Component
 *
 * Main component for displaying hierarchical archive navigation.
 * Shows tournaments, hands, players in a collapsible tree structure.
 */

import React, { useState, useMemo, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Search, ChevronDown, ChevronRight, Maximize2, Minimize2 } from "lucide-react";
import { TreeNode } from "./TreeNode";
import { buildArchiveTree, searchTreeNodes, expandAllNodes, collapseAllNodes } from "@/lib/utils/treeBuilder";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { SearchResultItem } from "@/types/search";
import type { TreeNode as TreeNodeType } from "@/types/tree";

export interface ArchiveTreeViewProps {
  /** Search results to display in tree */
  results: readonly SearchResultItem[];

  /** Callback when a node is clicked */
  onNodeClick?: (node: TreeNodeType) => void;

  /** Callback when a hand is selected */
  onHandSelect?: (hand: SearchResultItem) => void;

  /** Custom CSS class name */
  className?: string;

  /** Show search box */
  showSearch?: boolean;

  /** Show expand/collapse all buttons */
  showControls?: boolean;
}

/**
 * ArchiveTreeView Component
 *
 * Displays archive data as a hierarchical tree with search and navigation.
 *
 * Features:
 * - Tournament > Hand > Player hierarchy
 * - Search within tree
 * - Expand/collapse all
 * - Click to navigate
 * - Real-time filtering
 * - Keyboard navigation
 * - Responsive design
 *
 * @example
 * ```tsx
 * <ArchiveTreeView
 *   results={mockSearchResults}
 *   onHandSelect={(hand) => router.push(`/hands/${hand.handId}`)}
 *   showSearch={true}
 *   showControls={true}
 * />
 * ```
 */
export function ArchiveTreeView({
  results,
  onNodeClick,
  onHandSelect,
  className,
  showSearch = true,
  showControls = true,
}: ArchiveTreeViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedAll, setExpandedAll] = useState(false);

  /**
   * Build tree from results
   */
  const tree = useMemo(() => {
    let builtTree = buildArchiveTree(results);

    // Apply search filter
    if (searchQuery.trim()) {
      const filtered = searchTreeNodes(builtTree, searchQuery);
      builtTree = filtered || builtTree;
    }

    // Apply expand/collapse all
    if (expandedAll) {
      builtTree = expandAllNodes(builtTree);
    }

    return builtTree;
  }, [results, searchQuery, expandedAll]);

  /**
   * Handle node click
   */
  const handleNodeClick = useCallback(
    (node: TreeNodeType) => {
      onNodeClick?.(node);

      // If hand node, call onHandSelect
      if (node.type === "hand" && node.data) {
        onHandSelect?.(node.data as SearchResultItem);
      }
    },
    [onNodeClick, onHandSelect]
  );

  /**
   * Handle expand all
   */
  const handleExpandAll = useCallback(() => {
    setExpandedAll(true);
  }, []);

  /**
   * Handle collapse all
   */
  const handleCollapseAll = useCallback(() => {
    setExpandedAll(false);
  }, []);

  /**
   * Get tree statistics
   */
  const stats = useMemo(() => {
    const tournaments = new Set<string>();
    const players = new Set<string>();
    let handCount = 0;

    results.forEach((result) => {
      if (result.tournamentId) {
        tournaments.add(result.tournamentId);
      }
      players.add(result.hero_name);
      players.add(result.villain_name);
      handCount++;
    });

    return {
      tournaments: tournaments.size,
      players: players.size,
      hands: handCount,
    };
  }, [results]);

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-card border border-border rounded-lg overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-foreground">
            📁 Archive
          </h3>

          {/* Statistics */}
          <div className="flex gap-3 text-xs text-muted-foreground">
            <span>🏆 {stats.tournaments}</span>
            <span>🃏 {stats.hands}</span>
            <span>👤 {stats.players}</span>
          </div>
        </div>

        {/* Search */}
        {showSearch && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search tournaments, hands, players..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
        )}

        {/* Controls */}
        {showControls && (
          <div className="flex gap-2 mt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleExpandAll}
              className="flex-1 h-8 text-xs"
            >
              <Maximize2 className="w-3 h-3 mr-1" />
              Expand All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCollapseAll}
              className="flex-1 h-8 text-xs"
            >
              <Minimize2 className="w-3 h-3 mr-1" />
              Collapse All
            </Button>
          </div>
        )}
      </div>

      {/* Tree content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-2">
        {tree.children && tree.children.length > 0 ? (
          <div role="tree" aria-label="Archive tree">
            {tree.children.map((child) => (
              <TreeNode
                key={child.id}
                node={child}
                level={0}
                onNodeClick={handleNodeClick}
              />
            ))}
          </div>
        ) : (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <div className="text-4xl mb-2">🔍</div>
            <p className="text-sm">
              {searchQuery ? "No results found" : "No archive data available"}
            </p>
            {searchQuery && (
              <Button
                variant="link"
                size="sm"
                onClick={() => setSearchQuery("")}
                className="mt-2"
              >
                Clear search
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 px-4 py-2 border-t border-border bg-muted/50">
        <p className="text-xs text-muted-foreground text-center">
          {searchQuery
            ? `Showing filtered results for "${searchQuery}"`
            : `Total: ${stats.tournaments} tournaments, ${stats.hands} hands`}
        </p>
      </div>
    </div>
  );
}

export default ArchiveTreeView;
