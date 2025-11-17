/**
 * GET /api/favorites - Get user favorites
 * POST /api/favorites - Add favorite
 * DELETE /api/favorites - Remove favorite
 *
 * In production, this would store in Cloud Firestore or Datastore
 * For development, using in-memory storage
 */

import { NextRequest, NextResponse } from 'next/server';
import { FavoritesResponse, AddFavoriteRequest, AddFavoriteResponse, ApiError } from '@/lib/types';

// In-memory storage for development
// In production, use Firestore or Datastore keyed by user ID
const favoritesStore = new Map<string, Set<string>>();

function getUserId(req: NextRequest): string {
  // In production, extract from JWT/session
  // For now, use dev user
  return 'dev-user';
}

export async function GET(req: NextRequest) {
  try {
    const userId = getUserId(req);
    const favorites = favoritesStore.get(userId) || new Set();

    // TODO: Fetch hand details for favorited hands from BigQuery
    const favoritesResponse: FavoritesResponse = {
      total: favorites.size,
      favorites: Array.from(favorites).map((handId) => ({
        hand_id: handId,
        summary: `Favorite hand ${handId}`,
        event_name: 'WSOP 2024',
        players: [],
        is_favorite: true,
      })),
    };

    return NextResponse.json(favoritesResponse);
  } catch (error) {
    console.error('Get favorites API error:', error);

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

export async function POST(req: NextRequest) {
  try {
    const userId = getUserId(req);
    const body: AddFavoriteRequest = await req.json();

    if (!body.hand_id) {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'hand_id is required',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    if (!favoritesStore.has(userId)) {
      favoritesStore.set(userId, new Set());
    }

    const userFavorites = favoritesStore.get(userId)!;
    userFavorites.add(body.hand_id);

    const response: AddFavoriteResponse = {
      status: 'added',
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Add favorite API error:', error);

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

export async function DELETE(req: NextRequest) {
  try {
    const userId = getUserId(req);
    const handId = req.nextUrl.searchParams.get('hand_id');

    if (!handId) {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_REQUEST',
            message: 'hand_id query parameter is required',
          },
          timestamp: new Date().toISOString(),
        } as ApiError,
        { status: 400 }
      );
    }

    const userFavorites = favoritesStore.get(userId);
    if (userFavorites) {
      userFavorites.delete(handId);
    }

    const response: AddFavoriteResponse = {
      status: 'removed',
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Remove favorite API error:', error);

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
