# 📺 Electron = Player de TV (Apenas `/player`)

## 🎯 Esclarecimento Importante

O Electron **NÃO** renderiza o dashboard administrativo completo.

Ele renderiza **APENAS** a rota `/player`, que é:
- ✅ Player de TV/Kiosk
- ✅ Pareamento de dispositivos
- ✅ Exibição de playlist
- ✅ Controle remoto via IPC
- ❌ Dashboard administrativo (`/dashboard`, `/dispositivos`, etc)

---

## 📊 Arquitetura de Rotas

```
FRONTEND (React)
├── /login                      ← Autenticação
│
├── /player                     ← Electron carrega aqui
│   └── Player.jsx
│       ├── Pairing screen
│       ├── Playlist rendering
│       ├── Media playback
│       └── Commands listener
│
└── /* (AppLayout + protegidas)  ← Web admin carrega aqui
    ├── /dashboard              ← Dashboard
    ├── /dispositivos           ← Gerenciar TVs/Totens
    ├── /campanhas              ← Criar campanhas
    ├── /midias                 ← Upload de mídia
    └── ...
```

---

## 🖥️ DOIS CONTEXTOS DE USO

### 1️⃣ ELECTRON (Desktop Player)
```
Usuário: TV/Totem/Kiosk
URL: http://localhost:3000/player
Acesso: Read-only (apenas exibe conteúdo)
Função: Renderizar playlist de campanhas
Autenticação: Device token (não JWT admin)
```

**O que funciona:**
- ✅ Pairing com backend
- ✅ Receber playlist
- ✅ Exibir mídia
- ✅ Responder a comandos
- ✅ Enviar heartbeat

**O que NÃO funciona:**
- ❌ Gerenciar dispositivos
- ❌ Criar campanhas
- ❌ Upload de mídia
- ❌ Dashboard analytics

---

### 2️⃣ WEB (Admin Dashboard)
```
Usuário: Administrador/Operador
URL: http://localhost:5173 (dev) ou http://localhost:3000 (sem /player)
Acesso: CRUD completo
Função: Gerenciar sistema inteiro
Autenticação: JWT admin (login com email/senha)
```

**O que funciona:**
- ✅ Login admin
- ✅ Dashboard com analytics
- ✅ Gerenciar dispositivos
- ✅ Criar/editar campanhas
- ✅ Upload de mídia
- ✅ Agendamento
- ✅ Relatórios
- ✅ Configurações

---

## 🔄 FLUXO COMPLETO DO SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                  Backend FastAPI                            │
│  - Banco de dados (devices, campaigns, media)              │
│  - API REST para admin e player                            │
│  - WebSocket para notificações de playlist                 │
└──────────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │                                    │
    JWT Auth                              Device Token
         │                                    │
         │                                    │
┌────────┴──────────┐              ┌─────────┴──────────┐
│                   │              │                    │
│   WEB ADMIN       │              │   ELECTRON PLAYER  │
│ (localhost:5173)  │              │ (localhost:3000)   │
│                   │              │                    │
│ ┌─────────────┐   │              │ ┌──────────────┐  │
│ │ /login      │   │              │ │ /player      │  │
│ ├─────────────┤   │              │ │              │  │
│ │ /dashboard  │   │              │ │ ┌──────────┐ │  │
│ │             │   │              │ │ │ Pairing  │ │  │
│ │ /devices    │   │              │ │ │ Playlist │ │  │
│ │ /campaigns  │   │              │ │ │ Playback │ │  │
│ │ /media      │   │              │ │ │ Commands │ │  │
│ │ ...         │   │              │ │ └──────────┘ │  │
│ └─────────────┘   │              │ └──────────────┘  │
│ (Admin: manage)   │              │ (Player: display) │
└───────────────────┘              └───────────────────┘
```

---

## ✅ O QUE TESTAR NO ELECTRON

### 1. Pairing (Pareamento)
```
TV gera código: TV-4821
Admin digita código no backend
TV conecta com device_token
```

### 2. Playlist Reception
```
TV recebe playlist via WebSocket
Exibe primeira mídia
Aguarda comando next/prev
```

### 3. Media Playback
```
Exibe imagem (10-60s)
Play vídeo
Mostra OSD (On-Screen Display)
Responde a comando de fullscreen
```

### 4. Commands
```
Admin envia: show_desktop (10s)
TV minimiza, volta após 10s

Admin envia: take_screenshot
TV captura tela e envia

