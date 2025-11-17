# M6 Web UI Dockerfile
# Multi-stage build for production deployment

# Stage 1: Dependencies
FROM node:18-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Stage 2: Builder
FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Build arguments for environment
ARG NEXT_PUBLIC_POKER_ENV=production
ARG NEXT_PUBLIC_M3_API_URL
ARG NEXT_PUBLIC_M4_API_URL
ARG NEXT_PUBLIC_M5_API_URL

# Set environment variables for build
ENV NEXT_PUBLIC_POKER_ENV=$NEXT_PUBLIC_POKER_ENV
ENV NEXT_PUBLIC_M3_API_URL=$NEXT_PUBLIC_M3_API_URL
ENV NEXT_PUBLIC_M4_API_URL=$NEXT_PUBLIC_M4_API_URL
ENV NEXT_PUBLIC_M5_API_URL=$NEXT_PUBLIC_M5_API_URL
ENV NODE_ENV=production

# Build application
RUN npm run build

# Stage 3: Runner
FROM node:18-alpine AS runner
WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set ownership
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set environment
ENV PORT=3000
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start application
CMD ["node", "server.js"]
