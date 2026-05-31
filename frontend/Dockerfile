# DateNight Show Matcher — frontend (built static SPA served by nginx)
FROM oven/bun:1.3 AS build
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install
COPY . .
# Same-origin in the container image: nginx reverse-proxies /api & /health to the
# backend, so no API base is baked in. (Override for other deployments.)
ARG VITE_API_BASE=""
ENV VITE_API_BASE=$VITE_API_BASE
RUN bun run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
