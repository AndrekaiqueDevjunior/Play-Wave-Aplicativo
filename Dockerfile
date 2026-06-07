# Build stage para compilar o frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copiar frontend completo
COPY frontend/ ./frontend/

# Instalar dependências do electron
WORKDIR /app/frontend/electron
RUN npm ci

# Build do Electron para Linux
RUN npm run build:linux

# Runtime stage
FROM ubuntu:22.04

# Instalar dependências do Electron e sistema
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libnotify4 \
    libgconf-2-4 \
    libappindicator1 \
    libnss3 \
    libxss1 \
    fonts-liberation \
    xdg-utils \
    libasound2 \
    libxext6 \
    libxrandr2 \
    libgbm1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário playwave (segurança)
RUN useradd -m -s /bin/bash playwave

WORKDIR /app

# Copiar build do frontend
COPY --from=frontend-builder /app/frontend/electron/dist-electron/ ./

# Definir permissões
RUN chown -R playwave:playwave /app

# Trocar para usuário não-root
USER playwave

# Variáveis de ambiente padrão
ENV DISPLAY=:0
ENV NODE_ENV=production
ENV VITE_API_URL=http://localhost:8000
ENV VITE_PLAYER_URL=http://localhost:3000/player

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5173/health || exit 1

# Entrypoint
CMD ["./PlayWave"]
