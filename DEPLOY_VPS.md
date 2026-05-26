# 🚀 GUIA DE DEPLOY EM VPS - PLAYWAVE
**Data:** 26 de Maio de 2026  
**Servidor:** 2.24.81.194  
**Domínio:** playwave.com.br

---

## 📋 PRÉ-REQUISITOS

### Servidor VPS
- **IP:** 2.24.81.194
- **OS:** Ubuntu 20.04+ ou Debian 11+
- **RAM:** Mínimo 4GB (recomendado 8GB)
- **CPU:** Mínimo 2 cores (recomendado 4 cores)
- **Disco:** Mínimo 40GB SSD
- **Acesso:** SSH com usuário root ou sudo

### Domínio
- **Domínio:** playwave.com.br
- **DNS Configurado:**
  - `A` record: `playwave.com.br` → `2.24.81.194`
  - `A` record: `www.playwave.com.br` → `2.24.81.194`

### Portas Necessárias
- **80** (HTTP) - Aberta
- **443** (HTTPS) - Aberta
- **22** (SSH) - Aberta (para acesso)

---

## 🔧 PASSO 1: PREPARAR O SERVIDOR

### 1.1. Conectar ao Servidor
```bash
ssh root@2.24.81.194
# ou
ssh usuario@2.24.81.194
```

### 1.2. Atualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3. Instalar Docker e Docker Compose
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker (opcional)
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker --version
docker-compose --version
```

### 1.4. Instalar Git
```bash
sudo apt install git -y
git --version
```

### 1.5. Configurar Firewall (UFW)
```bash
# Instalar UFW
sudo apt install ufw -y

# Configurar regras
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Ativar firewall
sudo ufw enable

# Verificar status
sudo ufw status
```

---

## 📦 PASSO 2: CLONAR O PROJETO

### 2.1. Criar Diretório de Deploy
```bash
sudo mkdir -p /opt/playwave
sudo chown -R $USER:$USER /opt/playwave
cd /opt/playwave
```

### 2.2. Clonar Repositório
```bash
# Se usar Git
git clone https://github.com/seu-usuario/Play-Wave-Aplicativo.git .

# OU copiar via SCP do local
# No seu computador local:
# scp -r /home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/* root@2.24.81.194:/opt/playwave/
```

### 2.3. Verificar Estrutura
```bash
ls -la
# Deve mostrar:
# backend/
# frontend/
# nginx/
# docker-compose.production.yml
# etc.
```

---

## 🔐 PASSO 3: CONFIGURAR VARIÁVEIS DE AMBIENTE

### 3.1. Revisar docker-compose.production.yml
```bash
nano docker-compose.production.yml
```

**⚠️ IMPORTANTE: Trocar as senhas de produção!**

Procure e altere:
- `POSTGRES_PASSWORD` (linha 28)
- `REDIS_PASSWORD` (linha 51)
- `RABBITMQ_DEFAULT_PASS` (linha 75)
- `SECRET_KEY` (linha 134)
- `ADMIN_INITIAL_PASSWORD` (linha 152)
- `OPERATOR_INITIAL_PASSWORD` (linha 154)

**Exemplo de senhas fortes:**
```yaml
POSTGRES_PASSWORD: 'Tr0c@rP0rS3nh@F0rt3!2026'
SECRET_KEY: "PROD_$(openssl rand -hex 32)"
ADMIN_INITIAL_PASSWORD: "Adm1n@Pl@yW@v3!2026"
```

### 3.2. Verificar Domínio
Confirme que o domínio está correto (linha 279):
```yaml
VITE_API_URL: https://playwave.com.br
VITE_WS_URL:  wss://playwave.com.br/ws
```

E no CORS (linha 148):
```yaml
ALLOWED_ORIGINS: "https://playwave.com.br,https://www.playwave.com.br,https://localhost,capacitor://localhost"
```

---

## 🔒 PASSO 4: CONFIGURAR SSL (Let's Encrypt)

### 4.1. Verificar DNS
```bash
# Verificar se DNS está propagado
nslookup playwave.com.br
ping playwave.com.br
```

**Resultado esperado:** Deve retornar `2.24.81.194`

### 4.2. Criar Diretórios do Certbot
```bash
mkdir -p nginx/certbot/www
mkdir -p nginx/certbot/conf
```

### 4.3. Executar Script de Inicialização SSL
```bash
chmod +x deploy/init-ssl.sh
./deploy/init-ssl.sh playwave.com.br admin@playwave.com
```

**O que o script faz:**
1. Sobe Nginx em modo HTTP temporário
2. Solicita certificado SSL do Let's Encrypt
3. Reconfigura Nginx para HTTPS
4. Reinicia serviços

### 4.4. Verificar Certificado
```bash
sudo ls -la nginx/certbot/conf/live/playwave.com.br/
# Deve mostrar:
# cert.pem
# chain.pem
# fullchain.pem
# privkey.pem
```

---

## 🚀 PASSO 5: FAZER O DEPLOY

### 5.1. Build das Imagens
```bash
docker-compose -f docker-compose.production.yml build --no-cache
```

**Tempo estimado:** 5-10 minutos

### 5.2. Subir os Serviços
```bash
docker-compose -f docker-compose.production.yml up -d
```

### 5.3. Verificar Status
```bash
docker-compose -f docker-compose.production.yml ps
```

**Resultado esperado:**
```
NAME                      STATUS
playwave-postgres         Up (healthy)
playwave-redis            Up (healthy)
playwave-rabbitmq         Up (healthy)
playwave-backend          Up (healthy)
playwave-celery-worker    Up
playwave-celery-beat      Up
playwave-frontend         Up
playwave-nginx            Up (healthy)
playwave-certbot          Up
```

### 5.4. Verificar Logs
```bash
# Logs de todos os serviços
docker-compose -f docker-compose.production.yml logs -f

