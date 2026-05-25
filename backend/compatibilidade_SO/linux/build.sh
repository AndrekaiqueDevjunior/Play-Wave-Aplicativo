#!/usr/bin/env bash
# =============================================================================
# PlayWave Player — Build Linux (AppImage + .deb + .rpm)
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
ELECTRON_DIR="$FRONTEND_DIR/electron"

echo "==> [1/4] Build do frontend React"
cd "$FRONTEND_DIR"
npm install --legacy-peer-deps
VITE_PLAYER_MODE=electron npm run build

echo "==> [2/4] Instalar dependências do Electron"
cd "$ELECTRON_DIR"
npm install

echo "==> [3/4] Build Linux"
npm run build:linux

echo "==> [4/4] Pronto!"
echo "Arquivos gerados em: $ELECTRON_DIR/dist-electron/"
ls -lh "$ELECTRON_DIR/dist-electron/"
