/**
 * GET /api/download/[id]/status
 * BFF endpoint for checking download status (proxies M5 Clipping)
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/lib/api-config';
import { DownloadStatus, ApiError } from '@/lib/types';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const clipRequestId = params.id;

    if (!clipRequestId) {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'clip_request_id is required',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    // Proxy to M5 Clipping Service
    const response = await fetch(
      `${API_ENDPOINTS.M5_CLIPPING}/clip/${clipRequestId}/status`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      return NextResponse.json(
        {
          error: {
            code: errorData?.error?.code || 'M5_ERROR',
            message: errorData?.error?.message || 'Status check failed',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: response.status }
      );
    }

    const data: DownloadStatus = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('Download status API error:', error);

    return NextResponse.json(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An unexpected error occurred',
        },
        timestamp: new Date().toISOString(),
      } as ApiError,
      { status: 500 }
    );
  }
}
