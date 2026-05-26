# 📤 TRANSFERIR PROJETO PARA VPS

## Opção 1: Via Git (Recomendado)

### 1. Criar Repositório no GitHub/GitLab
```bash
# No seu computador local
cd /home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo

# Inicializar git (se ainda não foi)
git init
git add .
git commit -m "Deploy inicial"

# Adicionar remote
git remote add origin https://github.com/seu-usuario/playwave.git
git push -u origin main
```

### 2. Clonar no Servidor
```bash
# No servidor VPS
ssh root@2.24.81.194

cd /opt
git clone https://github.com/seu-usuario/playwave.git
cd playwave
```

---

## Opção 2: Via SCP (Transferência Direta)

### 1. Compactar Projeto
```bash
# No seu computador local
cd /home/andre-kaique/projetos/play_wave_aplicativo

# Criar arquivo tar.gz (excluindo node_modules e __pycache__)
tar -czf playwave.tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.pytest_cache' \
  Play-Wave-Aplicativo/
```

### 2. Transferir para Servidor
```bash
# Transferir arquivo
scp playwave.tar.gz root@2.24.81.194:/opt/

# Conectar ao servidor
ssh root@2.24.81.194

# Descompactar
cd /opt
tar -xzf playwave.tar.gz
mv Play-Wave-Aplicativo playwave
cd playwave
```

---

## Opção 3: Via rsync (Sincronização)

### Transferir e Sincronizar
```bash
# No seu computador local
rsync -avz --progress \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.pytest_cache' \
  /home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/ \
  root@2.24.81.194:/opt/playwave/
```

---

## Opção 4: Via FTP/SFTP (FileZilla)

### 1. Abrir FileZilla
- Host: `sftp://2.24.81.194`
- Usuário: `root`
- Senha: (sua senha)
- Porta: `22`

### 2. Transferir Arquivos
- Local: `/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo`
- Remoto: `/opt/playwave`

**Excluir:**
- `node_modules/`
- `__pycache__/`
- `.git/`
- `dist/`
- `build/`

---

## ✅ Verificar Transferência

### No Servidor
```bash
ssh root@2.24.81.194

# Verificar estrutura
ls -la /opt/playwave/

# Deve mostrar:
# backend/
# frontend/
# nginx/
# docker-compose.production.yml
# deploy-quick.sh
# etc.
```

---

## 🔐 Configurar Permissões

```bash
# No servidor
cd /opt/playwave

# Dar permissão de execução aos scripts
chmod +x deploy-quick.sh
chmod +x deploy/init-ssl.sh

# Ajustar proprietário (opcional)
chown -R root:root .
```

---

## 🚀 Próximos Passos

Após transferir, siga o guia de deploy:

1. **Deploy Rápido:** `DEPLOY_RAPIDO.md`
2. **Deploy Completo:** `DEPLOY_VPS.md`
3. **Executar:** `sudo ./deploy-quick.sh`

---

## 📝 Exemplo Completo (Git)

```bash
# ===================================
# NO SEU COMPUTADOR LOCAL
# ===================================

cd /home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo

# Criar .gitignore se não existir
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log
yarn-error.log
.pnpm-debug.log
dist/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Uploads (não versionar arquivos de usuários)
backend/uploads/media/*
backend/uploads/audio/*
!backend/uploads/.gitkeep

# Docker
.dockerignore

# Env
.env
.env.local
.env.production

# Cache
.pytest_cache/
.cache/
EOF

# Commit
git add .
git commit -m "Preparar para deploy"

# Push para GitHub
git remote add origin https://github.com/seu-usuario/playwave.git
git push -u origin main

# ===================================
# NO SERVIDOR VPS
# ===================================

ssh root@2.24.81.194

# Clonar
cd /opt
git clone https://github.com/seu-usuario/playwave.git
cd playwave

# Configurar
nano docker-compose.production.yml
# (alterar senhas)

# Deploy
sudo ./deploy-quick.sh
```

---

## 🔄 Atualizar Código (após deploy inicial)

### Via Git
```bash
# No servidor
cd /opt/playwave
git pull origin main
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

### Via rsync
```bash
# No seu computador local
rsync -avz --progress \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  /home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/ \
  root@2.24.81.194:/opt/playwave/

# No servidor
ssh root@2.24.81.194
cd /opt/playwave
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

---

## ⚠️ IMPORTANTE

### Não Transferir
- ❌ `node_modules/` (será instalado no build)
- ❌ `__pycache__/` (cache Python)
- ❌ `.git/` (se usar SCP/rsync)
- ❌ `dist/` (será gerado no build)
- ❌ `build/` (será gerado no build)
- ❌ Arquivos de upload de usuários (se houver)

### Transferir
- ✅ Código fonte (`backend/`, `frontend/`)
- ✅ Configurações (`docker-compose.production.yml`, `nginx/`)
- ✅ Scripts (`deploy-quick.sh`, `deploy/`)
- ✅ Documentação (`.md`)
- ✅ Migrations (`backend/alembic/versions/`)

---

## 🎯 Checklist de Transferência

- [ ] Projeto compactado ou commitado no Git
- [ ] Transferido para `/opt/playwave` no servidor
- [ ] Permissões de execução configuradas
- [ ] Senhas de produção alteradas
- [ ] Estrutura verificada
- [ ] Pronto para executar `./deploy-quick.sh`

---

**Próximo passo:** Seguir `DEPLOY_RAPIDO.md` ou `DEPLOY_VPS.md`
