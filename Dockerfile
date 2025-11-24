# Multi-stage Dockerfile for WebMirror
# Optimized for production with minimal size and maximum security

# ============================================================================
# Stage 1: Builder - Install dependencies and build the application
# ============================================================================
FROM python:3.11-slim as builder

# Install uv - the fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Install system dependencies required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv (blazingly fast!)
RUN uv pip install --system --no-cache -e .

# ============================================================================
# Stage 2: Runtime - Create minimal production image
# ============================================================================
FROM python:3.11-slim

# Install Chrome for Selenium support
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome path for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Create non-root user for security
RUN useradd -m -u 1000 webmirror && \
    mkdir -p /app /data && \
    chown -R webmirror:webmirror /app /data

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application source
COPY --chown=webmirror:webmirror src/ /app/src/

# Switch to non-root user
USER webmirror

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default output directory
VOLUME ["/data"]
WORKDIR /data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import webmirror; print(webmirror.__version__)" || exit 1

# Entry point
ENTRYPOINT ["python", "-m", "webmirror.cli"]
CMD ["--help"]

# Metadata
LABEL maintainer="Ruslan Magana <contact@ruslanmv.com>"
LABEL description="WebMirror - A blazingly fast, async-first website cloning engine"
LABEL version="1.0.0"
