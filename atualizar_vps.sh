#!/bin/bash

###############################################################################
# 🚀 SCRIPT DE ATUALIZAÇÃO VPS - PLAYWAVE
#
# Atualiza o código na VPS e reinicia os containers
###############################################################################

set -e

VPS_HOST="root@2.24.81.194"
VPS_PATH="/root/playwave"  # Ajustar se necessário

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 ATUALIZANDO PLAYWAVE NA VPS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📡 Conectando na VPS: ${VPS_HOST}${NC}"
echo ""

# Função para executar comando na VPS
vps_exec() {
    echo -e "${YELLOW}▶ $1${NC}"
    ssh ${VPS_HOST} "$1"
}

# 1. Verificar diretório
echo -e "${BLUE}1️⃣  Verificando diretório do projeto...${NC}"
vps_exec "ls -la /root/ | grep -i play || echo 'Listando /root:' && ls -la /root/"
echo ""

# 2. Encontrar diretório correto
echo -e "${BLUE}2️⃣  Localizando projeto...${NC}"
PROJECT_DIR=$(ssh ${VPS_HOST} "find /root -maxdepth 2 -name 'docker-compose.production.yml' -type f -exec dirname {} \; | head -1")

if [ -z "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Projeto não encontrado na VPS!${NC}"
    echo ""
    echo "Diretórios disponíveis em /root:"
    vps_exec "ls -la /root/"
    echo ""
    echo "Digite o caminho correto do projeto:"
    read -p "Caminho: " PROJECT_DIR
fi

echo -e "${GREEN}✓ Projeto encontrado em: ${PROJECT_DIR}${NC}"
echo ""

# 3. Pull do código
echo -e "${BLUE}3️⃣  Atualizando código (git pull)...${NC}"
vps_exec "cd ${PROJECT_DIR} && git pull origin main"
echo ""

# 4. Verificar docker-compose
echo -e "${BLUE}4️⃣  Verificando containers...${NC}"
vps_exec "cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml ps"
echo ""

# 5. Rebuild e restart
echo -e "${BLUE}5️⃣  Reconstruindo containers...${NC}"
vps_exec "cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml build --no-cache"
echo ""

echo -e "${BLUE}6️⃣  Reiniciando containers...${NC}"
vps_exec "cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml down && docker-compose -f docker-compose.production.yml up -d"
echo ""

# 7. Executar migrations
echo -e "${BLUE}7️⃣  Executando migrations...${NC}"
vps_exec "cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml exec -T backend alembic upgrade head"
echo ""

# 8. Verificar logs
echo -e "${BLUE}8️⃣  Verificando logs (últimas 20 linhas)...${NC}"
echo ""
echo -e "${YELLOW}Backend:${NC}"
vps_exec "cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml logs --tail=20 backend"
echo ""
echo -e "${YELLOW}Frontend:${NC}"
vps_exec "cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml logs --tail=20 frontend"
echo ""

# 9. Status final
echo -e "${BLUE}9️⃣  Status dos containers:${NC}"
vps_exec "cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml ps"
echo ""

# 10. Testar endpoints
echo -e "${BLUE}🔟 Testando endpoints...${NC}"
echo ""

echo -e "${YELLOW}Health check backend:${NC}"
vps_exec "curl -s http://localhost:8000/api/v1/health || echo 'Backend não respondeu'"
echo ""

echo -e "${YELLOW}Frontend:${NC}"
vps_exec "curl -s -I http://localhost:80 | head -5 || echo 'Frontend não respondeu'"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ ATUALIZAÇÃO CONCLUÍDA!${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Acesse: http://playwave.com.br"
echo ""
echo "📊 Monitorar logs:"
echo "   ssh ${VPS_HOST} 'cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml logs -f'"
echo ""
echo "🔧 Comandos úteis:"
echo "   Restart:  ssh ${VPS_HOST} 'cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml restart'"
echo "   Parar:    ssh ${VPS_HOST} 'cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml down'"
echo "   Status:   ssh ${VPS_HOST} 'cd ${PROJECT_DIR} && docker-compose -f docker-compose.production.yml ps'"
echo ""
