FROM node:20-alpine as builder

LABEL maintainer="Sahool Yemen <dev@sahool.ye>"
LABEL description="Field Suite Frontend - سهول اليمن"

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

LABEL maintainer="Sahool Yemen <dev@sahool.ye>"
LABEL description="Field Suite Frontend Production - سهول اليمن"

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
