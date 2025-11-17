/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Environment-aware API configuration
  env: {
    NEXT_PUBLIC_POKER_ENV: process.env.NEXT_PUBLIC_POKER_ENV || 'development',
    NEXT_PUBLIC_M3_API_URL: process.env.NEXT_PUBLIC_M3_API_URL || 'http://localhost:8003/v1',
    NEXT_PUBLIC_M4_API_URL: process.env.NEXT_PUBLIC_M4_API_URL || 'http://localhost:8004/v1',
    NEXT_PUBLIC_M5_API_URL: process.env.NEXT_PUBLIC_M5_API_URL || 'http://localhost:8005/v1',
  },

  // Image optimization
  images: {
    domains: ['storage.googleapis.com'],
    formats: ['image/avif', 'image/webp'],
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          }
        ]
      }
    ];
  },

  // Webpack optimizations
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
}

module.exports = nextConfig;
