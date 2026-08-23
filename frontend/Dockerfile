FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
# Types must be regenerable from the canonical schemas at build time.
COPY schemas /schemas-src
RUN mkdir -p /app/schemas && cp -r /schemas-src/* /app/schemas/ && npm run generate:types && rm -rf /app/schemas
RUN npm run build

FROM nginx:alpine
COPY infra/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