# Logs de um serviço específico
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f nginx
```

---

## 🗄️ PASSO 6: INICIALIZAR BANCO DE DADOS

### 6.1. Executar Migrations
```bash
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### 6.2. Verificar Migrations
```bash
docker-compose -f docker-compose.production.yml exec backend alembic current
```

### 6.3. Criar Usuário Admin (se necessário)
```bash
docker-compose -f docker-compose.production.yml exec backend python -c "
from core.database import SessionLocal
from core.models import User
from core.security import get_password_hash

db = SessionLocal()
admin = User(
    email='admin@playwave.com',
    password=get_password_hash('Adm1n@Pl@yW@v3!2026'),
    role='admin',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin criado com sucesso!')
"
```

---

## ✅ PASSO 7: VERIFICAR DEPLOY

### 7.1. Testar Backend
```bash
curl https://playwave.com.br/health
# Resultado esperado: {"status":"ok"}

curl https://playwave.com.br/api/v1/health
# Resultado esperado: {"status":"healthy","version":"1.0.0"}
```

### 7.2. Testar Frontend
```bash
curl -I https://playwave.com.br
# Resultado esperado: HTTP/2 200
```

### 7.3. Abrir no Navegador
1. Acesse: https://playwave.com.br
2. Deve carregar a tela de login
3. Login com: `admin@playwave.com` / `Adm1n@Pl@yW@v3!2026`

### 7.4. Testar API
```bash
# Login
curl -X POST https://playwave.com.br/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@playwave.com","password":"Adm1n@Pl@yW@v3!2026"}'

# Deve retornar token JWT
```

---

## 🔄 PASSO 8: CONFIGURAR BACKUP AUTOMÁTICO

### 8.1. Criar Script de Backup
```bash
sudo nano /opt/playwave/backup.sh
```

```bash
#!/bin/bash
# Backup automático do PlayWave

BACKUP_DIR="/opt/playwave/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
docker-compose -f /opt/playwave/docker-compose.production.yml exec -T postgres \
  pg_dump -U playwave playwave > $BACKUP_DIR/db_$DATE.sql

# Backup dos uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/playwave/backend/uploads

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

### 8.2. Tornar Executável
```bash
chmod +x /opt/playwave/backup.sh
```

### 8.3. Configurar Cron
```bash
sudo crontab -e
```

Adicionar linha:
```cron
# Backup diário às 3h da manhã
0 3 * * * /opt/playwave/backup.sh >> /var/log/playwave-backup.log 2>&1
```

---

## 📊 PASSO 9: MONITORAMENTO

### 9.1. Verificar Uso de Recursos
```bash
# CPU e RAM
docker stats

# Espaço em disco
df -h

# Logs do sistema
sudo journalctl -u docker -f
```

### 9.2. Verificar Logs da Aplicação
```bash
# Backend
docker-compose -f docker-compose.production.yml logs -f backend --tail=100

# Nginx
docker-compose -f docker-compose.production.yml logs -f nginx --tail=100

# Celery Worker
docker-compose -f docker-compose.production.yml logs -f celery-worker --tail=100
```

### 9.3. Verificar Health Checks
```bash
# Backend
curl https://playwave.com.br/health

# Postgres
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U playwave

# Redis
docker-compose -f docker-compose.production.yml exec redis redis-cli -a R4hM7pQ2tW8xY5zK9vL3nD6fG1hB8cE ping
```

---

## 🔧 COMANDOS ÚTEIS

### Reiniciar Serviços
```bash
# Reiniciar tudo
docker-compose -f docker-compose.production.yml restart

