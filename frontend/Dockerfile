# M3 Agent UI v2.2 - Frontend with WebSocket Triangle Chat Room
# Multi-stage build for optimized production image

# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm@9.15.0 && \
    pnpm install --frozen-lockfile

# Copy source code (entire project structure)
COPY client ./client
COPY vite.config.ts tsconfig.json ./

# Build the application
RUN pnpm run build

# Stage 2: Production
FROM nginx:1.27-alpine

# Copy built files from builder stage (dist/public as per vite.config.ts)
COPY --from=builder /app/dist/public /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
