# EvalX Online Judge Dockerfile
# Multi-stage build for optimized image size

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY main/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=main.settings \
    PORT=8000

# Create non-root user for security (code execution runs in isolated context)
RUN groupadd --gid 1000 evalx && \
    useradd --uid 1000 --gid evalx --shell /bin/bash --create-home evalx

WORKDIR /app

# Install runtime dependencies including compilers for code execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    # C/C++ compiler
    gcc \
    g++ \
    # Java runtime and compiler
    default-jdk \
    # Utilities
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY main/ /app/

# Create directories for static files and database
RUN mkdir -p /app/staticfiles /app/data && \
    chown -R evalx:evalx /app

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh 2>/dev/null || true

# Install netcat for database health checks
USER root
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER evalx

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Entrypoint for initialization
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - run with gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "main.wsgi:application"]