# Reiniciar serviço específico
docker-compose -f docker-compose.production.yml restart backend
docker-compose -f docker-compose.production.yml restart nginx
```

### Parar Serviços
```bash
docker-compose -f docker-compose.production.yml stop
```

### Iniciar Serviços
```bash
docker-compose -f docker-compose.production.yml start
```

### Atualizar Aplicação
```bash
# 1. Fazer pull do código
git pull origin main

# 2. Rebuild
docker-compose -f docker-compose.production.yml build --no-cache

# 3. Reiniciar
docker-compose -f docker-compose.production.yml up -d

# 4. Executar migrations
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### Ver Logs
```bash
# Todos os logs
docker-compose -f docker-compose.production.yml logs -f

# Logs de um serviço
docker-compose -f docker-compose.production.yml logs -f backend

# Últimas 100 linhas
docker-compose -f docker-compose.production.yml logs --tail=100 backend
```

### Executar Comandos no Container
```bash
# Shell no backend
docker-compose -f docker-compose.production.yml exec backend bash

# Shell no postgres
docker-compose -f docker-compose.production.yml exec postgres psql -U playwave

# Python no backend
docker-compose -f docker-compose.production.yml exec backend python
```

### Limpar Sistema
```bash
# Remover containers parados
docker container prune -f

# Remover imagens não usadas
docker image prune -a -f

# Remover volumes não usados
docker volume prune -f

# Limpar tudo
docker system prune -a -f --volumes
```

---

## 🐛 TROUBLESHOOTING

### Problema: Containers não sobem
```bash
# Verificar logs
docker-compose -f docker-compose.production.yml logs

# Verificar portas
sudo netstat -tulpn | grep -E ':(80|443|5432|6379|5672)'

# Verificar espaço em disco
df -h
```

### Problema: SSL não funciona
```bash
# Verificar certificado
sudo ls -la nginx/certbot/conf/live/playwave.com.br/

# Testar renovação manual
docker-compose -f docker-compose.production.yml exec certbot certbot renew --dry-run

# Verificar logs do Nginx
docker-compose -f docker-compose.production.yml logs nginx
```

### Problema: Backend não conecta ao banco
```bash
# Verificar se postgres está rodando
docker-compose -f docker-compose.production.yml ps postgres

# Testar conexão
docker-compose -f docker-compose.production.yml exec backend python -c "
from core.database import engine
try:
    engine.connect()
    print('Conexão OK!')
except Exception as e:
    print(f'Erro: {e}')
"
```

### Problema: Frontend não carrega
```bash
# Verificar build
docker-compose -f docker-compose.production.yml logs frontend

# Verificar Nginx
docker-compose -f docker-compose.production.yml exec nginx nginx -t

# Rebuild frontend
docker-compose -f docker-compose.production.yml build --no-cache frontend
docker-compose -f docker-compose.production.yml up -d frontend
```

---

## 📈 OTIMIZAÇÕES

### 1. Configurar Swap (se RAM < 8GB)
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. Configurar Logrotate
```bash
sudo nano /etc/logrotate.d/playwave
```

```
/opt/playwave/nginx/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose -f /opt/playwave/docker-compose.production.yml exec nginx nginx -s reload
    endscript
}
```

### 3. Configurar Limites do Docker
```bash
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker
```

---

## 🎯 CHECKLIST FINAL

- [ ] Servidor VPS configurado
- [ ] Docker e Docker Compose instalados
- [ ] Firewall configurado (portas 80, 443, 22)
- [ ] DNS apontando para o servidor
- [ ] Projeto clonado em `/opt/playwave`
- [ ] Senhas de produção alteradas
- [ ] SSL configurado (Let's Encrypt)
- [ ] Containers rodando (todos healthy)
- [ ] Migrations executadas
- [ ] Usuário admin criado
- [ ] Frontend acessível via HTTPS
- [ ] Backend respondendo na API
- [ ] Backup automático configurado
- [ ] Monitoramento configurado

---

## 📞 SUPORTE

### Logs Importantes
- **Backend:** `/opt/playwave/backend/logs/`
- **Nginx:** `/opt/playwave/nginx/logs/`
- **Docker:** `docker-compose logs`

### Comandos de Diagnóstico
```bash
# Status geral
docker-compose -f docker-compose.production.yml ps

# Health checks
curl https://playwave.com.br/health
curl https://playwave.com.br/api/v1/health

# Recursos
docker stats
df -h
free -h
```

---

**Deploy preparado por:** Cascade AI  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
