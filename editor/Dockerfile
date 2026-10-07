# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app

# Copiar package files
COPY package.json package-lock.json ./

# Instalar dependências
RUN npm ci

# Copiar código-fonte
COPY src ./src
COPY index.html ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY public ./public

# Build com Vite
RUN npm run build

# Stage 2: nginx
FROM nginx:alpine

# Copiar nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar dist do build
COPY --from=builder /app/dist /usr/share/nginx/html

# Remover mockServiceWorker.js (não deve ir para produção)
RUN rm -f /usr/share/nginx/html/mockServiceWorker.js

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
