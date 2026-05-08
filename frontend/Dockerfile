# ===========================================
# ESTÁGIO DE BUILD
# ===========================================
# node:20-bookworm-slim usa glibc (Debian), evitando o mismatch
# @rollup/rollup-linux-x64-musl que ocorre com Alpine (musl libc)
FROM node:20-bookworm-slim AS build-stage

ARG VITE_API_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000/ws

# Não setar NODE_ENV=production antes do npm ci — isso faria o npm
# omitir devDependencies, que incluem o próprio Vite.
# NODE_ENV é passado inline só para o build, garantindo output minificado.
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --silent

COPY . .
RUN NODE_ENV=production npm run build

# ===========================================
# ESTÁGIO DE PRODUÇÃO
# ===========================================
FROM nginx:alpine AS production-stage

RUN apk add --no-cache curl

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
