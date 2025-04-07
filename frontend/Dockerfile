# Stage 1: Build the React application
FROM node:16-alpine AS builder

WORKDIR /app

# Declare build arguments
ARG REACT_APP_GOOGLE_CLIENT_ID

# Set environment variables from build arguments for the build process
ENV REACT_APP_GOOGLE_CLIENT_ID=$REACT_APP_GOOGLE_CLIENT_ID

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application for production
RUN npm run build

# --- Stage 2: Serve the application with Nginx ---

# Use a specific stable version of Nginx based on Alpine Linux
FROM nginx:1.25-alpine

# Set working directory (optional, but good practice)
WORKDIR /usr/share/nginx/html

# Remove default Nginx welcome page
RUN rm -rf ./*

# Copy built assets from the builder stage
COPY --from=builder /app/build .

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx in the foreground when the container launches
CMD ["nginx", "-g", "daemon off;"]
