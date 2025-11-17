/**
 * Hand Detail Page
 * Display full hand information with video preview and download option
 */

'use client';

import * as React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Calendar, Users, DollarSign, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { VideoPlayer } from '@/components/VideoPlayer';
import { DownloadButton } from '@/components/DownloadButton';
import { bffApi } from '@/lib/api-client';
import { HandDetail } from '@/lib/types';
import { formatCurrency, formatRelativeTime } from '@/lib/utils';
import { Loader2, AlertCircle } from 'lucide-react';

export default function HandDetailPage() {
  const params = useParams();
  const router = useRouter();
  const handId = params.hand_id as string;

  const [hand, setHand] = React.useState<HandDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Fetch hand details
  React.useEffect(() => {
    const fetchHand = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = (await bffApi.hand.detail(handId)) as HandDetail;
        setHand(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load hand details');
      } finally {
        setLoading(false);
      }
    };

    fetchHand();
  }, [handId]);

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">Loading hand details...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !hand) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-center py-12">
          <div className="text-center max-w-md">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to Load Hand</h3>
            <p className="text-sm text-muted-foreground mb-4">{error || 'Hand not found'}</p>
            <Button onClick={() => router.back()}>Go Back</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Back button */}
      <Button variant="ghost" onClick={() => router.back()} className="mb-4">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Results
      </Button>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">{hand.summary_text}</h1>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{hand.event_name}</Badge>
          <Badge variant="outline">Day {hand.day_number}</Badge>
          <Badge variant="outline">Hand #{hand.hand_number}</Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content - Video and details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Video player */}
          {hand.proxy_url && (
            <Card>
              <CardContent className="p-0">
                <VideoPlayer src={hand.proxy_url} className="aspect-video" />
              </CardContent>
            </Card>
          )}

          {/* Hand description */}
          <Card>
            <CardHeader>
              <CardTitle>Hand Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground whitespace-pre-wrap">{hand.summary_text}</p>
            </CardContent>
          </Card>

          {/* Player actions */}
          {hand.players && hand.players.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Player Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {hand.players.map((player, index) => (
                    <div key={index} className="flex items-start gap-3 pb-3 border-b last:border-0">
                      <div className="flex-1">
                        <div className="font-semibold">{player.player_name}</div>
                        <div className="text-sm text-muted-foreground">{player.action}</div>
                        {player.hand_strength && (
                          <Badge variant="outline" className="mt-1">
                            {player.hand_strength}
                          </Badge>
                        )}
                      </div>
                      {player.amount && (
                        <div className="text-sm font-semibold">{formatCurrency(player.amount)}</div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Metadata and actions */}
        <div className="space-y-6">
          {/* Download button */}
          <Card>
            <CardHeader>
              <CardTitle>Download</CardTitle>
              <CardDescription>Get this hand as a video clip</CardDescription>
            </CardHeader>
            <CardContent>
              <DownloadButton handId={hand.hand_id} variant="default" size="lg" />
            </CardContent>
          </Card>

          {/* Hand metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <MetadataItem
                icon={<Calendar className="h-4 w-4" />}
                label="Date"
                value={new Date(hand.timestamp_start).toLocaleDateString()}
              />

              <MetadataItem
                icon={<Clock className="h-4 w-4" />}
                label="Time"
                value={formatRelativeTime(hand.timestamp_start)}
              />

              {hand.players && hand.players.length > 0 && (
                <MetadataItem
                  icon={<Users className="h-4 w-4" />}
                  label="Players"
                  value={hand.players.map((p) => p.player_name).join(', ')}
                />
              )}

              {hand.pot_size && (
                <MetadataItem
                  icon={<DollarSign className="h-4 w-4" />}
                  label="Pot Size"
                  value={formatCurrency(hand.pot_size)}
                />
              )}

              <div className="pt-4 border-t">
                <div className="text-xs text-muted-foreground">Hand ID</div>
                <div className="text-sm font-mono">{hand.hand_id}</div>
              </div>

              {hand.sync_score !== undefined && (
                <div>
                  <div className="text-xs text-muted-foreground">Sync Score</div>
                  <div className="text-sm">{(hand.sync_score * 100).toFixed(1)}%</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Metadata item component
function MetadataItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 text-muted-foreground">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-sm break-words">{value}</div>
      </div>
    </div>
  );
}
