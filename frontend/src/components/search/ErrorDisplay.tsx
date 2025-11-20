"use client";

import React from "react";
import { AlertCircle, Clock, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AutocompleteError } from "@/types";

interface ErrorDisplayProps {
  error: AutocompleteError;
  onRetry?: () => void;
}

/**
 * Error Display Component
 *
 * Displays autocomplete errors with appropriate icons and retry options.
 * Handles validation, rate limit, network, server, and timeout errors.
 *
 * @example
 * ```tsx
 * <ErrorDisplay
 *   error={{
 *     error: "network",
 *     message: "Failed to connect to server"
 *   }}
 *   onRetry={() => refetch()}
 * />
 * ```
 */
export function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  const config = {
    validation: {
      icon: AlertCircle,
      title: "Invalid Query",
      color: "text-yellow-500"
    },
    rate_limit: {
      icon: Clock,
      title: "Too Many Requests",
      color: "text-orange-500"
    },
    network: {
      icon: WifiOff,
      title: "Connection Error",
      color: "text-red-500"
    },
    server: {
      icon: AlertCircle,
      title: "Server Error",
      color: "text-red-500"
    },
    timeout: {
      icon: Clock,
      title: "Request Timeout",
      color: "text-orange-500"
    },
    unknown: {
      icon: AlertCircle,
      title: "Error",
      color: "text-red-500"
    }
  };

  // Safely get error config with fallback to 'unknown'
  const errorType = error?.error || 'unknown';
  const errorConfig = (errorType in config)
    ? config[errorType as keyof typeof config]
    : config.unknown;
  const { icon: Icon, title, color } = errorConfig;

  return (
    <div className="p-4 text-center">
      <Icon className={cn("w-12 h-12 mx-auto mb-2", color)} />
      <h3 className="font-semibold text-sm">{title}</h3>
      <p className="text-xs text-muted-foreground mt-1">{error.message}</p>

      {error.retryAfterSeconds && (
        <p className="text-xs text-muted-foreground mt-2">
          Please wait {error.retryAfterSeconds}s before trying again
        </p>
      )}

      {onRetry && error.error !== "rate_limit" && (
        <Button
          onClick={onRetry}
          variant="outline"
          size="sm"
          className="mt-3"
        >
          Retry
        </Button>
      )}
    </div>
  );
}
