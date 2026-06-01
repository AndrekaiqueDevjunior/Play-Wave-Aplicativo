# 🔄 GUIA DE ATUALIZAÇÃO - VPS PLAYWAVE

**Última atualização:** 01 de Junho de 2026  
**VPS:** 2.24.81.194  
**Domínio:** playwave.com.br

---

## 📋 PRÉ-REQUISITOS

- ✅ Acesso SSH à VPS (root@2.24.81.194)
- ✅ Senha da VPS
- ✅ Código atualizado no GitHub
- ✅ Docker e Docker Compose instalados na VPS

---

## 🚀 ATUALIZAÇÃO RÁPIDA (5 MINUTOS)

### Passo 1: Conectar na VPS
```bash
ssh root@2.24.81.194
```

### Passo 2: Navegar para o projeto
```bash
cd /opt/playwave
```

### Passo 3: Atualizar código
```bash
git pull origin main
```

### Passo 4: Rebuildar e reiniciar containers
```bash
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

### Passo 5: Executar migrations (se houver)
```bash
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### Passo 6: Verificar status
```bash
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs -f --tail=50
```

---

## 📝 ATUALIZAÇÃO DETALHADA

### 1️⃣ Verificar estado atual

```bash
# Conectar na VPS
ssh root@2.24.81.194

# Verificar containers rodando
docker ps

# Verificar commit atual
cd /opt/playwave
git log -1 --oneline
```

### 2️⃣ Fazer backup (opcional mas recomendado)

```bash
# Backup do banco de dados
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U playwave playwave > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup dos uploads
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/uploads/
```

### 3️⃣ Atualizar código

```bash
cd /opt/playwave

# Verificar mudanças locais
git status

# Se houver mudanças locais não commitadas, fazer stash
git stash

# Atualizar código
git pull origin main

# Verificar novo commit
git log -1 --oneline
```

### 4️⃣ Parar serviços

```bash
docker-compose -f docker-compose.production.yml down
```

### 5️⃣ Rebuildar imagens

```bash
# Build sem cache (garante versão mais recente)
docker-compose -f docker-compose.production.yml build --no-cache

# OU build com cache (mais rápido)
docker-compose -f docker-compose.production.yml build
```

### 6️⃣ Subir serviços

```bash
docker-compose -f docker-compose.production.yml up -d
```

### 7️⃣ Executar migrations

```bash
# Aguardar backend ficar pronto (10-15 segundos)
sleep 15

# Executar migrations
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### 8️⃣ Verificar deploy

```bash
# Ver status dos containers
docker-compose -f docker-compose.production.yml ps

# Ver logs em tempo real
docker-compose -f docker-compose.production.yml logs -f

# Ver logs de um serviço específico
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f frontend
docker-compose -f docker-compose.production.yml logs -f nginx

# Testar backend
curl http://localhost:8000/health

# Testar frontend
curl http://localhost/
```

---

## 🔧 COMANDOS ÚTEIS

### Verificar logs
```bash
# Todos os serviços
docker-compose -f docker-compose.production.yml logs -f

# Últimas 100 linhas
docker-compose -f docker-compose.production.yml logs --tail=100

# Apenas backend
docker-compose -f docker-compose.production.yml logs -f backend

# Apenas erros
docker-compose -f docker-compose.production.yml logs | grep -i error
```

### Reiniciar serviços
```bash
# Reiniciar tudo
docker-compose -f docker-compose.production.yml restart

# Reiniciar apenas backend
docker-compose -f docker-compose.production.yml restart backend

# Reiniciar apenas frontend
docker-compose -f docker-compose.production.yml restart frontend
```

### Verificar recursos
```bash
# Ver uso de recursos
docker stats

# Ver espaço em disco
df -h

# Ver uso de memória
free -h
```

### Limpar recursos
```bash
# Remover containers parados
docker container prune -f

# Remover imagens não usadas
docker image prune -a -f

# Remover volumes não usados (CUIDADO!)
docker volume prune -f

# Limpar tudo (CUIDADO!)
docker system prune -a -f
```

---

## 🆘 TROUBLESHOOTING

### Problema: Container não sobe

```bash
# Ver logs detalhados
docker-compose -f docker-compose.production.yml logs backend

# Verificar se porta está em uso
netstat -tulpn | grep 8000

# Reiniciar container específico
docker-compose -f docker-compose.production.yml restart backend
```

### Problema: Migrations falham

```bash
# Verificar conexão com banco
docker-compose -f docker-compose.production.yml exec postgres psql -U playwave -d playwave -c "SELECT version();"

# Ver histórico de migrations
docker-compose -f docker-compose.production.yml exec backend alembic history

# Ver migrations pendentes
docker-compose -f docker-compose.production.yml exec backend alembic current
```

### Problema: Frontend não carrega

```bash
# Verificar logs do nginx
docker-compose -f docker-compose.production.yml logs nginx

