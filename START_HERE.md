# 🚀 COMECE AQUI — PlayWave Setup Correto

**Leia isso ANTES de tentar rodar qualquer coisa.**

---

## 🎯 DUAS APLICAÇÕES DIFERENTES

### 1️⃣ DASHBOARD ADMIN (para gerenciar)
```
Acesso: http://localhost:5173 (dev) ou localhost:5173
Usuário: admin@playwave.com / &2p0Kw45A&lLNX4bM%gpH*cy
Função: Gerenciar dispositivos, campanhas, mídia
Dados: Mock data de 6 devices, campanhas, etc
```

### 2️⃣ PLAYER (para exibir/testar)
```
Acesso: http://localhost:3000/player (via Electron)
Usuário: Device token (pareamento automático)
Função: Exibir playlists, responder comandos
Dados: Recebe do backend
```

---

## ✅ SETUP RÁPIDO (5 MINUTOS)

### Passo 1: Backend (já está rodando)
```bash
docker-compose ps
# Verificar se 5 containers estão UP
```

### Passo 2: Dashboard Admin (para gerenciar)
```bash
cd frontend
npm run dev
# Abre em http://localhost:5173
# Faz login com admin@playwave.com
# VÊ mock data com 6 devices, campanhas, etc
```

### Passo 3: Player (opcional, para testar TV)
```bash
# Terminal 3 (servidor player)
cd frontend
npm run preview -- --port 3000

# Terminal 4 (Electron app)
cd frontend/electron
npm run dev
# Abre janela fullscreen
# Mostra tela de pareamento
```

---

## 📊 COMPARAÇÃO

| Feature | Dashboard (localhost:5173) | Player (localhost:3000/player) |
|---------|---------------------------|-------------------------------|
| **Login** | Email + Senha | Device pairing code |
| **Visualização** | Dashboard admin | TV fullscreen |
| **Gerenciar Devices** | ✅ CRUD completo | ❌ Não |
| **Criar Campanhas** | ✅ Sim | ❌ Não |
| **Upload Mídia** | ✅ Sim | ❌ Não |
| **Ver Analytics** | ✅ Sim | ❌ Não |
| **Exibir Conteúdo** | ❌ Não | ✅ Sim |
| **Responder Comandos** | ❌ Não | ✅ Sim |
| **Mock Data** | ✅ 6 devices | ✅ Recebe do backend |

---

## 🎬 PRIMEIRO TESTE (10 MINUTOS)

### Objetivo: Ver o Dashboard com Mock Data

```bash
# Terminal 1: Backend
docker-compose ps
# Verificar containers rodando

# Terminal 2: Frontend Dev
cd "C:\Users\Kaik\Documents\VScode\PlayWave\Play-Wave-Aplicativo\frontend"
npm run dev
# Aguarda "Local: http://localhost:5173"

# Browser: abrir http://localhost:5173
# Login:
#   Email: admin@playwave.com
#   Senha: &2p0Kw45A&lLNX4bM%gpH*cy

# RESULTADO ESPERADO:
# ✅ Dashboard carrega
# ✅ 6 dispositivos listados (1 offline, 1 error, 4 online)
# ✅ 6 campanhas visíveis
# ✅ Gráfico de views por dia
# ✅ 3 alertas com severidade
# ✅ Sem erros na console (F12)
```

---

## 📺 SEGUNDO TESTE (Opcional: Electron Player)

### Objetivo: Testar o Player de TV

```bash
# Você já tem Terminal 2 rodando (npm run dev)

# Terminal 3: Preview Server (porta 3000)
cd "C:\Users\Kaik\Documents\VScode\PlayWave\Play-Wave-Aplicativo\frontend"
npm run preview -- --port 3000
# Aguarda "➜ Local: http://localhost:3000"

# Terminal 4: Electron App
cd "C:\Users\Kaik\Documents\VScode\PlayWave\Play-Wave-Aplicativo\frontend\electron"
npm run dev
# Abre janela Electron em fullscreen

# RESULTADO ESPERADO:
# ✅ Janela fullscreen preta
# ✅ Mostra código de pareamento TV-XXXX
# ✅ Sem erros na console (Ctrl+Shift+I)
# ✅ Status: Aguardando pareamento
```

---

## 🐛 SOLUÇÃO RÁPIDA SE ALGO FALHAR

### "Backend não conectado" ou "API unreachable"
```bash
# Verificar Docker
docker-compose ps

# Se não tiver 5 containers UP:
docker-compose down
docker-compose up -d

# Verificar health
curl http://localhost:8000/health
```

### "Porta 5173 já em uso"
```bash
# Matar processo
Get-Process | Where-Object {$_.Port -eq 5173}
# Copiar PID e:
Stop-Process -Id <PID> -Force
```

### "Porta 3000 já em uso"
```bash
# Usar porta diferente
npm run preview -- --port 3001
```

### "Electron não abre"
```bash
# Instalar dependências
cd frontend/electron
npm install

# Verificar cross-env instalado
npm list cross-env

# Se não tiver:
npm install cross-env --save-dev
```

