# Configuração do Electron + Backend

## Status Atual ✓

| Item | Dev | Produção |
|------|-----|----------|
| **Backend** | http://localhost:8000 | https://api.playwave.com.br |
| **Frontend Web** | http://localhost:5173 | https://playwave.com.br |
| **Frontend Electron** | http://localhost:3000 | Capacitor APK |
| **Admin Credentials** | admin@playwave.com | Configurado ✓ |

---

## Problemas Resolvidos

### ✓ Docker & Backend
- Backend iniciado em `http://localhost:8000`
- Credenciais do admin: `admin@playwave.com` / `&2p0Kw45A&lLNX4bM%gpH*cy`
- Smoke test: **LOGIN FUNCIONA** ✓

### ✓ Variáveis de Ambiente Configuradas

**Backend (.env)**
```bash
URL_HOST=http://localhost:8000
ENVIRONMENT=development
VITE_API_URL=http://localhost:8000
```

**Frontend (.env.local)**
```bash
VITE_API_URL=http://localhost:8000
VITE_PLAYER_URL=http://localhost:3000/player
```

---

## Como Testar Electron Localmente

### 1️⃣ Iniciar Backend (Docker)
```bash
docker-compose down --remove-orphans
docker-compose up -d
```

### 2️⃣ Iniciar Frontend Web
```bash
cd frontend
npm run dev
# Roda em http://localhost:5173
```

### 3️⃣ Iniciar Servidor Player (Electron)
```bash
cd frontend
npm run dev:electron
# Ou rodar manualmente em outra porta:
npm run preview -- --port 3000
```

### 4️⃣ Iniciar Electron App
```bash
cd frontend/electron
npm run electron:dev
# Carregará de VITE_PLAYER_URL=http://localhost:3000/player
```

---

## Problema: "Backend não conectado" no Electron

### Causas Possíveis

1. **VITE_API_URL não definida**
   - Arquivo: `frontend/src/lib/AuthContext.jsx` (linha 4)
   - Solução: Verificar `.env.local` tem `VITE_API_URL=http://localhost:8000`

2. **Backend fora (porta 8000 inacessível)**
   - Verificar: `curl http://localhost:8000/health`
   - Se falhar: `docker-compose up -d`

3. **CORS bloqueando requisição**
   - Backend: `ALLOWED_ORIGINS` no `.env`
   - Configurado para: `http://localhost:3000` ✓

4. **Electron carregando porta errada**
   - Se VITE_PLAYER_URL vazio: Electron tenta porta aleatória
   - Solução: Certificar que `frontend/.env.local` tem `VITE_PLAYER_URL=http://localhost:3000/player`

---

## Arquivos de Configuração

### Backend
- **`.env`** — Credenciais, URLs, variáveis de produção
- **`docker-compose.yml`** — Nginx redireciona `/api/*` para backend:8000

### Frontend
- **`.env.example`** — Template com documentação
- **`.env.local`** — Desenvolvimento local (NÃO commitar)
- **`.env.production`** — Produção/APK (HTTPS obrigatório)

### Electron
- **`frontend/electron/main.js`** — Lê `VITE_PLAYER_URL` via `process.env`
- **`frontend/electron/preload.js`** — Bridge entre Node e Renderer

---

## 🔧 Proxies & Redirecionamentos

### Nginx (docker-compose.yml)
```
/api/* → http://backend:8000/api/*
/health → http://backend:8000/health
/ → frontend:5173 ou arquivo local
```

### Electron LocalServer (main.js)
```
Se VITE_PLAYER_URL vazio:
  Inicia servidor HTTP em porta aleatória
  Serve arquivos de /dist
  SPA fallback: qualquer rota unknown → index.html
```

---

## 📊 Dados Mock Disponíveis

Localização: `frontend/src/lib/mockData.js`

### Entidades
- **mockDevices** (6 dispositivos)
  - TVs, Totens, Web Players
  - Status: online, offline, error, syncing

- **mockCampaigns** (6 campanhas)
  - Status: active, draft, ended
  - Incluem agendamento

- **mockMedia** (7 arquivos)
  - Imagens (JPG, PNG, WebP)
  - Vídeos (MP4)
  - Resoluções: 1920x1080

- **mockLocations** (6 localizações)
  - Recepção, Salas, Lojas, Restaurante

- **mockAlerts** (3 alertas)
  - Dispositivos offline, Campanhas encerrando, Mídia processando

- **mockViewsPerDay** (7 dias)
  - Gráfico de visualizações por data

---

## 🚀 Fluxo de Produção

1. **Build Frontend**
   ```bash
   npm run build
   # Gera /dist com VITE_API_URL=https://playwave.com.br
   ```

2. **Build Electron**
   ```bash
   npm run build:electron
   # Gera .exe para Windows
   ```

3. **Deploy Backend**
   ```bash
   # API roda em https://api.playwave.com.br
   URL_HOST=https://api.playwave.com.br
   ```

4. **Capacitor APK**
   ```bash
   # Usa .env.production
   # cleartext: true no capacitor.config.ts
   # CORS permitido para capacitor://localhost
   ```

---

## Checklist de Conexão

- [ ] Backend rodando (`docker-compose up -d`)
- [ ] Admin consegue fazer login (`/api/auth/login`)
- [ ] `.env.local` tem `VITE_API_URL=http://localhost:8000`
- [ ] `.env.local` tem `VITE_PLAYER_URL=http://localhost:3000/player`
- [ ] Frontend dev rodando (`npm run dev`)
- [ ] Electron dev rodando (`npm run electron:dev`)
- [ ] Console do Electron sem erros de `ECONNREFUSED`

---

## Debug

### Ver variáveis de ambiente no Electron
```javascript
// No main.js ou renderer
console.log(process.env.VITE_API_URL);
console.log(process.env.VITE_PLAYER_URL);
```

### Ver requisições de API
1. Abrir DevTools do Electron (`Ctrl+Shift+I`)
2. Aba **Network**
3. Filtrar por `localhost:8000`
4. Verificar status das requisições (200, 401, CORS erro, etc.)

### Testar saúde do backend
```bash
curl -X GET http://localhost:8000/health
# Resposta esperada: { "status": "ok" } ou 200
```
