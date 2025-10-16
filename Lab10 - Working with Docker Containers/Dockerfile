# Start from official Python slim image
FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Install build deps and cleanup to keep image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY shopease/requirements.txt /app/requirements.txt

# Install Python deps
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY shopease /app/shopease

# Expose the port the app listens on
EXPOSE 8000

# Default environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run the uvicorn server and bind to 0.0.0.0 so host can connect
CMD ["uvicorn", "shopease.app:app", "--host", "0.0.0.0", "--port", "8000"]
