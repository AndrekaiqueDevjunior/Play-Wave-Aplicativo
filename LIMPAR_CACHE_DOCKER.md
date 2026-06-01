# 🧹 LIMPAR CACHE DO DOCKER - FRONTEND BUGADO

**Problema:** Frontend com cache/imagem antiga, não atualizou as correções.

---

## 🚨 SOLUÇÃO RÁPIDA - COPIAR E COLAR NA VPS

### 1. Conectar na VPS
```bash
ssh root@2.24.81.194
# Senha: Pl@ywave2026
```

### 2. Ir para o projeto
```bash
cd /root/playwave
# OU
cd /root/Play-Wave-Aplicativo
# OU procurar:
find /root -name "docker-compose.production.yml" -type f 2>/dev/null
```

### 3. PARAR TUDO
```bash
docker-compose -f docker-compose.production.yml down
```

### 4. REMOVER IMAGENS ANTIGAS (IMPORTANTE!)
```bash
# Remover imagem do frontend
docker rmi playwave-frontend:latest 2>/dev/null || true
docker rmi $(docker images | grep playwave-frontend | awk '{print $3}') 2>/dev/null || true

# Remover imagem do backend também
docker rmi playwave-backend:latest 2>/dev/null || true
docker rmi $(docker images | grep playwave-backend | awk '{print $3}') 2>/dev/null || true
```

### 5. LIMPAR CACHE DO DOCKER
```bash
# Limpar build cache
docker builder prune -af

# Limpar volumes não usados
docker volume prune -f

# Limpar tudo que não está em uso
docker system prune -af
```

### 6. REBUILD TOTAL (SEM CACHE!)
```bash
docker-compose -f docker-compose.production.yml build --no-cache --pull
```

**Aguarde ~3-5 minutos** ⏳

### 7. SUBIR CONTAINERS
```bash
docker-compose -f docker-compose.production.yml up -d
```

### 8. VERIFICAR LOGS DO FRONTEND
```bash
docker-compose -f docker-compose.production.yml logs -f frontend
```

**Pressione Ctrl+C para sair dos logs**

### 9. VERIFICAR SE SUBIU
```bash
docker-compose -f docker-compose.production.yml ps
```

**Deve mostrar:**
```
NAME                STATUS
playwave-frontend   Up X seconds
playwave-backend    Up X seconds
playwave-db         Up X seconds
playwave-redis      Up X seconds
```

### 10. TESTAR
```bash
curl -I http://localhost:80
```

---

## 🔍 VERIFICAR SE ATUALIZOU

### Dentro do container do frontend
```bash
docker-compose -f docker-compose.production.yml exec frontend ls -la /usr/share/nginx/html/assets/
```

**Deve mostrar arquivos recentes (data de hoje)**

### Ver código do ErrorBoundary
```bash
docker-compose -f docker-compose.production.yml exec frontend cat /usr/share/nginx/html/index.html | grep -i error
```

---

## 🌐 TESTAR NO NAVEGADOR

1. Abrir: **http://playwave.com.br**
2. **LIMPAR CACHE DO NAVEGADOR:**
   - Chrome/Edge: `Ctrl + Shift + Delete` → Limpar cache
   - Firefox: `Ctrl + Shift + Delete` → Limpar cache
   - Ou abrir em **aba anônima** (Ctrl + Shift + N)

3. **F12** (DevTools) → **Aba Network** → Marcar **"Disable cache"**
4. **F5** (Recarregar)
5. Login
6. Dispositivos → Ver detalhes
7. **Console** deve mostrar:
   ```
   [DispositivoDetalhe] Componente montado
   [DispositivoDetalhe] Device ID: xxx
   ```

---

## 🐛 SE AINDA NÃO FUNCIONAR

### Verificar se código foi atualizado
```bash
cd /root/playwave  # ou caminho correto
git log --oneline -5
```

**Deve mostrar:**
```
ed4deed docs: adicionar script e instruções de atualização VPS
bbb3e86 feat: criar agentes automatizados para testar bugs P0
03a5a9f fix: adicionar ErrorBoundary e logging para debug
```

### Se NÃO mostrar, fazer pull:
```bash
git fetch origin
git reset --hard origin/main
```

### Rebuild novamente:
```bash
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache --pull
docker-compose -f docker-compose.production.yml up -d
```

---

## 🔥 LIMPEZA EXTREMA (SE NADA FUNCIONAR)

```bash
# PARAR TUDO
docker-compose -f docker-compose.production.yml down -v

# REMOVER TODAS AS IMAGENS DO PLAYWAVE
docker images | grep playwave | awk '{print $3}' | xargs docker rmi -f

# LIMPAR TODO O CACHE
docker system prune -af --volumes

# REBUILD DO ZERO
docker-compose -f docker-compose.production.yml build --no-cache --pull

# SUBIR
docker-compose -f docker-compose.production.yml up -d
```

---

## 📊 VERIFICAR VERSÃO DO CÓDIGO NO CONTAINER

### Frontend
```bash
docker-compose -f docker-compose.production.yml exec frontend cat /usr/share/nginx/html/index.html | head -20
```

**Procure por:** `ErrorBoundary` ou data de build recente

### Backend
```bash
docker-compose -f docker-compose.production.yml exec backend cat /app/main.py | head -10
```

---

## ✅ CHECKLIST FINAL

- [ ] Git pull feito (commit ed4deed)
- [ ] Imagens antigas removidas
- [ ] Cache do Docker limpo
- [ ] Rebuild sem cache (--no-cache)
- [ ] Containers UP (4/4)
- [ ] Cache do navegador limpo
- [ ] F12 → Network → Disable cache marcado
- [ ] Console mostra logs do DispositivoDetalhe

---

## 🆘 AINDA COM PROBLEMA?

### Envie essas informações:

```bash
# 1. Versão do código
git log --oneline -3

# 2. Status dos containers
docker-compose -f docker-compose.production.yml ps

# 3. Logs do frontend
docker-compose -f docker-compose.production.yml logs --tail=50 frontend

# 4. Listar arquivos do frontend
docker-compose -f docker-compose.production.yml exec frontend ls -lah /usr/share/nginx/html/

# 5. Ver se ErrorBoundary está no código
docker-compose -f docker-compose.production.yml exec frontend find /usr/share/nginx/html -name "*.js" -exec grep -l "ErrorBoundary" {} \;
```

Copie e cole a saída desses comandos!
