# ===========================================
# ESTÁGIO DE BUILD
# ===========================================
FROM node:18-alpine as build-stage

# ===========================================
# CONFIGURAÇÕES DE AMBIENTE
# ===========================================
ENV NODE_ENV=production
ENV VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_WS_URL=ws://localhost:8000/ws

# ===========================================
# DIRETÓRIO DE TRABALHO
# ===========================================
WORKDIR /app

# ===========================================
# COPIA E INSTALAÇÃO DE DEPENDÊNCIAS
# ===========================================
COPY package*.json ./
RUN npm ci --only=production --silent

# ===========================================
# COPIA DO CÓDIGO FONTE
# ===========================================
COPY . .

# ===========================================
# BUILD DA APLICAÇÃO
# ===========================================
RUN npm run build

# ===========================================
# ESTÁGIO DE PRODUÇÃO
# ===========================================
FROM nginx:alpine as production-stage

# ===========================================
# INSTALAÇÃO DE FERRAMENTAS ADICIONAIS
# ===========================================
RUN apk add --no-cache curl

# ===========================================
# COPIA DO BUILD PARA NGINX
# ===========================================
COPY --from=build-stage /app/dist /usr/share/nginx/html

# ===========================================
# CONFIGURAÇÃO DO NGINX
# ===========================================
COPY nginx.conf /etc/nginx/nginx.conf

# ===========================================
# EXPOSIÇÃO DA PORTA
# ===========================================
EXPOSE 5173

# ===========================================
# COMANDO DE INICIALIZAÇÃO
# ===========================================
CMD ["nginx", "-g", "daemon off;"]