---

## ✨ PRÓXIMAS TAREFAS

### Semana 1: Explorar Mock Data
- [ ] Login no dashboard
- [ ] Ver todos os 6 dispositivos
- [ ] Clicar em cada dispositivo (ver detalhes)
- [ ] Ver campanhas (6 total: 4 ativas, 1 rascunho, 1 encerrada)
- [ ] Ver mídia (7 arquivos)
- [ ] Ver alertas (3 com severidade)
- [ ] Testar dark mode (se houver)

### Semana 2: Implementar Features Real
- [ ] Conectar API real de dispositivos (remover mock)
- [ ] Conectar API real de campanhas
- [ ] Conectar API real de mídia
- [ ] Implementar upload real
- [ ] Testar CRUD completo

### Semana 3: Player e Electron
- [ ] Implementar pairing real
- [ ] Testar playback de vídeo
- [ ] Testar comandos remoto
- [ ] Build .exe para Windows
- [ ] Testar instalador

---

## 📞 REFERÊNCIAS RÁPIDAS

| Problema | Arquivo |
|----------|---------|
| Como rodar tudo | Este arquivo (START_HERE.md) |
| Explicação Electron vs Web | ELECTRON_PLAYER_ONLY.md |
| Setup completo | QUICK_START.md |
| Troubleshooting | ELECTRON_SETUP.md |
| Dados mock | MOCK_DATA_FEATURES.md |
| Arquitetura | ARCHITECTURE.md |

---

## 🎓 ESTRUTURA DO PROJETO

```
PlayWave/
├── backend/
│   ├── .env                    ← Configuração (URL_HOST, ENVIRONMENT)
│   ├── main.py                 ← FastAPI app
│   ├── core/
│   │   ├── models.py           ← SQLAlchemy ORM
│   │   ├── auth.py             ← JWT, password hash
│   │   └── database.py         ← Connection pool
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py         ← /api/auth/login
│   │   │   ├── dispositivos.py ← /api/devices
│   │   │   ├── campanhas.py    ← /api/campaigns
│   │   │   └── midias.py       ← /api/media
│   └── docker-compose.yml      ← PostgreSQL, Redis, RabbitMQ, etc
│
├── frontend/
│   ├── .env.local              ← VITE_API_URL, VITE_PLAYER_URL
│   ├── src/
│   │   ├── app.jsx             ← Routing (login, /player, /dashboard, etc)
│   │   ├── pages/
│   │   │   ├── Login.jsx       ← Login form
│   │   │   ├── Dashboard.jsx   ← Admin dashboard
│   │   │   ├── Dispositivos.jsx← Gerenciar devices
│   │   │   ├── Campanhas.jsx   ← Gerenciar campanhas
│   │   │   ├── BibliotecaMidias.jsx ← Gerenciar mídia
│   │   │   └── Player.jsx      ← TV Player (/player)
│   │   ├── lib/
│   │   │   ├── AuthContext.jsx ← JWT auth
│   │   │   └── mockData.js     ← 6 devices, campanhas, etc
│   │   └── api/
│   │       ├── http.js         ← HTTP client
│   │       ├── dispositivos.js ← GET /api/devices
│   │       ├── campanhas.js    ← CRUD /api/campaigns
│   │       └── midias.js       ← POST /api/media/upload
│   └── electron/
│       ├── package.json        ← "dev" script
│       ├── main.js             ← Carrega /player
│       └── preload.js          ← IPC bridge
│
└── docs/
    ├── START_HERE.md           ← Este arquivo
    ├── QUICK_START.md          ← 3 passos rápidos
    ├── ELECTRON_PLAYER_ONLY.md ← Explicação Electron
    └── FINAL_CHECKLIST.md      ← Checklist completo
```

---

## 🚀 COMANDOS RÁPIDOS

```bash
# Backend
docker-compose up -d        # Iniciar
docker-compose ps           # Status
docker-compose logs backend # Ver logs

# Frontend Dashboard
npm run dev                 # Dev server :5173
npm run build              # Build para prod
npm run preview            # Preview do build

# Frontend Electron
npm run preview -- --port 3000  # Servidor em :3000
cd electron && npm run dev      # Electron app
cd electron && npm run build:win # Build .exe
```

---

## ✅ CHECKLIST FINAL

- [ ] Docker `docker-compose ps` (5 containers UP)
- [ ] Backend health `curl http://localhost:8000/health` (200 OK)
- [ ] Login test (admin@playwave.com consegue fazer login)
- [ ] CORS test (`curl -H "Origin: http://localhost:3000"`)
- [ ] Frontend dev rodando em :5173
- [ ] Ver 6 dispositivos na página de Dispositivos
- [ ] Ver mock data (campanhas, mídia, alertas)

---

**Pronto?** Execute os passos acima e volte com dúvidas.

**Data**: 2026-06-04  
**Status**: ✅ Pronto para começar  
**Próximo**: `npm run dev` na pasta frontend

