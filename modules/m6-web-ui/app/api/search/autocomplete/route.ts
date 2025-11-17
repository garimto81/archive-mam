/**
 * GET /api/search/autocomplete
 * BFF endpoint for autocomplete suggestions (proxies M4 RAG Search)
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/lib/api-config';
import { AutocompleteResponse, ApiError } from '@/lib/types';

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const query = searchParams.get('q') || '';
    const limit = parseInt(searchParams.get('limit') || '10', 10);

    // Validate request
    if (query.trim().length < 2) {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'q parameter must be at least 2 characters',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    if (limit < 1 || limit > 20) {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'limit must be between 1 and 20',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    // Proxy to M4 RAG Search autocomplete
    const response = await fetch(
      `${API_ENDPOINTS.M4_SEARCH}/search/autocomplete?q=${encodeURIComponent(query)}&limit=${limit}`,
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
            code: 'M4_ERROR',
            message: errorData?.error?.message || 'Autocomplete service error',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: response.status }
      );
    }

    const data: AutocompleteResponse = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('Autocomplete API error:', error);

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
