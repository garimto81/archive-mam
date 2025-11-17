/**
 * POST /api/search
 * BFF endpoint for searching poker hands (proxies M4 RAG Search)
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/lib/api-config';
import { SearchRequest, SearchResponse, ApiError } from '@/lib/types';

export async function POST(req: NextRequest) {
  try {
    const body: SearchRequest = await req.json();

    // Validate request
    if (!body.query || typeof body.query !== 'string') {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'query is required and must be a string',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    if (body.query.trim().length < 2) {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'query must be at least 2 characters',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    // Proxy to M4 RAG Search
    const response = await fetch(`${API_ENDPOINTS.M4_SEARCH}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: body.query,
        limit: body.limit || 20,
        filters: body.filters || {},
        include_proxy: body.include_proxy !== false,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      return NextResponse.json(
        {
          error: {
            code: 'M4_ERROR',
            message: errorData?.error?.message || 'Search service error',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: response.status }
      );
    }

    const data: SearchResponse = await response.json();

    // Add BFF-specific enhancements
    const enhancedResponse: SearchResponse = {
      query_id: data.query_id || `search-${Date.now()}`,
      total_results: data.total_results || data.results?.length || 0,
      processing_time_ms: data.processing_time_ms,
      results: (data.results || []).map((result) => ({
        ...result,
        is_favorite: false, // TODO: Check user favorites from database
      })),
    };

    return NextResponse.json(enhancedResponse);
  } catch (error) {
    console.error('Search API error:', error);

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
