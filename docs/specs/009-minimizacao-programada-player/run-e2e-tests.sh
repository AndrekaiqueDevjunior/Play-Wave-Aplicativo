#!/bin/bash

# SPEC 009 - Executar Testes E2E Automatizados
# Uso: bash run-e2e-tests.sh

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║     SPEC 009 - Testes E2E Automatizados                ║"
echo "║     Desktop Exposure / Window Control                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Encontrar diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../../" && pwd )"

echo "📁 Diretórios:"
echo "   Projeto: $PROJECT_ROOT"
echo "   Spec 009: $SCRIPT_DIR"
echo ""

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado!"
    echo "   Instale em: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v)
echo "✓ Node.js: $NODE_VERSION"
echo ""

# Rodar testes
echo "▶ Executando testes E2E..."
echo ""

node "$SCRIPT_DIR/test-e2e-automated.js"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║              ✓ TESTES APROVADOS                        ║"
    echo "║     SPEC 009 está pronta para produção!                ║"
    echo "╚════════════════════════════════════════════════════════╝"
else
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║              ✗ TESTES FALHARAM                         ║"
    echo "║     Verifique os erros acima                           ║"
    echo "╚════════════════════════════════════════════════════════╝"
fi

exit $EXIT_CODE
