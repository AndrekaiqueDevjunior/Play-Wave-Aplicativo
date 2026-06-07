#!/bin/bash

# PlayWave — Script de Build Docker
# Uso: bash build-docker.sh [TAG]

set -e

TAG=${1:-"latest"}
REGISTRY=${REGISTRY:-"playwave"}
IMAGE_NAME="${REGISTRY}/playwave:${TAG}"

echo "=========================================="
echo "PlayWave — Build Docker"
echo "=========================================="
echo ""
echo "📦 Imagem: $IMAGE_NAME"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale em: https://docker.com"
    exit 1
fi

echo "[1/3] Verificando Docker..."
docker --version
echo "✅ Docker pronto"
echo ""

# Build
echo "[2/3] Compilando imagem Docker..."
docker build -t "$IMAGE_NAME" .
if [ $? -ne 0 ]; then
    echo "❌ Erro ao compilar"
    exit 1
fi
echo "✅ Imagem compilada"
echo ""

# Sucesso
echo "[3/3] Finalizando..."
echo ""
echo "=========================================="
echo "✨ Build Concluído!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo ""
echo "1️⃣  Executar com docker-compose:"
echo "   docker-compose up -d"
echo ""
echo "2️⃣  Ou manualmente:"
echo "   docker run -d --name playwave-player \\"
echo "     -e VITE_PLAYER_URL='https://seu-servidor/player' \\"
echo "     -v playwave-config:/home/playwave/.config/PlayWave \\"
echo "     $IMAGE_NAME"
echo ""
echo "3️⃣  Ver logs:"
echo "   docker logs -f playwave-player"
echo ""
