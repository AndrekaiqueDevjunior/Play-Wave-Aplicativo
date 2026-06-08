#!/usr/bin/env bash
# Abre o Play Wave Player no Chrome sem política de autoplay.
# Ideal para TVs e quiosques digitais.

URL="${1:-http://127.0.0.1:3500/player}"

# Tenta chromium-browser, google-chrome, chromium (nesta ordem)
for bin in chromium-browser google-chrome chromium; do
  if command -v "$bin" &>/dev/null; then
    exec "$bin" \
      --autoplay-policy=no-user-gesture-required \
      --disable-features=PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies \
      --no-first-run \
      --noerrdialogs \
      --disable-infobars \
      "$URL"
  fi
done

echo "Nenhum browser Chrome/Chromium encontrado." >&2
exit 1
