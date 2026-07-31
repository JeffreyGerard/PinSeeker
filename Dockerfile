# Build Stage for React Frontend
FROM node:20-alpine AS frontend-builder

ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_STORAGE_BUCKET
ARG VITE_FIREBASE_MESSAGING_SENDER_ID
ARG VITE_FIREBASE_APP_ID

ENV VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY
ENV VITE_FIREBASE_AUTH_DOMAIN=$VITE_FIREBASE_AUTH_DOMAIN
ENV VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID
ENV VITE_FIREBASE_STORAGE_BUCKET=$VITE_FIREBASE_STORAGE_BUCKET
ENV VITE_FIREBASE_MESSAGING_SENDER_ID=$VITE_FIREBASE_MESSAGING_SENDER_ID
ENV VITE_FIREBASE_APP_ID=$VITE_FIREBASE_APP_ID

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Production Stage for FastAPI
FROM python:3.11-slim-bookworm

# Install system dependencies needed for Playwright/Chromium and Tailscale
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Install Tailscale
RUN curl -fsSL https://tailscale.com/install.sh | sh

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

# Copy the startup script and make it executable
COPY start.sh .
RUN chmod +x start.sh

# Run as non-root user for security
# Note: Tailscale userspace mode does not require root
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Run the application via the startup script
CMD ["./start.sh"]
