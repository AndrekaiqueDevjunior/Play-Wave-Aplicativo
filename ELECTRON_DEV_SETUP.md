# 🖥️ Electron Development Setup — Windows

## ✅ Status
- Backend Docker: ✓ Rodando em `http://localhost:8000`
- Frontend npm: ✓ Pronto em `http://localhost:5173`
- Electron npm: ✓ Script `dev` adicionado

---

## 🚀 Iniciar Electron em 3 Terminais

### Terminal 1: Backend (já deve estar rodando)
```bash
docker-compose ps
# Verificar se 5 containers estão UP
```

### Terminal 2: Frontend Dev Server
```bash
cd "C:\Users\Kaik\Documents\VScode\PlayWave\Play-Wave-Aplicativo\frontend"

npm run dev
# Aguarda alguns segundos...
# Abre em http://localhost:5173
```

### Terminal 3: Servidor Player (porta 3000)
```bash
cd "C:\Users\Kaik\Documents\VScode\PlayWave\Play-Wave-Aplicativo\frontend"

npm run preview -- --port 3000
# Abre em http://localhost:3000
# Carrega a SPA do build ou dev
```

### Terminal 4: Electron App
```bash
cd "C:\Users\Kaik\Documents\VScode\PlayWave\Play-Wave-Aplicativo\frontend\electron"

npm run dev
# Abre janela do Electron
# Carrega de http://localhost:3000/player
# Com DevTools ativado (NODE_ENV=development)
```

---

## ✅ Teste de Conexão

Assim que a janela Electron abrir:

1. **Abrir DevTools**: `Ctrl+Shift+I`
2. **Aba Console**: Procurar por:
   - `[electron] local server on port...` ❌ (significa VITE_PLAYER_URL vazio)
   - `[electron] window ready` ✓ (carregou corretamente)
3. **Aba Network**: Ver requisições a `localhost:8000`

### Login Test
```
Email: admin@playwave.com
Senha: &2p0Kw45A&lLNX4bM%gpH*cy
```

**Esperado**: 
- ✓ Form carrega
- ✓ Login POST → `http://localhost:8000/api/auth/login`
- ✓ Status: 200 OK
- ✓ Redireciona para `/dashboard`

---

## 📊 O que mudou

### Electron package.json
```json
{
  "scripts": {
    "start": "electron .",
    "dev": "cross-env NODE_ENV=development VITE_PLAYER_URL=http://localhost:3000/player electron .",
    "build:win": "electron-builder --win",
    "build:linux": "electron-builder --linux",
    "build:all": "electron-builder --win --linux"
  }
}
```

**Novo script `dev`**:
- `cross-env` → Windows-compatible env vars
- `NODE_ENV=development` → Ativa DevTools + logs
- `VITE_PLAYER_URL=http://localhost:3000/player` → Carrega SPA da porta 3000

---

## 🔍 Debug

### Se nada abrir após `npm run dev`

**Verificar logs**:
```bash
# Ver se electron iniciou
npm run dev 2>&1 | head -20
```

**Se der erro "electron not found"**:
```bash
npm install
npm run dev
```

**Se der erro "port 3000 já em uso"**:
```bash
# Matar processo que está usando a porta
# Windows PowerShell
Get-Process | Where-Object {$_.Port -eq 3000}
# Então: Stop-Process -Id <PID> -Force

# Ou trocar porta do preview
npm run preview -- --port 3001
# Atualizar VITE_PLAYER_URL no script dev
```

---

## 🎯 Próximos Testes

### 1. Login Funciona?
- [ ] Entrar no dashboard ✓
- [ ] Dashboard carrega dados mock ✓
- [ ] Sidebar aparece ✓

### 2. Navegação Funciona?
- [ ] Clicar em "Dispositivos" ✓
- [ ] Clicar em "Campanhas" ✓
- [ ] Clicar em "Mídia" ✓

### 3. Dados Mock Aparecem?
- [ ] 6 dispositivos listados ✓
- [ ] Status badges (online/offline) ✓
- [ ] Campanhas com status ✓
- [ ] Alertas com severidade ✓

### 4. API Real Funciona?
- [ ] DevTools → Network: Ver `/api/devices`
- [ ] Status: 200 OK (não 401 ou 404)
- [ ] Response: Array de devices

---

## 📋 Arquivos Atualizados

| Arquivo | Mudança |
|---------|---------|
| `frontend/electron/package.json` | Adicionado script `dev` |
| `frontend/electron/node_modules/` | Instalado `cross-env` |
| `frontend/.env.local` | `VITE_PLAYER_URL=http://localhost:3000/player` |

---

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| "electron not found" | `npm install` na pasta electron |
| "Janela não abre" | Verificar console do terminal 4 |
| "Backend não conectado" | Verificar `docker-compose ps` |
| "Porta 3000 em uso" | Matar processo ou trocar porta |
| "DevTools não aparece" | Esperar alguns segundos |
| "Login não funciona" | Verificar credenciais: `admin@playwave.com` |

---

## 📸 Screenshots Esperados

### 1. DevTools Console (Sucesso)
```
[electron] window ready — platform: win32
[electron] powerSaveBlocker started, id: 1
[electron] local server on port <random>  ❌ NÃO deve aparecer
```
Esperado: Sem mensagens de erro

### 2. Login Form
```
╔════════════════════════════════════╗
║       PlayWave                     ║
║                                    ║
║   📧 Email                         ║
║   [                          ]     ║
║                                    ║
║   🔐 Senha                         ║
║   [                          ]     ║
║                                    ║
║   ☐ Lembrar acesso                 ║
║                                    ║
║        [ Entrar ]                  ║
║                                    ║
╚════════════════════════════════════╝
```

### 3. Dashboard (Após Login)
```
┌─────────────────────────────────────┐
│ PlayWave Dashboard  [✕]             │
├──────────────────┬──────────────────┤
│ MENU             │ Bem-vindo, Admin │
│ ☰ Dashboard      │                  │
│ 📱 Dispositivos  │ ┌──────────────┐ │
│ 🎬 Campanhas     │ │ 5 Online     │ │
│ 🎥 Mídia         │ │ 1 Offline    │ │
│ 📊 Relatórios    │ └──────────────┘ │
│ ⚙️  Configuração │                  │
│ 🚪 Logout        │ [Gráfico]        │
│                  │                  │
└──────────────────┴──────────────────┘
```

---

## 🎓 Referências

- **Electron**: https://www.electronjs.org/docs
- **Vite Preview**: https://vitejs.dev/guide/ssr.html#dev-server
- **Cross-env**: https://github.com/kentcdodds/cross-env

---

**Último update**: 2026-06-04  
**Status**: ✅ Pronto para testar  
**Próximo**: Abrir 4 terminais e rodar os comandos acima

