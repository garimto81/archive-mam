/**
 * Admin Dashboard Page
 * Display timecode validation statistics and manual matching queue
 */

'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { bffApi } from '@/lib/api-client';
import { ValidationStats } from '@/lib/types';
import { Loader2, CheckCircle, AlertTriangle, XCircle, TrendingUp } from 'lucide-react';

export default function AdminPage() {
  const [stats, setStats] = React.useState<ValidationStats | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Fetch validation stats
  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = (await bffApi.admin.stats()) as ValidationStats;
        setStats(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();

    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  // Loading state
  if (loading && !stats) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">Loading statistics...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
        <p className="text-muted-foreground">Timecode validation progress and statistics</p>
      </div>

      {/* Error state */}
      {error && (
        <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Statistics grid */}
      {stats && (
        <>
          {/* Summary cards */}
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            <StatCard
              title="Total Hands"
              value={stats.total_hands.toLocaleString()}
              icon={<TrendingUp className="h-5 w-5 text-blue-500" />}
              color="blue"
            />
            <StatCard
              title="Validated"
              value={stats.validated_hands.toLocaleString()}
              subtitle={`${(stats.validation_rate * 100).toFixed(1)}%`}
              icon={<CheckCircle className="h-5 w-5 text-green-500" />}
              color="green"
            />
            <StatCard
              title="Perfect Sync"
              value={stats.perfect_sync_count.toLocaleString()}
              subtitle={`${((stats.perfect_sync_count / stats.total_hands) * 100).toFixed(1)}%`}
              icon={<CheckCircle className="h-5 w-5 text-emerald-500" />}
              color="emerald"
            />
            <StatCard
              title="Manual Review"
              value={stats.manual_needed_count.toLocaleString()}
              subtitle={`${((stats.manual_needed_count / stats.total_hands) * 100).toFixed(1)}%`}
              icon={<AlertTriangle className="h-5 w-5 text-yellow-500" />}
              color="yellow"
            />
          </div>

          {/* Validation breakdown */}
          <div className="grid gap-6 lg:grid-cols-2 mb-8">
            {/* Validation status breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Validation Status Breakdown</CardTitle>
                <CardDescription>Timecode validation results by category</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <StatusRow
                  label="Perfect Sync"
                  count={stats.perfect_sync_count}
                  total={stats.total_hands}
                  color="bg-emerald-500"
                  icon={<CheckCircle className="h-4 w-4" />}
                />
                <StatusRow
                  label="Offset Needed"
                  count={stats.offset_needed_count}
                  total={stats.total_hands}
                  color="bg-blue-500"
                  icon={<CheckCircle className="h-4 w-4" />}
                />
                <StatusRow
                  label="Manual Review"
                  count={stats.manual_needed_count}
                  total={stats.total_hands}
                  color="bg-yellow-500"
                  icon={<AlertTriangle className="h-4 w-4" />}
                />
                <StatusRow
                  label="Not Validated"
                  count={stats.total_hands - stats.validated_hands}
                  total={stats.total_hands}
                  color="bg-gray-500"
                  icon={<XCircle className="h-4 w-4" />}
                />
              </CardContent>
            </Card>

            {/* Progress visualization */}
            <Card>
              <CardHeader>
                <CardTitle>Validation Progress</CardTitle>
                <CardDescription>
                  Overall progress: {((stats.validated_hands / stats.total_hands) * 100).toFixed(1)}%
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Progress bar */}
                <div className="mb-6">
                  <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-emerald-500"
                      style={{ width: `${(stats.validated_hands / stats.total_hands) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-emerald-600">
                      {((stats.perfect_sync_count / stats.validated_hands) * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Perfect Sync Rate</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {(stats.total_hands - stats.validated_hands).toLocaleString()}
                    </div>
                    <div className="text-xs text-muted-foreground">Remaining</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Manual review queue */}
          {stats.manual_needed_count > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  Manual Review Queue
                </CardTitle>
                <CardDescription>
                  {stats.manual_needed_count} hands require manual timecode matching
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  These hands have low sync scores (&lt;60) and need manual verification to ensure
                  accurate timecode mapping.
                </p>
                {/* In production, would show actual list of hands needing review */}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

// Stat card component
function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

// Status row component
function StatusRow({
  label,
  count,
  total,
  color,
  icon,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
  icon: React.ReactNode;
}) {
  const percentage = (count / total) * 100;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-medium">{label}</span>
        </div>
        <span className="text-sm text-muted-foreground">
          {count.toLocaleString()} ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}
