# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app (outputs to /app/dist)
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:alpine

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built React app from the previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Start script to inject runtime environment variables
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "window.ENV = { BACKEND_URL: \"${BACKEND_URL}\" };" > /usr/share/nginx/html/env.js' >> /start.sh && \
    echo 'nginx -g "daemon off;"' >> /start.sh && \
    chmod +x /start.sh

# Expose the port (we match Cloud Run's expected port configured in deploy.yml)
EXPOSE 8501

# Start Nginx
CMD ["/start.sh"]
