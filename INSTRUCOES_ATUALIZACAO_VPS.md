# 🚀 INSTRUÇÕES DE ATUALIZAÇÃO VPS

**Data:** 01/06/2026  
**VPS:** 2.24.81.194  
**Domínio:** playwave.com.br

---

## 📋 O QUE VAI SER ATUALIZADO

### ✅ Correções Aplicadas

1. **ErrorBoundary** - Captura erros de renderização (tela branca)
2. **Logging detalhado** - Debug do DispositivoDetalhe
3. **Agentes de teste** - Validação automatizada de bugs

### 📦 Commits a Subir

```bash
bbb3e86 - feat: criar agentes automatizados para testar bugs P0 (#1, #4, #5)
4111829 - docs: adicionar BUG 8 no documento de bugs críticos  
03a5a9f - fix: adicionar ErrorBoundary e logging para debug de tela branca
```

---

## 🚀 MÉTODO 1: SCRIPT AUTOMÁTICO (RECOMENDADO)

### Executar

```bash
./atualizar_vps.sh
```

**Senha quando solicitado:** `Pl@ywave2026`

O script vai:
1. ✅ Conectar na VPS
2. ✅ Localizar o projeto
3. ✅ Fazer git pull
4. ✅ Rebuild dos containers
5. ✅ Executar migrations
6. ✅ Reiniciar serviços
7. ✅ Verificar logs
8. ✅ Testar endpoints

**Duração:** ~3-5 minutos

---

## 🔧 MÉTODO 2: MANUAL (PASSO A PASSO)

### 1. Conectar na VPS

```bash
ssh root@2.24.81.194
# Senha: Pl@ywave2026
```

### 2. Localizar Projeto

```bash
# Opção A: Se souber o caminho
cd /root/playwave  # ou /root/Play-Wave-Aplicativo

# Opção B: Procurar
find /root -name "docker-compose.production.yml" -type f
```

### 3. Atualizar Código

```bash
git pull origin main
```

**Saída esperada:**
```
Updating 7dd93f8..bbb3e86
Fast-forward
 frontend/src/app.jsx                          |   4 +-
 frontend/src/components/shared/ErrorBoundary.jsx | 93 ++++++++++
 frontend/src/pages/DispositivoDetalhe.jsx    |   8 +
 tests/test_agents/...                         | 2481 +++++++++++++++++++
 4 files changed, 2584 insertions(+), 2 deletions(-)
```

### 4. Rebuild Containers

```bash
docker-compose -f docker-compose.production.yml build --no-cache
```

### 5. Reiniciar

```bash
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

### 6. Executar Migrations

```bash
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### 7. Verificar Status

```bash
docker-compose -f docker-compose.production.yml ps
```

**Esperado:**
```
NAME                STATUS              PORTS
playwave-backend    Up 30 seconds       0.0.0.0:8000->8000/tcp
playwave-frontend   Up 30 seconds       0.0.0.0:80->80/tcp
playwave-db         Up 30 seconds       5432/tcp
playwave-redis      Up 30 seconds       6379/tcp
```

### 8. Verificar Logs

```bash
# Backend
docker-compose -f docker-compose.production.yml logs --tail=50 backend

# Frontend
docker-compose -f docker-compose.production.yml logs --tail=50 frontend
```

---

## 🧪 TESTAR CORREÇÕES

### 1. Testar ErrorBoundary (Bug #8)

1. Abrir: http://playwave.com.br
2. Login com credenciais
3. Ir em **Dispositivos**
4. Clicar em **"Ver detalhes"** de qualquer dispositivo
5. **Abrir DevTools (F12)** → Aba Console

**Resultado esperado:**
```
[DispositivoDetalhe] Componente montado
[DispositivoDetalhe] Device ID: abc123
[DispositivoDetalhe] Device data: {...}
[DispositivoDetalhe] Loading: false
[DispositivoDetalhe] Error: null
```

**Se ainda der erro:**
- ErrorBoundary vai capturar e mostrar mensagem
- Copiar erro do console
- Reportar com screenshot

### 2. Verificar Outros Bugs

Após atualização, testar:

- [ ] **Bug #1:** Criar campanha → adicionar mídia → ver no player
- [ ] **Bug #4:** Criar playlist → adicionar spot → verificar alternância
- [ ] **Bug #5:** Criar pasta → agendar → verificar se toca
- [ ] **Bug #6:** Enviar comando → verificar se player executa

---

## 🐛 TROUBLESHOOTING

### Container não sobe

```bash
# Ver logs de erro
docker-compose -f docker-compose.production.yml logs backend
docker-compose -f docker-compose.production.yml logs frontend

# Restart forçado
docker-compose -f docker-compose.production.yml restart
```

### Migration falha

```bash
# Entrar no container
docker-compose -f docker-compose.production.yml exec backend bash

# Ver migrations pendentes
alembic current
alembic history

# Forçar upgrade
alembic upgrade head
```

### Frontend não carrega

```bash
# Verificar nginx
docker-compose -f docker-compose.production.yml exec frontend nginx -t

# Rebuild só do frontend
docker-compose -f docker-compose.production.yml build frontend
docker-compose -f docker-compose.production.yml up -d frontend
```

### Porta já em uso

```bash
# Ver o que está usando a porta
netstat -tulpn | grep :80
netstat -tulpn | grep :8000

# Matar processo
kill -9 <PID>

# Ou mudar porta no docker-compose.production.yml
```

### Git pull falha

```bash
# Ver status
git status

# Descartar mudanças locais
git reset --hard origin/main

# Forçar pull
git pull --force origin main
```

---

## 📊 VALIDAÇÃO PÓS-ATUALIZAÇÃO

### Checklist

- [ ] Containers rodando (4/4 up)
- [ ] Backend responde: `curl http://localhost:8000/api/v1/health`
- [ ] Frontend carrega: `curl -I http://localhost:80`
- [ ] Login funciona
- [ ] Dispositivos listam
- [ ] **Ver detalhes não dá tela branca** ✨
- [ ] Console mostra logs do DispositivoDetalhe

### Endpoints de Teste

```bash
# Health check
curl http://playwave.com.br/api/v1/health

# Versão da API
curl http://playwave.com.br/api/v1/version

# Frontend
curl -I http://playwave.com.br
```

---

## 🔄 ROLLBACK (SE NECESSÁRIO)

### Se algo der errado:

```bash
# 1. Voltar código
git reset --hard 7dd93f8  # Commit anterior

# 2. Rebuild
docker-compose -f docker-compose.production.yml build

# 3. Restart
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

---

## 📞 SUPORTE

### Logs Completos

```bash
# Salvar logs para análise
docker-compose -f docker-compose.production.yml logs > /tmp/playwave-logs.txt

# Enviar para análise
cat /tmp/playwave-logs.txt
```

### Informações do Sistema

```bash
# Versão Docker
docker --version
docker-compose --version

# Espaço em disco
df -h

# Memória
free -h

# Containers
docker ps -a
```

---

## ✅ SUCESSO!

Após atualização bem-sucedida:

1. ✅ Testar bug #8 (tela branca)
2. ✅ Verificar logs no console
3. ✅ Reportar se corrigiu ou se ainda tem erro
4. ✅ Testar outros bugs (1, 4, 5, 6)

---

**Criado em:** 01/06/2026  
**Última atualização:** 01/06/2026  
**Versão:** 1.0.0
