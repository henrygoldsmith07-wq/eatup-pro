# EatUp Pro v8.0 - Multi-stage Docker Containerization
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOTNET_CLI_TELEMETRY_OPT_OUT=1 \
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    wget \
    curl \
    git \
    file \
    lsb-release \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy application code
COPY . .

# Create data directory for database
RUN mkdir -p /app/data && chmod 755 /app/data

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Command to run the application
CMD ["python", "api_server.py"]

# Optional: Production stage with optimization
FROM base as production

# Optimize Python installation
RUN pip install gunicorn \
    && find /usr/local/lib/python3.11/site-packages -name "*.pyc" -delete \
    && find /usr/local/lib/python3.11/site-packages -name "__pycache__" -delete

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "api_server:app"]

# Optional: Minimal stage (smallest image size)
FROM base as minimal

# Remove unnecessary files
RUN find /app -type f -name "*.pyc" -delete \
    && find /app -type d -name "__pycache__" -delete \
    && find /app -type f -name "*.log" -delete \
    && rm -rf /app/docs /app/tests /app/.git

LABEL org.label-schema.name="EatUp Pro" \
      org.label-schema.description="Enterprise Storage Management Platform" \
      org.label-schema.version="8.0.0" \
      org.label-schema.vendor="EatUp Team" \
      maintainer="support@eatup.pro"
