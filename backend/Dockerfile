# ─────────────────────────────────────────────────────────────────────────────
# backend/Dockerfile
# Multi-layer build for the FastAPI JEE Dropout Prediction backend.
#
# Build stages
# ────────────
#   deps   — install Python packages into /install so they are cached
#   runtime — lean final image that copies only what is needed
#
# The two-stage approach keeps the final image small: gcc and build headers
# are needed to compile psycopg2-binary / cryptography but are not needed
# at runtime.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS deps

# Install C build tools + libpq headers (required for psycopg2-binary, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy only requirements first — this layer is cached until requirements change
COPY requirements.txt .

# Install all packages into a dedicated prefix so we can copy them cleanly
RUN pip install --prefix=/install --no-cache-dir --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="JEE Dropout Prediction System"
LABEL description="FastAPI backend — ML-powered dropout risk prediction"

# Runtime system deps only (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from the builder stage
COPY --from=deps /install /usr/local

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

# Copy project source
COPY . .

# Ensure model and report directories exist and are writable
RUN mkdir -p /app/models /app/reports /app/uploads /app/logs \
 && chown -R appuser:appuser /app

USER appuser

# Expose FastAPI port
EXPOSE 8000

# ── Entrypoint ────────────────────────────────────────────────────────────────
# 1. Run Alembic migrations (idempotent — safe to run on every startup)
# 2. Start uvicorn with 2 workers
#
# The ENTRYPOINT script is inlined here to avoid a separate file.
CMD ["sh", "-c", "\
    echo '[Docker] Running Alembic migrations...' && \
    alembic upgrade head && \
    echo '[Docker] Starting uvicorn...' && \
    uvicorn backend.app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 2 \
        --access-log \
        --log-level info \
"]
