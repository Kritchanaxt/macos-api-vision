# Stage 1: Base image
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base AS dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies (skip macOS-only packages)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    Pillow \
    numpy \
    opencv-python-headless

# Stage 3: Production
FROM dependencies AS production

# Copy application code
COPY ./app ./app
COPY ./static ./static

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE  5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
