#!/usr/bin/env bash
# =============================================================================
# PlayWave — Inicialização SSL (Let's Encrypt) — rodar UMA vez
# =============================================================================
set -euo pipefail

DOMAIN="playwave.com.br"
EMAIL="suporte@playwave.com.br"   # email para notificações Let's Encrypt
STAGING=0                          # 1 = ambiente de teste (não conta no rate limit)

DATA_PATH="./nginx/certbot"

if [ -d "$DATA_PATH/conf/live/$DOMAIN" ]; then
  echo "[!] Certificados para $DOMAIN já existem. Abortando para não sobrescrever."
  echo "    Para forçar, remova $DATA_PATH/conf/live/$DOMAIN e rode novamente."
  exit 1
fi

echo "==> [1/5] Criando diretórios..."
mkdir -p "$DATA_PATH/conf"
mkdir -p "$DATA_PATH/www"

echo "==> [2/5] Baixando parâmetros SSL recomendados..."
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$DATA_PATH/conf/options-ssl-nginx.conf"
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem  > "$DATA_PATH/conf/ssl-dhparams.pem"

echo "==> [3/5] Gerando certificado temporário (dummy) para Nginx subir..."
DUMMY_PATH="/etc/letsencrypt/live/$DOMAIN"
mkdir -p "$DATA_PATH/conf/live/$DOMAIN"
docker compose -f docker-compose.production.yml run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
    -keyout '$DUMMY_PATH/privkey.pem' \
    -out '$DUMMY_PATH/fullchain.pem' \
    -subj '/CN=localhost'" certbot

echo "==> [4/5] Subindo Nginx com cert temporário..."
docker compose -f docker-compose.production.yml up -d nginx
sleep 5

echo "==> [5/5] Removendo cert temporário e solicitando o real..."
docker compose -f docker-compose.production.yml run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/$DOMAIN && \
  rm -rf /etc/letsencrypt/archive/$DOMAIN && \
  rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf" certbot

STAGING_ARG=""
if [ $STAGING -ne 0 ]; then STAGING_ARG="--staging"; fi

docker compose -f docker-compose.production.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    -d $DOMAIN -d www.$DOMAIN \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

echo "==> Recarregando Nginx com certificado real..."
docker compose -f docker-compose.production.yml exec nginx nginx -s reload

echo ""
echo "✓ SSL configurado para $DOMAIN"
echo "  Os certificados serão renovados automaticamente pelo serviço 'certbot'."
