#!/usr/bin/env bash
# =============================================================================
# PlayWave Player — Build Android APK (Capacitor)
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "==> Verificando pré-requisitos"
command -v java  >/dev/null || { echo "ERRO: Java não encontrado. Instale JDK 17+"; exit 1; }
command -v node  >/dev/null || { echo "ERRO: Node.js não encontrado"; exit 1; }
[ -n "${ANDROID_HOME:-}" ] || { echo "ERRO: ANDROID_HOME não definido"; exit 1; }

echo "==> [1/4] Build do frontend React"
cd "$FRONTEND_DIR"
npm install --legacy-peer-deps
VITE_PLAYER_MODE=capacitor npm run build

echo "==> [2/4] Sync Capacitor"
npx cap sync android

echo "==> [3/4] Build APK Debug"
cd "$FRONTEND_DIR/android"
./gradlew assembleDebug

APK_PATH="$FRONTEND_DIR/android/app/build/outputs/apk/debug/app-debug.apk"
echo "==> [4/4] Pronto!"
echo "APK gerado: $APK_PATH"
ls -lh "$APK_PATH"

echo ""
echo "Para instalar em dispositivo conectado via ADB:"
echo "  adb install -r $APK_PATH"
