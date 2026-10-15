# Build stage
FROM node:24-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# Runtime stage
FROM nginx:1.27-alpine AS runtime
RUN addgroup -S appuser && adduser -S -G appuser appuser

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R appuser:appuser /usr/share/nginx/html

USER appuser
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]