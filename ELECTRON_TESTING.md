# Testes do Electron + Backend

## 🧪 Teste Rápido (5 minutos)

### Pré-requisitos
- Docker rodando
- Node.js 18+
- Backend em `http://localhost:8000`

### Passo 1: Verificar Backend
```bash
curl -X GET http://localhost:8000/health
# Esperado: {"status":"ok"} ou 200 OK
```

### Passo 2: Verificar Credenciais Admin
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@playwave.com",
    "password": "&2p0Kw45A&lLNX4bM%gpH*cy"
  }'

# Esperado: 200 OK com token JWT
```

### Passo 3: Iniciar Frontend
```bash
cd frontend
npm install
npm run dev
# Abre em http://localhost:5173
```

### Passo 4: Testar Login na Web
1. Abrir browser em `http://localhost:5173`
2. Email: `admin@playwave.com`
3. Senha: `&2p0Kw45A&lLNX4bM%gpH*cy`
4. Esperado: Redireciona para `/dashboard` ✓

---

## 🖥️ Teste Electron

### Passo 1: Iniciar Servidor Player
```bash
cd frontend
npm run preview -- --port 3000
# Abre servidor em http://localhost:3000
# Testa http://localhost:3000/player
```

### Passo 2: Iniciar Electron
```bash
cd frontend/electron
npm install
npm run electron:dev
# Abre janela do Electron
# Carrega de VITE_PLAYER_URL=http://localhost:3000/player
```

### Passo 3: Debug
- **Abrir DevTools**: `Ctrl+Shift+I`
- **Aba Console**: Ver erros de carregamento
- **Aba Network**: Ver requisições à API

### Esperado ✓
1. Janela Electron abre mostrando a tela de login
2. Form de login carregado
3. Sem erros de CORS
4. Sem erros de conexão
5. Consegue fazer login com admin@playwave.com

---

## 🐛 Diagnóstico: "Backend não conectado"

### Cenário 1: CORS Error
```
Access to XMLHttpRequest at 'http://localhost:8000/api/auth/login' 
from origin 'http://localhost:3000' blocked by CORS policy
```

**Solução**: Adicionar `http://localhost:3000` a `ALLOWED_ORIGINS` no `.env`
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,...
# Reiniciar docker-compose
docker-compose down && docker-compose up -d
```

---

### Cenário 2: Connection Refused
```
Failed to fetch
TypeError: Failed to fetch
```

**Causas**:
1. Backend não está rodando
2. Porta 8000 diferente
3. VITE_API_URL vazio

**Testes**:
```bash
# Verificar se backend roda
docker ps | grep playwave-backend

# Verificar porta 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Verificar .env
cat frontend/.env.local | grep VITE_API_URL
```

---

### Cenário 3: VITE_API_URL Vazio
```javascript
// frontend/src/lib/AuthContext.jsx linha 4
const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
// Se VITE_API_URL vazio: API_URL = ""
// Fetch vai para origem atual (http://localhost:3000)
```

**Solução**: Editar `frontend/.env.local`
```bash
VITE_API_URL=http://localhost:8000
VITE_PLAYER_URL=http://localhost:3000/player
npm run dev  # Recarrega variáveis
```

---

### Cenário 4: Electron Carrega Porta Errada
Lê-se na console: `[electron] local server on port 54321`

Significa que `VITE_PLAYER_URL` estava vazio e Electron criou um servidor local.

**Solução**: 
1. Certificar que `frontend/.env.local` tem `VITE_PLAYER_URL=http://localhost:3000/player`
2. Reiniciar `npm run electron:dev`

---

## ✅ Checklist de Teste Completo

### Backend (Docker)
- [ ] `docker-compose up -d` rodando
- [ ] 5 containers saudáveis (postgres, redis, rabbitmq, backend, frontend)
- [ ] `curl http://localhost:8000/health` retorna 200
- [ ] Admin consegue fazer login

### Frontend Web
- [ ] `npm run dev` rodando em http://localhost:5173
- [ ] Tela de login carregada
- [ ] Login funciona
- [ ] Dashboard aparece
- [ ] Console sem erros

### Frontend Electron Server
- [ ] `npm run preview -- --port 3000` rodando
- [ ] http://localhost:3000/player retorna HTML (SPA)
- [ ] DevTools mostra `Content-Type: text/html`

