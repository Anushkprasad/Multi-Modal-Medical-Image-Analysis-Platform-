# Step 1: Build the React application using Vite
FROM node:20-alpine AS build
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy the rest of the source code and build the production bundle
COPY . .
RUN npm run build

# Step 2: Serve the build directory using Nginx
FROM nginx:1.25-alpine

# Copy the build output from the previous stage to the Nginx public folder
COPY --from=build /app/dist /usr/share/nginx/html

# Copy our custom Nginx config for handling Single Page App (SPA) routes
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for traffic
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
