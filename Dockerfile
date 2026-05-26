# Build Stage for React Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Production Stage for FastAPI
FROM python:3.11-slim

# Install system dependencies needed for Playwright/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Copy and install python dependencies
COPY backend/requirements-fastapi.txt .
RUN pip install --no-cache-dir -r requirements-fastapi.txt

# Install Playwright and its system dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy all FastAPI backend app files
COPY backend/ .

# Copy built React assets from the frontend builder stage
# main.py expects a folder named 'dist'
COPY --from=frontend-builder /frontend/dist ./dist

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
