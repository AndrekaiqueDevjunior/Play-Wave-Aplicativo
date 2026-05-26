# ⚡ DEPLOY RÁPIDO - PLAYWAVE VPS
**Servidor:** 2.24.81.194  
**Domínio:** playwave.com.br

---

## 🚀 DEPLOY EM 5 MINUTOS

### 1️⃣ Conectar ao Servidor
```bash
ssh root@2.24.81.194
```

### 2️⃣ Instalar Dependências (primeira vez)
```bash
# Docker
curl -fsSL https://get.docker.com | sh

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Firewall
sudo apt install ufw -y
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3️⃣ Clonar Projeto
```bash
cd /opt
git clone <seu-repositorio> playwave
cd playwave
```

### 4️⃣ Configurar Senhas
```bash
nano docker-compose.production.yml
```

**Trocar:**
- Linha 28: `POSTGRES_PASSWORD`
- Linha 51: `REDIS_PASSWORD` (comando redis-server)
- Linha 75: `RABBITMQ_DEFAULT_PASS`
- Linha 134: `SECRET_KEY`
- Linha 152: `ADMIN_INITIAL_PASSWORD`

### 5️⃣ Deploy Automático
```bash
sudo ./deploy-quick.sh
```

**O script faz:**
- ✅ Build das imagens
- ✅ Sobe containers
- ✅ Executa migrations
- ✅ Verifica saúde

### 6️⃣ Configurar SSL (Let's Encrypt)
```bash
./deploy/init-ssl.sh
```

---

## 📋 COMANDOS ESSENCIAIS

### Ver Status
```bash
docker-compose -f docker-compose.production.yml ps
```

### Ver Logs
```bash
# Todos
docker-compose -f docker-compose.production.yml logs -f

# Backend
docker-compose -f docker-compose.production.yml logs -f backend

# Nginx
docker-compose -f docker-compose.production.yml logs -f nginx
```

### Reiniciar
```bash
# Tudo
docker-compose -f docker-compose.production.yml restart

# Serviço específico
docker-compose -f docker-compose.production.yml restart backend
```

### Atualizar Código
```bash
git pull
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### Backup Manual
```bash
# Banco
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U playwave playwave > backup_$(date +%Y%m%d).sql

# Uploads
tar -czf uploads_$(date +%Y%m%d).tar.gz backend/uploads
```

---

## ✅ VERIFICAR DEPLOY

### Testar Backend
```bash
curl https://playwave.com.br/health
# Esperado: {"status":"ok"}
```

### Testar API
```bash
curl https://playwave.com.br/api/v1/health
# Esperado: {"status":"healthy","version":"1.0.0"}
```

### Abrir no Navegador
```
https://playwave.com.br
```

**Login padrão:**
- Email: `admin@playwave.com`
- Senha: (a que você configurou)

---

## 🐛 PROBLEMAS COMUNS

### Containers não sobem
```bash
# Ver logs
docker-compose -f docker-compose.production.yml logs

# Verificar portas
sudo netstat -tulpn | grep -E ':(80|443)'

# Verificar espaço
df -h
```

### SSL não funciona
```bash
# Verificar DNS
nslookup playwave.com.br

# Deve retornar: 2.24.81.194

# Verificar certificado
ls -la nginx/certbot/conf/live/playwave.com.br/
```

### Backend não conecta
```bash
# Verificar postgres
docker-compose -f docker-compose.production.yml ps postgres

# Testar conexão
docker-compose -f docker-compose.production.yml exec backend python -c "from core.database import engine; engine.connect(); print('OK')"
```

---

## 📊 MONITORAMENTO

### Recursos
```bash
# CPU e RAM
docker stats

# Espaço
df -h

# Memória
free -h
```

### Health Checks
```bash
# Backend
curl https://playwave.com.br/health

# Postgres
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U playwave

# Redis
docker-compose -f docker-compose.production.yml exec redis redis-cli -a <senha> ping
```

---

## 🔄 MANUTENÇÃO

### Backup Automático
```bash
# Editar crontab
sudo crontab -e

# Adicionar linha (backup diário às 3h)
0 3 * * * /opt/playwave/backup.sh >> /var/log/playwave-backup.log 2>&1
```

### Limpar Docker
```bash
# Remover containers parados
docker container prune -f

# Remover imagens não usadas
docker image prune -a -f

# Limpar tudo
docker system prune -a -f --volumes
```

### Renovar SSL (automático)
O container `certbot` renova automaticamente a cada 12h.

Para forçar renovação:
```bash
docker-compose -f docker-compose.production.yml exec certbot certbot renew --force-renewal
docker-compose -f docker-compose.production.yml exec nginx nginx -s reload
```

---

## 📞 SUPORTE RÁPIDO

### Logs Importantes
```bash
# Backend
docker-compose -f docker-compose.production.yml logs backend --tail=100

# Nginx
docker-compose -f docker-compose.production.yml logs nginx --tail=100

# Postgres
docker-compose -f docker-compose.production.yml logs postgres --tail=100
```

### Entrar no Container
```bash
# Backend
docker-compose -f docker-compose.production.yml exec backend bash

# Postgres
docker-compose -f docker-compose.production.yml exec postgres psql -U playwave
```

### Executar Migrations
```bash
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### Criar Usuário Admin
```bash
docker-compose -f docker-compose.production.yml exec backend python -c "
from core.database import SessionLocal
from core.models import User
from core.security import get_password_hash

db = SessionLocal()
admin = User(
    email='admin@playwave.com',
    password=get_password_hash('SuaSenhaForte123!'),
    role='admin',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin criado!')
"
```

---

## 🎯 CHECKLIST

- [ ] Servidor VPS com Ubuntu/Debian
- [ ] Docker e Docker Compose instalados
- [ ] Firewall configurado (80, 443, 22)
- [ ] DNS apontando para 2.24.81.194
- [ ] Senhas de produção alteradas
- [ ] Deploy executado com sucesso
- [ ] SSL configurado
- [ ] Backend respondendo
- [ ] Frontend acessível
- [ ] Login funcionando

---

**Documentação completa:** `DEPLOY_VPS.md`  
**Script automático:** `./deploy-quick.sh`  
**Configurar SSL:** `./deploy/init-ssl.sh`