### Electron App
- [ ] `npm run electron:dev` abre janela
- [ ] Janela em modo fullscreen/kiosk (se `PLAYER_KIOSK=true`)
- [ ] Tela de login renderiza
- [ ] Cursor oculto em modo kiosk
- [ ] Sem errors no console

### Conexão API
- [ ] DevTools → Network → `/api/auth/login`
- [ ] Status: 200 OK
- [ ] Response headers: `Authorization: Bearer eyJ...`
- [ ] Local Storage tem `pw_access_token`
- [ ] Consegue navegbar para `/dashboard`

---

## 📊 Teste de Performance

### Memory Usage
```bash
# Ver consumo de RAM do Electron
ps aux | grep electron  # macOS/Linux
tasklist | findstr electron  # Windows
```

Esperado: < 300 MB

### Network Latency
DevTools → Network → aba "Timing"

Esperado:
- Login: < 200ms
- Dashboard: < 500ms
- Listar devices: < 300ms

---

## 🎥 Teste Visual

### Página de Login
- [ ] Logo PlayWave visível
- [ ] Input email visível
- [ ] Input senha visível
- [ ] Checkbox "Lembrar acesso" visível
- [ ] Botão "Entrar" visível
- [ ] Campo de erro em caso de falha

### Dashboard
- [ ] Sidebar com menu visível
- [ ] Cards de resumo (devices online, campanhas ativas)
- [ ] Gráfico de views por dia
- [ ] Alertas listados
- [ ] Sem layout quebrado

### Dispositivos
- [ ] Lista de 6 devices (mockData)
- [ ] Status badges coloridas (verde=online, vermelho=offline)
- [ ] IP visible
- [ ] Versão do player visível

### Campanhas
- [ ] Lista com 6 campanhas
- [ ] Status badges (ativa, rascunho, encerrada)
- [ ] Datas visíveis
- [ ] Contagem de devices atribuídos

---

## 🔍 Debug Console

### Verificar VITE_API_URL
```javascript
// Console do Electron
console.log(import.meta.env.VITE_API_URL);
// Esperado: "http://localhost:8000"
```

### Verificar Token
```javascript
localStorage.getItem('pw_access_token');
sessionStorage.getItem('pw_access_token');
// Esperado: "eyJhbGciOiJIUzI1NiIs..." (JWT válido)
```

### Testar API Manualmente
```javascript
fetch('http://localhost:8000/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('pw_access_token')}`
  }
}).then(r => r.json()).then(console.log);

// Esperado: { id, name, email, role, ... }
```

### Monitorar Requisições
```javascript
// Interceptar todas as requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log('FETCH:', args[0]);
  return originalFetch.apply(this, args);
};
```

---

## 🚀 Teste de Build

### Build Frontend
```bash
cd frontend
npm run build
# Gera /dist com VITE_API_URL=https://playwave.com.br
```

### Build Electron
```bash
cd frontend/electron
npm run build
# Gera PlayWave.exe para Windows
```

### Teste do .exe
```bash
# Windows
./dist/PlayWave Setup 1.0.0.exe
# Abre installer
```

---

## 📋 Teste de Regressão

### Após atualizar dependências
```bash
npm install
npm run build
npm run electron:dev
# Verificar se tudo ainda funciona
```

### Após alterar .env
```bash
# Limpar node_modules se necessário
rm -rf node_modules/.vite
npm run dev
# Verificar se variáveis carregam
```

---

## 📝 Relatório de Teste

Usar este template:

```markdown
# Teste Electron - [DATA]

## Versões
- Node: $(node -v)
- Electron: 27.0.0
- Vite: 4.0.0

## Backend
- [x] Docker rodando
- [x] Login funciona
- [x] Health check OK

## Frontend Web
- [x] Dev server OK
- [x] Login funciona
- [x] Dashboard carrega

## Electron
- [x] App inicia
- [x] Sem erros de CORS
- [x] Login funciona
- [x] Dashboard carrega

## Issues
- [ ] Nenhum

## Aprovado ✓
```

---

## 🎯 Próximas Etapas

1. **Automação de Testes**
   - Cypress para E2E
   - Playwright para UI
   - GitHub Actions para CI/CD

2. **Monitoring em Produção**
   - Sentry para erro tracking
   - Datadog para performance
   - LogRocket para session replay

3. **Load Testing**
   - K6 para stress test
   - Apache JMeter
   - Locust para backend