Admin envia: restart_device
TV reinicia
```

### 5. Heartbeat & Watchdog
```
A cada 30s: TV envia heartbeat
Backend atualiza last_connection
Se 5 falhas: status = offline
```

---

## 🧪 COMO TESTAR O PLAYER

### Teste 1: Pairing
```bash
# Terminal 1: Backend
docker-compose up -d

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Electron
cd frontend/electron && npm run dev
```

**Esperado:**
1. Electron abre em fullscreen (ou window)
2. Mostra "Pareamento" com código TV-XXXX
3. Sem erro CORS
4. Console limpo (Ctrl+Shift+I)

---

### Teste 2: Simular Device Pairing via API

```bash
# Parear TV programaticamente
curl -X POST http://localhost:8000/api/devices/pair \
  -H "Content-Type: application/json" \
  -d '{
    "pairing_code": "TV-4821",
    "name": "TV Teste Electron"
  }'
```

---

### Teste 3: Enviar Playlist para Device

```bash
# Criar device
curl -X POST http://localhost:8000/api/devices \
  -H "Authorization: Bearer <JWT_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TV Electron Test",
    "location": "Dev",
    "ip_address": "127.0.0.1"
  }'

# Atribuir campanha
curl -X PUT http://localhost:8000/api/devices/<DEVICE_ID> \
  -H "Authorization: Bearer <JWT_ADMIN>" \
  -d '{"current_campaign": "Campanha Abril"}'
```

---

## 🚀 PARA TESTAR O DASHBOARD ADMIN

**NÃO use o Electron. Use o navegador:**

```bash
# Terminal 1: Backend
docker-compose up -d

# Terminal 2: Frontend
cd frontend && npm run dev

# Browser: http://localhost:5173
# Login: admin@playwave.com
# Senha: &2p0Kw45A&lLNX4bM%gpH*cy
```

**Agora você tem:**
- ✅ Dashboard completo
- ✅ Gerenciar dispositivos
- ✅ Criar campanhas
- ✅ Upload de mídia
- ✅ Mock data visual
- ✅ Usar DevTools normalmente

---

## 📋 RESUMO

| Contexto | URL | Tipo | Função |
|----------|-----|------|--------|
| **Electron** | http://localhost:3000/player | Player | Exibir conteúdo |
| **Web Admin** | http://localhost:5173 | Dashboard | Gerenciar sistema |
| **Web Admin (Prod)** | https://playwave.com.br | Dashboard | Prod |

---

## 🎯 PRÓXIMOS PASSOS

### Para testar o PLAYER (Electron):
1. Implementar pairing real
2. Testar playlist reception
3. Testar media playback
4. Testar commands (screenshot, restart, etc)
5. Testar heartbeat/watchdog

### Para testar o ADMIN (Web):
1. Usar o navegador, não Electron
2. Testar CRUD de dispositivos
3. Testar CRUD de campanhas
4. Testar upload de mídia
5. Testar atribuição device↔campaign

---

## 📖 Estrutura de Player.jsx

```javascript
// Player.jsx — Componente do Player de TV

export default function Player() {
  // 1. Inicializar
  const [pairingCode, setPairingCode] = useState(generateCode());
  const [isConnected, setIsConnected] = useState(false);
  
  // 2. Pareamento
  useEffect(() => {
    pairRequest(pairingCode)
      .then(device => {
        setIsConnected(true);
        setDeviceToken(device.token);
      });
  }, []);
  
  // 3. Receber Playlist
  useEffect(() => {
    if (!isConnected) return;
    getDevicePlaylist(deviceToken)
      .then(playlist => setPlaylist(playlist));
  }, [isConnected]);
  
  // 4. Renderizar
  if (!isConnected) return <PairingScreen code={pairingCode} />;
  if (currentMedia) return <MediaRenderer media={currentMedia} />;
  return <LoadingScreen />;
}
```

---

## ⚠️ IMPORTANTE

**Electron não é para testar o admin dashboard!**

Se você quiser testar o dashboard administrativo com mock data:
```bash
npm run dev
# Abra http://localhost:5173
# Login com admin@playwave.com
```

Se você quiser testar o player de TV:
```bash
cd frontend/electron
npm run dev
```

---

**Última atualização**: 2026-06-04  
**Esclarecimento**: Electron renderiza APENAS `/player` (Player de TV)  
**Para Admin Dashboard**: Use `npm run dev` + navegador

