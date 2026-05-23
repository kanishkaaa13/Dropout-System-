# ─────────────────────────────────────────────────────────────────────────────
# frontend/Dockerfile
# Multi-stage build: Node.js build → Nginx serve
#
# Stage 1 (builder) — install deps and run `npm run build`
# Stage 2 (runtime) — copy only the static dist/ into a minimal nginx image
#
# This keeps the final image < 30 MB instead of > 600 MB.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build React app ──────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests first so node_modules layer is cached
COPY package.json package-lock.json ./

# Install exact versions from lockfile (faster + reproducible)
RUN npm ci --silent

# Copy source and build for production
COPY . .
RUN npm run build


# ── Stage 2: Serve with Nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="JEE Dropout Prediction System"
LABEL description="React frontend served by Nginx"

# Remove the default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom nginx config (handles React Router fallback)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Nginx runs in foreground by default in Docker — no CMD override needed
CMD ["nginx", "-g", "daemon off;"]
