# PlayWave — Deploy em Produção

## Servidor

- **IP**:        2.24.81.194
- **Domínio**:   playwave.com.br (+ www.playwave.com.br)
- **SSH**:       `ssh root@2.24.81.194`
- **Senha**:     `Pl@ywave2026`

## Pré-requisitos no servidor

1. DNS apontando:
   - `playwave.com.br      A   2.24.81.194`
   - `www.playwave.com.br  A   2.24.81.194`
2. Portas abertas no firewall: `22`, `80`, `443`
3. Docker + Docker Compose instalados

```bash
# Instalar Docker (uma vez)
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

## Deploy passo a passo

### 1. Subir o código no servidor

```bash
ssh root@2.24.81.194

# Clonar o repositório
cd /opt
git clone https://github.com/AndrekaiqueDevjunior/Play-Wave-Aplicativo.git playwave
cd playwave
```

### 2. Inicializar SSL (uma vez só)

```bash
chmod +x deploy/init-ssl.sh
./deploy/init-ssl.sh
```

Esse script:
1. Cria os diretórios `nginx/certbot/conf` e `nginx/certbot/www`
2. Gera um certificado dummy para o Nginx subir
3. Solicita o certificado real via Let's Encrypt (HTTP-01 challenge)
4. Recarrega o Nginx com o cert real

### 3. Subir todos os serviços

```bash
docker compose -f docker-compose.production.yml up -d --build
```

### 4. Verificar saúde

```bash
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs -f backend
curl https://playwave.com.br/health
```

### 5. Aplicar migrations do banco

```bash
docker compose -f docker-compose.production.yml exec backend alembic upgrade head
```

## Credenciais iniciais

| Tipo       | Email                  | Senha                        |
|------------|------------------------|------------------------------|
| Admin      | admin@playwave.com     | `&2p0Kw45A&lLNX4bM%gpH*cy`   |
| Operador   | operador@playwave.com  | `Troque@456!`                |

**Trocar a senha do operador no primeiro acesso.**

## Comandos úteis

```bash
# Logs de um serviço
docker compose -f docker-compose.production.yml logs -f backend

# Reiniciar um serviço
docker compose -f docker-compose.production.yml restart backend

# Atualizar código e re-deploy
git pull
docker compose -f docker-compose.production.yml up -d --build

# Backup do banco
docker compose -f docker-compose.production.yml exec postgres \
  pg_dump -U playwave playwave > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
cat backup.sql | docker compose -f docker-compose.production.yml exec -T postgres \
  psql -U playwave playwave

# Renovar SSL manualmente
docker compose -f docker-compose.production.yml run --rm certbot renew

# Parar tudo
docker compose -f docker-compose.production.yml down

# Parar + apagar volumes (CUIDADO: apaga dados)
docker compose -f docker-compose.production.yml down -v
```

## Atualização contínua

```bash
ssh root@2.24.81.194
cd /opt/playwave
git pull
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml exec backend alembic upgrade head
```

## Monitoramento

```bash
# Uso de recursos
docker stats

# Espaço em disco dos volumes
docker system df

# Limpar imagens antigas
docker image prune -af
```

## Checklist de produção

- [ ] DNS apontando para 2.24.81.194
- [ ] Portas 80/443 abertas no firewall
- [ ] `init-ssl.sh` executado com sucesso
- [ ] HTTPS funcionando (`curl -I https://playwave.com.br`)
- [ ] Login admin funcionando
- [ ] Backend `/health` respondendo `200`
- [ ] Migrations aplicadas
- [ ] **Trocar `SECRET_KEY` no `docker-compose.production.yml`** (atualmente é um placeholder)
- [ ] **Trocar senhas de Postgres/Redis/RabbitMQ** (rotação periódica)
- [ ] Configurar backup automático do Postgres
- [ ] Configurar monitoramento (Uptime Robot, Prometheus etc.)
