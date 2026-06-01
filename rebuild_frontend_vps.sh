#!/bin/bash

###############################################################################
# 🧹 REBUILD COMPLETO DO FRONTEND - LIMPAR CACHE
#
# Executa na VPS para forçar rebuild total do frontend
###############################################################################

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🧹 LIMPANDO CACHE E RECONSTRUINDO FRONTEND"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

VPS_HOST="root@2.24.81.194"

echo -e "${BLUE}📡 Conectando na VPS...${NC}"
echo ""

# Executar comandos na VPS
ssh ${VPS_HOST} << 'ENDSSH'

# Encontrar projeto
PROJECT_DIR=$(find /root -maxdepth 2 -name "docker-compose.production.yml" -type f -exec dirname {} \; | head -1)

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ Projeto não encontrado!"
    exit 1
fi

echo "✓ Projeto encontrado em: $PROJECT_DIR"
cd "$PROJECT_DIR"

echo ""
echo "1️⃣  Parando containers..."
docker-compose -f docker-compose.production.yml down

echo ""
echo "2️⃣  Removendo imagens antigas do frontend..."
docker rmi $(docker images | grep playwave-frontend | awk '{print $3}') 2>/dev/null || echo "Nenhuma imagem antiga encontrada"

echo ""
echo "3️⃣  Removendo imagens antigas do backend..."
docker rmi $(docker images | grep playwave-backend | awk '{print $3}') 2>/dev/null || echo "Nenhuma imagem antiga encontrada"

echo ""
echo "4️⃣  Limpando cache do Docker..."
docker builder prune -af
docker system prune -af

echo ""
echo "5️⃣  Atualizando código (git pull)..."
git fetch origin
git reset --hard origin/main
git pull origin main

echo ""
echo "6️⃣  Rebuild TOTAL sem cache..."
docker-compose -f docker-compose.production.yml build --no-cache --pull

echo ""
echo "7️⃣  Subindo containers..."
docker-compose -f docker-compose.production.yml up -d

echo ""
echo "8️⃣  Aguardando containers iniciarem..."
sleep 10

echo ""
echo "9️⃣  Status dos containers:"
docker-compose -f docker-compose.production.yml ps

echo ""
echo "🔟 Logs do frontend (últimas 20 linhas):"
docker-compose -f docker-compose.production.yml logs --tail=20 frontend

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ REBUILD CONCLUÍDO!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Acesse: http://playwave.com.br"
echo ""
echo "⚠️  IMPORTANTE: Limpe o cache do navegador!"
echo "   Chrome/Edge: Ctrl + Shift + Delete"
echo "   Ou abra em aba anônima: Ctrl + Shift + N"
echo ""
echo "🔍 Verificar arquivos do frontend:"
echo "   docker-compose -f docker-compose.production.yml exec frontend ls -lah /usr/share/nginx/html/"
echo ""

ENDSSH

echo ""
echo -e "${GREEN}✅ Processo concluído!${NC}"
echo ""
echo -e "${YELLOW}Próximos passos:${NC}"
echo "1. Abrir http://playwave.com.br em aba anônima"
echo "2. F12 → Network → Marcar 'Disable cache'"
echo "3. Login → Dispositivos → Ver detalhes"
echo "4. Console deve mostrar: [DispositivoDetalhe] Componente montado"
echo ""
