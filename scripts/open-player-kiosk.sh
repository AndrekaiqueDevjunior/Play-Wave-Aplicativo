#!/usr/bin/env bash
# Abre o Play Wave Player no Chrome sem política de autoplay.
# Ideal para TVs e quiosques digitais.

URL="${1:-http://127.0.0.1:3500/player}"

# Tenta chromium-browser, google-chrome, chromium (nesta ordem)
# As 3 flags --disable-background-* evitam que o Chromium congele os
# setIntervals (heartbeat, polling de comandos, watchdog) quando a aba
# perde foco/visibilidade — sem elas a TV "some" do painel sem erro
# algum até alguém reiniciar o app manualmente.
for bin in chromium-browser google-chrome chromium; do
  if command -v "$bin" &>/dev/null; then
    exec "$bin" \
      --autoplay-policy=no-user-gesture-required \
      --disable-features=PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies,CalculateNativeWinOcclusion \
      --disable-background-timer-throttling \
      --disable-backgrounding-occluded-windows \
      --disable-renderer-backgrounding \
      --no-first-run \
      --noerrdialogs \
      --disable-infobars \
      "$URL"
  fi
done

echo "Nenhum browser Chrome/Chromium encontrado." >&2
exit 1
