'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { OpenHandHistory } from '@/types/openHandHistory';
import { allMockHands } from '@/lib/mock/openHandHistoryMockData';
import { HandHeader } from '@/components/hand-detail/HandHeader';
import { PlayersGrid } from '@/components/hand-detail/PlayersGrid';
import { ActionTimeline } from '@/components/hand-detail/ActionTimeline';
import { PotDistribution } from '@/components/hand-detail/PotDistribution';
import { VideoPlayer } from '@/components/hand-detail/VideoPlayer';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Share2 } from 'lucide-react';
import { PageErrorBoundary } from '@/components/ErrorBoundary';

interface HandDetailPageProps {
  params: {
    handId: string;
  };
}

/**
 * Hand Detail Page
 *
 * Comprehensive hand history viewer with:
 * - Header with game info and tags
 * - Players grid with stacks and positions
 * - Action timeline (street by street)
 * - Pot distribution
 * - Video player (if available)
 *
 * Features:
 * - Loading state with skeleton
 * - Error handling (404, 500)
 * - Share functionality
 * - Back navigation
 * - Responsive design (mobile, tablet, desktop)
 *
 * @param params.handId - Unique hand identifier
 */
export default function HandDetailPage({ params }: HandDetailPageProps) {
  const router = useRouter();
  const [hand, setHand] = useState<OpenHandHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate API fetch with mock data
    const fetchHand = async () => {
      try {
        setLoading(true);
        setError(null);

        // Simulate network delay
        await new Promise((resolve) => setTimeout(resolve, 300));

        // Find hand in mock data
        const foundHand = allMockHands.find(
          (h) => h.game_number === params.handId
        );

        if (!foundHand) {
          setError('Hand not found');
          return;
        }

        setHand(foundHand);
      } catch (err) {
        setError('Failed to load hand');
        if (process.env.NODE_ENV === 'development') {
          console.error('[DEV] Error fetching hand:', err);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchHand();
  }, [params.handId]);

  const handleShare = async () => {
    const url = window.location.href;

    if (navigator.share) {
      try {
        await navigator.share({
          title: `Poker Hand: ${hand?.game_number}`,
          text: `Check out this poker hand: ${hand?.hero_player_id}`,
          url: url,
        });
      } catch (err) {
        // User cancelled or share failed - silently ignore
      }
    } else {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(url);
        alert('Link copied to clipboard!');
      } catch (err) {
        if (process.env.NODE_ENV === 'development') {
          console.error('[DEV] Failed to copy:', err);
        }
      }
    }
  };

  // Loading state
  if (loading) {
    return (
      <PageErrorBoundary>
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          <Skeleton className="h-10 w-32 mb-6" />
          <Skeleton className="h-64 w-full mb-6" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
          </div>
        </div>
      </PageErrorBoundary>
    );
  }

  // Error state
  if (error || !hand) {
    return (
      <PageErrorBoundary>
        <div className="container mx-auto px-4 py-16 max-w-2xl text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {error === 'Hand not found' ? '404 - Hand Not Found' : 'Error Loading Hand'}
          </h1>
          <p className="text-gray-600 mb-8">
            {error === 'Hand not found'
              ? `The hand "${params.handId}" could not be found.`
              : 'An error occurred while loading the hand details. Please try again.'}
          </p>
          <Button onClick={() => router.back()} variant="default">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>
      </PageErrorBoundary>
    );
  }

  // Extract video URL from tournament info or use placeholder
  const videoUrl = hand.tournament_info?.name
    ? `https://www.youtube.com/watch?v=dQw4w9WgXcQ` // Placeholder
    : undefined;

  return (
    <PageErrorBoundary>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Top Navigation */}
        <div className="flex items-center justify-between mb-6">
          <Button
            onClick={() => router.back()}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Results
          </Button>
          <Button
            onClick={handleShare}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <Share2 className="w-4 h-4" />
            Share
          </Button>
        </div>

        {/* Header Section */}
        <HandHeader hand={hand} />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
          {/* Left Column: Players + Pot Distribution */}
          <div className="lg:col-span-1 space-y-6">
            <PlayersGrid hand={hand} />
            <PotDistribution hand={hand} />
          </div>

          {/* Right Column: Action Timeline + Video */}
          <div className="lg:col-span-2 space-y-6">
            <ActionTimeline hand={hand} />
            {videoUrl && <VideoPlayer videoUrl={videoUrl} handId={hand.game_number} />}
          </div>
        </div>
      </div>
    </PageErrorBoundary>
  );
}
