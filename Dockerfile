FROM python:3.11.9-slim

WORKDIR /app

# Copy and install backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set working directory to backend so uvicorn finds app.main
WORKDIR /app/backend

EXPOSE 10000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
