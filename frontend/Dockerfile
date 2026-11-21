# Stage 1: Build React application
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies using clean install
COPY package*.json ./
RUN npm ci

# Copy frontend source
COPY . .

# Build-time API URL configuration (defaults to http://localhost:8000)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Build production bundle
RUN npm run build

# Stage 2: Serve production bundle with Nginx
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
