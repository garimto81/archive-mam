/**
 * DownloadButton Component
 * Request and poll for clip download with progress indicator
 *
 * Usage:
 * <DownloadButton handId="wsop2024_me_d3_h154" />
 */

'use client';

import * as React from 'react';
import { Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { bffApi } from '@/lib/api-client';
import { DownloadResponse, DownloadStatus, ClipStatus } from '@/lib/types';
import { APP_CONFIG } from '@/lib/api-config';
import { downloadFile } from '@/lib/utils';

interface DownloadButtonProps {
  handId: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
  onStatusChange?: (status: ClipStatus, downloadUrl?: string) => void;
}

export function DownloadButton({
  handId,
  variant = 'default',
  size = 'default',
  onStatusChange,
}: DownloadButtonProps) {
  const [status, setStatus] = React.useState<ClipStatus | null>(null);
  const [progress, setProgress] = React.useState(0);
  const [downloadUrl, setDownloadUrl] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [clipRequestId, setClipRequestId] = React.useState<string | null>(null);

  const pollIntervalRef = React.useRef<NodeJS.Timeout | null>(null);
  const pollStartTimeRef = React.useRef<number>(0);

  // Request clip download
  const handleRequestDownload = async () => {
    try {
      setStatus('queued');
      setError(null);

      const response = (await bffApi.download.request(handId)) as DownloadResponse;
      setClipRequestId(response.clip_request_id);
      setStatus(response.status);

      // Start polling
      pollStartTimeRef.current = Date.now();
      startPolling(response.clip_request_id);
    } catch (err) {
      setStatus('failed');
      setError(err instanceof Error ? err.message : 'Failed to request download');
      onStatusChange?.('failed');
    }
  };

  // Poll for status
  const startPolling = (requestId: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    pollIntervalRef.current = setInterval(async () => {
      // Check timeout (2 minutes max)
      const elapsed = Date.now() - pollStartTimeRef.current;
      if (elapsed > APP_CONFIG.MAX_POLL_DURATION_MS) {
        stopPolling();
        setStatus('failed');
        setError('Download timeout - please try again');
        onStatusChange?.('failed');
        return;
      }

      try {
        const statusResponse = (await bffApi.download.status(requestId)) as DownloadStatus;

        setStatus(statusResponse.status);
        setProgress(statusResponse.progress_percent || 0);

        if (statusResponse.status === 'completed' && statusResponse.download_url) {
          setDownloadUrl(statusResponse.download_url);
          stopPolling();
          onStatusChange?.('completed', statusResponse.download_url);
        } else if (statusResponse.status === 'failed') {
          setError(statusResponse.error_message || 'Download failed');
          stopPolling();
          onStatusChange?.('failed');
        }
      } catch (err) {
        console.error('Polling error:', err);
        // Continue polling on error
      }
    }, APP_CONFIG.POLL_INTERVAL_MS);
  };

  // Stop polling
  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => stopPolling();
  }, []);

  // Handle download file
  const handleDownload = () => {
    if (downloadUrl) {
      downloadFile(downloadUrl, `${handId}.mp4`);
    }
  };

  // Render based on status
  if (status === null) {
    return (
      <Button variant={variant} size={size} onClick={handleRequestDownload}>
        <Download className="mr-2 h-4 w-4" />
        Download Clip
      </Button>
    );
  }

  if (status === 'queued' || status === 'processing') {
    return (
      <Button variant={variant} size={size} disabled>
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        {status === 'queued' ? 'Queued' : `Processing ${progress}%`}
      </Button>
    );
  }

  if (status === 'completed' && downloadUrl) {
    return (
      <Button variant={variant} size={size} onClick={handleDownload}>
        <CheckCircle className="mr-2 h-4 w-4" />
        Download Ready
      </Button>
    );
  }

  if (status === 'failed') {
    return (
      <Button variant="destructive" size={size} onClick={handleRequestDownload}>
        <AlertCircle className="mr-2 h-4 w-4" />
        Retry Download
      </Button>
    );
  }

  return null;
}
