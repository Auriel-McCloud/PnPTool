# Produktiv-Image: fertiges Vite-Bundle hinter nginx.
# Lokal bleibt `npm run dev` — dieses Image ist für bebop (und docker compose).
# Lauscht auf 5173, damit der Host-nginx unverändert auf 127.0.0.1:5173 zeigt.

FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 5173
