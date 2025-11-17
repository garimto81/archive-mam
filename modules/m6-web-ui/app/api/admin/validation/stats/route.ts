/**
 * GET /api/admin/validation/stats
 * BFF endpoint for validation statistics (proxies M3 Timecode Validation)
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/lib/api-config';
import { ValidationStats, ApiError } from '@/lib/types';

export async function GET(req: NextRequest) {
  try {
    // Proxy to M3 Timecode Validation Service
    const response = await fetch(`${API_ENDPOINTS.M3_VALIDATION}/stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      return NextResponse.json(
        {
          error: {
            code: 'M3_ERROR',
            message: errorData?.error?.message || 'Validation service error',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: response.status }
      );
    }

    const data: ValidationStats = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('Validation stats API error:', error);

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
