# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app/api

# Copiar package files
COPY api/package.json api/package-lock.json ./

# Instalar dependências (incluindo dev para build)
RUN npm ci

# Copiar código-fonte
COPY api/src ./src
COPY api/tsconfig*.json ./

# Build TypeScript
RUN npm run build

# Stage 2: Runtime
FROM node:22-alpine

WORKDIR /app

# Extrator de PDF (POST /api/extracao): python3 + pdftotext
RUN apk add --no-cache python3 poppler-utils

# Copiar package files
COPY api/package.json api/package-lock.json ./api/

# Instalar apenas dependências de produção
RUN cd api && npm ci --omit=dev

# Copiar dist do build
COPY --from=builder /app/api/dist ./api/dist

# Copiar pasta revista (necessária em runtime)
COPY revista ./revista

# Extrator de descritores (resolvido como /app/scripts/ a partir de dist/modules/extracao)
COPY scripts/extrair_descritores.py ./scripts/extrair_descritores.py

# Criar usuário node e mudar propriedade
RUN chown -R node:node /app

USER node

WORKDIR /app/api

CMD ["node", "dist/server.js"]
