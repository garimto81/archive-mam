"use client";

import React from "react";
import { Database, Bot, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AutocompleteSource } from "@/types";

interface SourceBadgeProps {
  source: AutocompleteSource;
  responseTimeMs: number;
}

/**
 * Autocomplete Source Badge Component
 *
 * Displays the source of autocomplete suggestions (cache, AI, or hybrid)
 * along with response time. Shows in the footer of the dropdown.
 *
 * @example
 * ```tsx
 * <SourceBadge source="vertex_ai" responseTimeMs={45} />
 * ```
 */
export function SourceBadge({ source, responseTimeMs }: SourceBadgeProps) {
  const config: Record<string, { icon: any; label: string; color: string }> = {
    bigquery_cache: {
      icon: Database,
      label: "Fast",
      color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100"
    },
    vertex_ai: {
      icon: Bot,
      label: "AI-powered",
      color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100"
    },
    hybrid: {
      icon: Zap,
      label: "Smart",
      color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100"
    },
    mock: {
      icon: Database,
      label: "Mock",
      color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100"
    }
  };

  const sourceConfig = source in config ? config[source] : config.mock;
  const { icon: Icon, label, color } = sourceConfig;

  return (
    <Badge variant="outline" className={cn("text-xs", color)}>
      <Icon className="w-3 h-3 mr-1" />
      {label} ({responseTimeMs}ms)
    </Badge>
  );
}
