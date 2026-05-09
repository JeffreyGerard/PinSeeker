# Build Stage for React Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Production Stage for FastAPI
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

WORKDIR /app

# Copy python dependencies
COPY backend/requirements-fastapi.txt .
RUN pip install --no-cache-dir -r requirements-fastapi.txt

# Copy FastAPI app code
COPY backend/main.py .

# Copy built React assets from the frontend builder stage
# main.py expects a folder named 'dist'
COPY --from=frontend-builder /frontend/dist ./dist

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
