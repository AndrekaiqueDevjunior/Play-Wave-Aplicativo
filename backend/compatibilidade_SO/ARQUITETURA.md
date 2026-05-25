# PlayWave — Arquitetura Multiplataforma

## Visão Geral

```
┌─────────────────────────────────────────────────────────┐
│               PlayWave Player Core                      │
│                                                         │
│  frontend/src/player-core/                              │
│  ├── platform.js    ← detecção de plataforma            │
│  ├── storage.js     ← localStorage + IndexedDB          │
│  ├── network.js     ← retry, watchdog, online/offline   │
│  └── commands.js    ← engine de comandos remotos        │
│                                                         │
│  frontend/src/pages/Player.jsx    ← player principal    │
│  frontend/src/components/audio/AudioPlayer.jsx          │
│  frontend/src/components/player/MediaRenderer.jsx       │
└─────────────────────────────────────────────────────────┘
           │
    ┌──────┴──────────────────────────┐
    │                                 │
    ▼                                 ▼
┌──────────────┐              ┌────────────────────┐
│   WEB        │              │  DESKTOP           │
│  (Browser)   │              │  (Electron)        │
│              │              │                    │
│  - Chrome    │              │  frontend/electron/│
│  - Firefox   │              │  ├── main.js       │
│  - Tizen     │              │  ├── preload.js    │
│  - WebOS     │              │  └── package.json  │
│  - Any WebV  │              │                    │
└──────────────┘              │  Windows: .exe     │
                              │  Linux: AppImage/  │
                              │  .deb / .rpm       │
                              └────────────────────┘
                                        │
                              ┌─────────┴──────────┐
                              │  MOBILE / TV       │
                              │  (Capacitor)       │
                              │                    │
                              │  frontend/         │
                              │  capacitor.config  │
                              │                    │
                              │  Android APK       │
                              │  Android TV        │
                              │  TV Box Android    │
                              └────────────────────┘
```

## Núcleo Compartilhado

O mesmo código React roda em todas as plataformas:

| Módulo           | Responsabilidade                              |
|------------------|-----------------------------------------------|
| `platform.js`    | Detecta plataforma, fullscreen, wakeLock      |
| `storage.js`     | Pareamento, cache de playlist, estado         |
| `network.js`     | Retry, watchdog, detecção online/offline      |
| `commands.js`    | Execução de comandos remotos sem reload       |
| `Player.jsx`     | Orquestrador principal (polling, SSE, estado) |
| `AudioPlayer.jsx`| Motor de áudio persistente (nunca desmonta)   |
| `MediaRenderer`  | Renderização de vídeo/imagem/url              |

## Plataformas

### Web / Smart TVs
- **Acesso direto**: `http://SEU_SERVIDOR/player`
- Tizen (Samsung): abrir URL no Samsung Smart TV Developer
- WebOS (LG): abrir URL no webOS Developer Mode
- Limitações: autoplay depende de gesto inicial

### Linux (AppImage / .deb)
- **Base**: Electron 28+
- **Kiosk**: fullscreen automático, sem barra de título
- **Auto-start**: systemd service
- **ARM64**: suportado (TV Box, Raspberry Pi)
- **Build**: `backend/compatibilidade_SO/linux/build.sh`

### Windows (.exe)
- **Base**: Electron 28+
- **Kiosk**: modo kiosk ativo por padrão
- **Auto-start**: registro do Windows
- **Build**: `backend/compatibilidade_SO/windows/build.bat`

### Android (APK / TV)
- **Base**: Capacitor 6+
- **Suporte**: Android 8+, Android TV, TV Box
- **Orientação**: landscape permanente
- **Wake Lock**: tela nunca apaga
- **Build**: `backend/compatibilidade_SO/apk/build.sh`

## Comandos Remotos (sem reload)

| Comando          | Efeito                                    |
|------------------|-------------------------------------------|
| `sync`           | Recarrega playlist (soft, sem reload)     |
| `refresh_playlist`| Recarrega playlist (soft, sem reload)    |
| `clear_cache`    | Limpa IndexedDB + recarrega playlist      |
| `restart`        | Soft reset de estado, preserva áudio      |
| `set_volume`     | Ajusta volume do áudio (payload.volume)   |
| `mute`           | Silencia vídeo e áudio                    |
| `unmute`         | Ativa vídeo e áudio                       |

## Checklist de Produção

- [ ] `VITE_API_URL` apontando para servidor de produção
- [ ] HTTPS configurado no servidor
- [ ] `PLAYER_KIOSK=true` nos deploys de TV
- [ ] Systemd service configurado (Linux)
- [ ] Auto-start no registro (Windows)
- [ ] Wake lock confirmado (Android)
- [ ] AudioPlayer nunca desmontando
- [ ] Watchdog ativo (120s sem heartbeat = reconexão)
- [ ] Cache IndexedDB configurado
- [ ] Comandos remotos testados end-to-end
