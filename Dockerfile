# OpenStack Monitoring Dashboard Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/analysis data/forecasts templates logs

# Set environment variables
ENV FLASK_APP=dashboard.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting OpenStack Monitoring Dashboard..."\n\
echo "Waiting for OpenStack API to be available..."\n\
sleep 10\n\
echo "Starting data collection..."\n\
python collect_metrics.py\n\
echo "Starting analysis..."\n\
python analyze_metrics.py\n\
echo "Starting forecasting..."\n\
python forecast_usage.py\n\
echo "Starting dashboard server..."\n\
python dashboard.py\n\
' > start.sh && chmod +x start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Run the application
CMD ["./start.sh"]
