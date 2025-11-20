'use client';

import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { logger } from '@/lib/utils/logger';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Error Boundary Component
 *
 * Catches React component errors and displays fallback UI.
 * Prevents the entire app from crashing due to component errors.
 *
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error details to monitoring service
    logger.error('Error Boundary caught error', error);

    this.setState({
      errorInfo,
    });

    // Send to error tracking service (Sentry, CloudWatch, etc.)
    if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
      // Sentry.captureException(error, { extra: errorInfo });
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): React.ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center p-8">
          <div className="mx-auto max-w-md text-center">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600">
              <AlertCircle className="h-6 w-6" />
            </div>

            <h2 className="mb-2 text-2xl font-bold text-gray-900">
              Something went wrong
            </h2>

            <p className="mb-6 text-gray-600">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="mb-6 rounded-lg bg-gray-100 p-4 text-left text-sm">
                <summary className="cursor-pointer font-semibold text-gray-700">
                  Error Details (Development Only)
                </summary>
                <pre className="mt-2 overflow-auto text-xs text-gray-600">
                  {this.state.error?.stack}
                </pre>
                <pre className="mt-2 overflow-auto text-xs text-gray-600">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div className="flex gap-3 justify-center">
              <Button
                onClick={this.handleReset}
                variant="default"
              >
                Try Again
              </Button>

              <Button
                onClick={() => window.location.href = '/'}
                variant="outline"
              >
                Go Home
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Page-level Error Boundary
 *
 * Specialized error boundary for page components.
 * Shows page-specific error UI with navigation options.
 */
export function PageErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      fallback={
        <div className="container mx-auto py-12">
          <div className="mx-auto max-w-2xl text-center">
            <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-red-100 text-red-600">
              <AlertCircle className="h-8 w-8" />
            </div>

            <h1 className="mb-4 text-4xl font-bold text-gray-900">
              Page Error
            </h1>

            <p className="mb-8 text-lg text-gray-600">
              We encountered an error while loading this page. Please try again or go back to the home page.
            </p>

            <div className="flex gap-4 justify-center">
              <Button
                onClick={() => window.location.reload()}
                variant="default"
                size="lg"
              >
                Reload Page
              </Button>

              <Button
                onClick={() => window.location.href = '/'}
                variant="outline"
                size="lg"
              >
                Go Home
              </Button>
            </div>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

/**
 * Feature-level Error Boundary
 *
 * Specialized error boundary for specific features.
 * Allows the rest of the app to continue working even if one feature fails.
 */
export function FeatureErrorBoundary({
  children,
  featureName,
}: {
  children: React.ReactNode;
  featureName: string;
}) {
  return (
    <ErrorBoundary
      fallback={
        <div className="rounded-lg border border-red-200 bg-red-50 p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 mb-1">
                {featureName} Error
              </h3>
              <p className="text-sm text-red-700">
                This feature is temporarily unavailable. Please try again later.
              </p>
            </div>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}
