# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

# Only copy source files needed for the build (not node_modules)
COPY frontend/index.html ./
COPY frontend/src/ ./src/
COPY frontend/public/ ./public/
COPY frontend/vite.config.ts ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/tsconfig*.json ./
RUN npm run build
# Output: /app/frontend/dist/


# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.12-slim

# System tools required for tc / iptables / ebtables
RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    iptables \
    ebtables \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy uv project files and install dependencies (no dev deps)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# Copy backend source
COPY backend/ ./

# Copy built frontend dist only (no source, no node_modules)
COPY --from=frontend-builder /app/frontend/dist/ ./static/

# Create data directory for SQLite
RUN mkdir -p /data

EXPOSE 8080

CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