# Verificar se frontend buildou corretamente
docker-compose -f docker-compose.production.yml exec frontend ls -la /usr/share/nginx/html/

# Rebuildar apenas frontend
docker-compose -f docker-compose.production.yml build --no-cache frontend
docker-compose -f docker-compose.production.yml up -d frontend
```

### Problema: SSL não funciona

```bash
# Verificar certificados
ls -la /opt/playwave/nginx/certbot/conf/live/playwave.com.br/

# Renovar certificados
docker-compose -f docker-compose.production.yml exec certbot certbot renew

# Reiniciar nginx
docker-compose -f docker-compose.production.yml restart nginx
```

---

## 🔄 ROLLBACK (SE NECESSÁRIO)

### Voltar para commit anterior

```bash
cd /opt/playwave

# Ver histórico
git log --oneline -10

# Voltar para commit específico
git checkout <commit-hash>

# Rebuildar
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

### Restaurar backup do banco

```bash
# Parar containers
docker-compose -f docker-compose.production.yml down

# Subir apenas postgres
docker-compose -f docker-compose.production.yml up -d postgres

# Aguardar postgres ficar pronto
sleep 10

# Restaurar backup
cat backup_YYYYMMDD_HHMMSS.sql | docker-compose -f docker-compose.production.yml exec -T postgres psql -U playwave playwave

# Subir todos os serviços
docker-compose -f docker-compose.production.yml up -d
```

---

## 📊 CHECKLIST DE ATUALIZAÇÃO

- [ ] Conectar na VPS via SSH
- [ ] Fazer backup do banco (opcional)
- [ ] Fazer backup dos uploads (opcional)
- [ ] Verificar commit atual
- [ ] Fazer `git pull origin main`
- [ ] Parar containers (`down`)
- [ ] Rebuildar imagens (`build --no-cache`)
- [ ] Subir containers (`up -d`)
- [ ] Executar migrations (`alembic upgrade head`)
- [ ] Verificar logs (`logs -f`)
- [ ] Testar backend (`curl /health`)
- [ ] Testar frontend (abrir no navegador)
- [ ] Verificar domínio HTTPS
- [ ] Monitorar por 5-10 minutos

---

## 🎯 ATUALIZAÇÃO EM UM COMANDO

Para atualização rápida sem downtime significativo:

```bash
ssh root@2.24.81.194 'cd /opt/playwave && \
  git pull origin main && \
  docker-compose -f docker-compose.production.yml build --no-cache && \
  docker-compose -f docker-compose.production.yml up -d && \
  sleep 15 && \
  docker-compose -f docker-compose.production.yml exec -T backend alembic upgrade head && \
  docker-compose -f docker-compose.production.yml ps'
```

---

## 📞 INFORMAÇÕES IMPORTANTES

### Credenciais VPS
- **IP:** 2.24.81.194
- **Usuário:** root
- **Porta SSH:** 22

### Domínio
- **Principal:** playwave.com.br
- **WWW:** www.playwave.com.br

### Portas
- **HTTP:** 80
- **HTTPS:** 443
- **Backend (interno):** 8000
- **Frontend (interno):** 3000
- **PostgreSQL (interno):** 5432
- **Redis (interno):** 6379
- **RabbitMQ (interno):** 5672

### Diretórios importantes
- **Projeto:** `/opt/playwave`
- **Uploads:** `/opt/playwave/backend/uploads`
- **Logs:** `/opt/playwave/backend/logs`
- **SSL:** `/opt/playwave/nginx/certbot/conf`
- **Backups:** `/opt/playwave/backups`

---

## ✅ VALIDAÇÃO PÓS-ATUALIZAÇÃO

### 1. Verificar serviços
```bash
docker-compose -f docker-compose.production.yml ps
```

Todos devem estar **Up** e **healthy**.

### 2. Testar endpoints
```bash
# Health check
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs

# Frontend
curl http://localhost/
```

### 3. Testar no navegador
- ✅ https://playwave.com.br (deve carregar)
- ✅ https://playwave.com.br/admin (deve redirecionar para login)
- ✅ https://playwave.com.br/api/v1/docs (deve mostrar Swagger)

### 4. Verificar logs
```bash
# Não deve ter erros críticos
docker-compose -f docker-compose.production.yml logs --tail=100 | grep -i error
```

---

## 📚 DOCUMENTAÇÃO RELACIONADA

- **Deploy completo:** `DEPLOY_VPS.md`
- **Deploy rápido:** `DEPLOY_RAPIDO.md`
- **Transferência:** `TRANSFERIR_PARA_VPS.md`
- **Índice:** `README_DEPLOY.md`

---

**Criado por:** Cascade AI  
**Data:** 01 de Junho de 2026  
**Versão:** 1.0
