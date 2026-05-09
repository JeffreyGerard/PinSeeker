# Use the official Playwright Linux image
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Install Xvfb (Virtual Display) so we can run "headed" code in Linux
RUN apt-get update && apt-get install -y xvfb

WORKDIR /app

# Pre-install playwright browsers into the image to save time
RUN pip install playwright && playwright install chromium && playwright install-deps chromium