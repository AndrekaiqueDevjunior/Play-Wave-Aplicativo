#!/bin/bash
# =============================================================================
# PlayWave - Script de Deploy Rápido em VPS
# =============================================================================
# Uso: ./deploy-quick.sh
# =============================================================================

set -e  # Parar em caso de erro

echo "🚀 PlayWave - Deploy Rápido em VPS"
echo "===================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está rodando como root ou com sudo
if [[ $EUID -ne 0 ]]; then
   log_error "Este script precisa ser executado como root ou com sudo"
   exit 1
fi

# =============================================================================
# PASSO 1: Verificar Pré-requisitos
# =============================================================================
log_info "Verificando pré-requisitos..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker não está instalado. Instale com: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose não está instalado."
    exit 1
fi

log_info "✓ Docker e Docker Compose instalados"

# =============================================================================
# PASSO 2: Verificar Estrutura do Projeto
# =============================================================================
log_info "Verificando estrutura do projeto..."

if [ ! -f "docker-compose.production.yml" ]; then
    log_error "Arquivo docker-compose.production.yml não encontrado"
    exit 1
fi

if [ ! -d "backend" ] || [ ! -d "frontend" ] || [ ! -d "nginx" ]; then
    log_error "Diretórios backend/, frontend/ ou nginx/ não encontrados"
    exit 1
fi

log_info "✓ Estrutura do projeto OK"

# =============================================================================
# PASSO 3: Verificar Senhas de Produção
# =============================================================================
log_warn "⚠️  IMPORTANTE: Verifique se você alterou as senhas de produção em docker-compose.production.yml"
echo ""
echo "Senhas que devem ser alteradas:"
echo "  - POSTGRES_PASSWORD (linha 28)"
echo "  - REDIS_PASSWORD (linha 51)"
echo "  - RABBITMQ_DEFAULT_PASS (linha 75)"
echo "  - SECRET_KEY (linha 134)"
echo "  - ADMIN_INITIAL_PASSWORD (linha 152)"
echo ""
read -p "Você já alterou as senhas? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    log_error "Altere as senhas antes de continuar!"
    exit 1
fi

# =============================================================================
# PASSO 4: Criar Diretórios Necessários
# =============================================================================
log_info "Criando diretórios necessários..."

mkdir -p nginx/certbot/www
mkdir -p nginx/certbot/conf
mkdir -p backend/uploads/media
mkdir -p backend/uploads/audio/tracks
mkdir -p backend/logs
mkdir -p backups

log_info "✓ Diretórios criados"

# =============================================================================
# PASSO 5: Parar Containers Antigos (se existirem)
# =============================================================================
log_info "Parando containers antigos (se existirem)..."

docker-compose -f docker-compose.production.yml down 2>/dev/null || true

log_info "✓ Containers antigos parados"

# =============================================================================
# PASSO 6: Build das Imagens
# =============================================================================
log_info "Fazendo build das imagens Docker..."
log_warn "Isso pode levar 5-10 minutos..."

docker-compose -f docker-compose.production.yml build --no-cache

log_info "✓ Build concluído"

# =============================================================================
# PASSO 7: Subir os Serviços
# =============================================================================
log_info "Subindo os serviços..."

docker-compose -f docker-compose.production.yml up -d

log_info "✓ Serviços iniciados"

# =============================================================================
# PASSO 8: Aguardar Serviços Ficarem Healthy
# =============================================================================
log_info "Aguardando serviços ficarem prontos..."

sleep 10

# Verificar status
log_info "Verificando status dos containers..."
docker-compose -f docker-compose.production.yml ps

# =============================================================================
# PASSO 9: Executar Migrations
# =============================================================================
log_info "Executando migrations do banco de dados..."

# Aguardar backend ficar pronto
sleep 5

docker-compose -f docker-compose.production.yml exec -T backend alembic upgrade head

log_info "✓ Migrations executadas"

# =============================================================================
# PASSO 10: Verificar Deploy
# =============================================================================
log_info "Verificando deploy..."

# Verificar backend
if docker-compose -f docker-compose.production.yml exec -T backend curl -f http://localhost:8000/health &> /dev/null; then
    log_info "✓ Backend respondendo"
else
    log_warn "⚠️  Backend não está respondendo ainda"
fi

# Verificar containers
CONTAINERS_UP=$(docker-compose -f docker-compose.production.yml ps | grep -c "Up" || true)
log_info "Containers rodando: $CONTAINERS_UP"

# =============================================================================
# FINALIZAÇÃO
# =============================================================================
echo ""
echo "=========================================="
echo "✅ Deploy Concluído!"
echo "=========================================="
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Verificar logs:"
echo "   docker-compose -f docker-compose.production.yml logs -f"
echo ""
echo "2. Verificar status:"
echo "   docker-compose -f docker-compose.production.yml ps"
echo ""
echo "3. Testar backend:"
echo "   curl http://localhost:8000/health"
echo ""
echo "4. Configurar SSL (se ainda não configurado):"
echo "   ./deploy/init-ssl.sh playwave.com.br admin@playwave.com"
echo ""
echo "5. Acessar aplicação:"
echo "   http://seu-ip-ou-dominio"
echo ""
echo "=========================================="
echo ""

# Mostrar logs em tempo real
log_info "Mostrando logs (Ctrl+C para sair)..."
sleep 2
docker-compose -f docker-compose.production.yml logs -f
