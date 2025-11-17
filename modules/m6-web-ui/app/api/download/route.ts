/**
 * POST /api/download
 * BFF endpoint for requesting clip download (proxies M5 Clipping)
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/lib/api-config';
import { DownloadRequest, DownloadResponse, ApiError } from '@/lib/types';

export async function POST(req: NextRequest) {
  try {
    const body: DownloadRequest = await req.json();

    // Validate request
    if (!body.hand_id || typeof body.hand_id !== 'string') {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'hand_id is required and must be a string',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    // Proxy to M5 Clipping Service
    const response = await fetch(`${API_ENDPOINTS.M5_CLIPPING}/clip/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        hand_id: body.hand_id,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      return NextResponse.json(
        {
          error: {
            code: errorData?.error?.code || 'M5_ERROR',
            message: errorData?.error?.message || 'Clipping service error',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: response.status }
      );
    }

    const data: DownloadResponse = await response.json();

    // TODO: Save download request to user history in database

    return NextResponse.json(data);
  } catch (error) {
    console.error('Download request API error:', error);

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
