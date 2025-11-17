/**
 * GET /api/hand/[hand_id]
 * BFF endpoint for hand details (from BigQuery via mock data for now)
 */

import { NextRequest, NextResponse } from 'next/server';
import { HandDetail, ApiError } from '@/lib/types';
import { readFile } from 'fs/promises';
import path from 'path';

export async function GET(
  req: NextRequest,
  { params }: { params: { hand_id: string } }
) {
  try {
    const handId = params.hand_id;

    if (!handId) {
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

    // In development, load from mock data
    // In production, this would query BigQuery
    try {
      const mockDataPath = path.join(
        process.cwd(),
        '..',
        '..',
        'mock_data',
        'bigquery',
        'hand_summary_mock.json'
      );
      const mockData = JSON.parse(await readFile(mockDataPath, 'utf-8'));

      // Find hand by ID
      const hand = mockData.find((h: HandDetail) => h.hand_id === handId);

      if (!hand) {
        return NextResponse.json(
          {
            error: {
              code: 'NOT_FOUND',
              message: `Hand ${handId} not found`,
            },
            timestamp: new Date().toISOString(),
          } as ApiError,
          { status: 404 }
        );
      }

      return NextResponse.json(hand);
    } catch (fileError) {
      console.error('Error loading mock data:', fileError);

      // Return mock hand if file not found
      const mockHand: HandDetail = {
        hand_id: handId,
        tournament_id: 'WSOP2024',
        event_name: 'Main Event Day 3',
        day_number: 3,
        hand_number: parseInt(handId.split('_h')[1] || '1', 10),
        timestamp_start: new Date().toISOString(),
        timestamp_end: new Date(Date.now() + 150000).toISOString(),
        summary_text: `Mock hand ${handId}`,
        players: [],
        pot_size: 100000,
        nas_path: '/nas/poker/mock.mp4',
        proxy_url: null,
      };

      return NextResponse.json(mockHand);
    }
  } catch (error) {
    console.error('Hand detail API error:', error);

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
