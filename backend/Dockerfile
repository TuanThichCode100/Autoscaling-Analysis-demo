# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install system dependencies
# --- ĐÃ SỬA: Thêm docker.io vào đây ---
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir "numpy>=1.24.0,<2.0.0" && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application code (will be overridden by volume mount in dev)
COPY backend/ /app/
COPY ml_model/ /app/ml_model/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]