FROM python:3.11.9-slim

# Install build tools in case any package needs them
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better layer caching
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies — prefer binary wheels, allow source compile as fallback
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set working dir to backend so `app.main` is importable
WORKDIR /app/backend

EXPOSE 10000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
