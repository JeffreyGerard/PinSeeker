# Use an official Node runtime as a parent image
FROM node:20-alpine

# Set work directory
WORKDIR /app

# Install dependencies
# Copying package.json first allows Docker to cache the npm install step
COPY package.json .
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5173

# Start the application
# --host 0.0.0.0 is required for Docker to expose the port
CMD ["npm", "run", "dev", "--", "--host"]
