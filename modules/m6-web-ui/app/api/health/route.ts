/**
 * GET /api/health
 * Health check endpoint - checks BFF and all upstream services
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS, IS_DEVELOPMENT } from '@/lib/api-config';
import { HealthResponse } from '@/lib/types';

async function checkServiceHealth(url: string): Promise<'healthy' | 'unhealthy'> {
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(5000), // 5 second timeout
    });

    return response.ok ? 'healthy' : 'unhealthy';
  } catch {
    return 'unhealthy';
  }
}

export async function GET(req: NextRequest) {
  try {
    // Check all upstream services in parallel
    const [m3Status, m4Status, m5Status] = await Promise.all([
      checkServiceHealth(`${API_ENDPOINTS.M3_VALIDATION}/health`),
      checkServiceHealth(`${API_ENDPOINTS.M4_SEARCH}/health`),
      checkServiceHealth(`${API_ENDPOINTS.M5_CLIPPING}/health`),
    ]);

    const dependencies = {
      m3_validation: m3Status,
      m4_search: m4Status,
      m5_clipping: m5Status,
    };

    // Overall status
    const allHealthy = Object.values(dependencies).every((status) => status === 'healthy');
    const anyUnhealthy = Object.values(dependencies).some((status) => status === 'unhealthy');

    const overallStatus: 'healthy' | 'degraded' | 'unhealthy' = allHealthy
      ? 'healthy'
      : anyUnhealthy
      ? 'degraded'
      : 'unhealthy';

    const healthResponse: HealthResponse = {
      status: overallStatus,
      environment: IS_DEVELOPMENT ? 'development' : 'production',
      uptime_seconds: Math.floor(process.uptime()),
      dependencies,
    };

    const statusCode = overallStatus === 'healthy' ? 200 : overallStatus === 'degraded' ? 200 : 503;

    return NextResponse.json(healthResponse, { status: statusCode });
  } catch (error) {
    console.error('Health check error:', error);

    return NextResponse.json(
      {
        status: 'unhealthy',
        environment: IS_DEVELOPMENT ? 'development' : 'production',
        error: 'Health check failed',
      } as HealthResponse,
      { status: 503 }
    );
  }
}
