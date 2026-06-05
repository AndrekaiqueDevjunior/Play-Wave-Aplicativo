# PlayWave Player — Build Electron

Player desktop empacotado com Electron para Windows e Linux (kiosk 24/7).

## Estrutura

- `main.js` — processo principal: kiosk window, watchdog, IPC handlers,
  servidor HTTP local servindo `dist/`.
- `preload.js` — bridge segura (`contextBridge`) entre renderer e main.
  Expõe `window.__ELECTRON__.player.*` para comandos remotos.
- `package.json` — config do electron-builder.

## SPEC 003 — Comandos remotos nativos

A partir da SPEC 003 o Electron implementa os IPC handlers:

| Canal | Ação |
|---|---|
| `player:restart_app`     | `app.relaunch()` + `app.quit()` |
| `player:restart_device`  | `shutdown /r` (Win) ou `shutdown -r` (Linux) |
| `player:shutdown_device` | `shutdown /s` (Win) ou `shutdown -h` (Linux) |
| `player:take_screenshot` | `mainWindow.webContents.capturePage()` |
| `player:restart`         | legado, alias de `restart_app` |

## SPEC 009 — Window Control Commands

A partir da SPEC 009 o Electron implementa os IPC handlers para minimização programada:

| Canal | Ação | Parâmetros |
|---|---|---|
| `player:minimize_window`  | `mainWindow.minimize()` | — |
| `player:restore_window`   | `mainWindow.restore()` + restaura fullscreen | — |
| `player:show_desktop`     | Minimiza + auto-restore | `duration_seconds` (1-300s, default 10s) |

### Comportamento

**`minimize_window`**: Minimiza a janela para a taskbar/tray.

**`restore_window`**: Restaura a janela do minimize, preservando estado anterior (fullscreen, kiosk, etc).

**`show_desktop`** (Principal): Minimiza a janela por N segundos, mostrando o desktop. Após o timeout, restaura automaticamente para o estado anterior (fullscreen, kiosk, etc).

#### Snapshot de Estado

Antes de minimizar, `show_desktop` captura um snapshot do estado atual:

```javascript
const snapshot = {
  fullscreen: mainWindow.isFullScreen(),
  kiosk: mainWindow.isKiosk(),
  alwaysOnTop: mainWindow.isAlwaysOnTop(),
}
```

Mesmo que o usuário saia de fullscreen manualmente durante a exposição do desktop, o restore usa o snapshot original — garantindo que a janela volta ao estado de kiosk.

#### Validação de Input

O parâmetro `duration_seconds` é validado e clamped:

```javascript
const duration = Math.max(1, Math.min(300, Math.round(Number(durationSeconds) || 10)));
```

- Mínimo: 1 segundo
- Máximo: 300 segundos
- Padrão: 10 segundos
- Tipo: int (não aceita strings)

### Uso (Backend → Electron)

O backend envia um comando `show_desktop` via API:

```bash
POST /devices/{device_id}/commands
Content-Type: application/json

{
  "command_type": "show_desktop",
  "payload": {
    "duration_seconds": 5,
    "restore_fullscreen": true
  }
}
```

O player recebe via SSE e executa:

```javascript
await callNativeWindowCommand("player:show_desktop", 5, true);
```

### Scheduler Local

O player também pode agendar `show_desktop` localmente (sem backend):

```javascript
// Em frontend/src/player-core/windowExposureScheduler.js
// Agendado a cada interval_seconds, executa show_desktop com duration_seconds
```

O scheduler:
- ✅ Respeita a fase do player (não executa em `loading`/`waiting`)
- ✅ Cancela timers anteriores (previne acúmulo)
- ✅ Continua após SSE reconectar
- ✅ É 100% local (não faz chamadas de API)

### Plataformas Suportadas

- ✅ **Windows Electron**: Totalmente suportado
- ✅ **Linux Electron**: Suportado (teórico, testar em produção)
- ❌ **Android/Smart TV/iOS**: Retorna `platform_unsupported`

Veja [`LIMITACOES_PLATAFORMAS.md`](./LIMITACOES_PLATAFORMAS.md) para detalhes.

### Segurança

- ✅ Sem shell execution (apenas Electron APIs)
- ✅ Input validado e clamped (não vulnerable a injection)
- ✅ Context isolation ativado (`contextIsolation: true`)
- ✅ Preload bridge expõe apenas funções seguras

Veja [`VALIDACAO_SEGURANCA.md`](./VALIDACAO_SEGURANCA.md) para análise completa.

---

## Pré-requisitos para shutdown/reboot

### Windows

O processo do Electron precisa rodar com permissão de Administrador (ou o
usuário precisa estar autorizado em `Local Security Policy → User Rights
Assignment → Shut down the system`).

Recomendado: criar atalho do PlayWave que sempre roda como Administrador.

### Linux

`shutdown` é binário privilegiado. O usuário que roda o player precisa de
sudoers configurado para executar sem senha:

```sudoers
# /etc/sudoers.d/playwave
playwave ALL=(root) NOPASSWD: /sbin/shutdown
```

(Substitua `playwave` pelo usuário do sistema.)

Sem isso, o `shutdown -h now` retorna `permission denied` e o ACK do comando
volta com `error_code: PERMISSION_DENIED`.

Alternativa: rodar o player como `root` (não recomendado por segurança).

## Build

```bash
npm install
npm run build           # constrói o dist/ do Vite
npm run electron:build  # empacota para Win/Linux
```

Saída em `dist-electron/`.

## Dev local

```bash
npm run dev               # Vite em :5173
NODE_ENV=development npx electron frontend/electron/main.js
```

Em dev o `KIOSK` é desligado por default — para forçar kiosk:

```bash
PLAYER_KIOSK=true npx electron frontend/electron/main.js
```

## URL externa (debug)

Para apontar o Electron para um servidor remoto (em vez do dist/ embutido):

```bash
VITE_PLAYER_URL="https://playwave.com.br/player" npx electron .
```

## Logs

Stdout do processo Electron contém todos os IPC + heartbeats. Em produção
considerar redirecionar para `~/.config/PlayWave/logs/main.log`.

## Troubleshooting

### `window.__ELECTRON__.player.shutdownDevice is not a function`

Bug pré-SPEC 003. Atualizar o bundle do player e verificar que `preload.js`
está com o conteúdo novo. O `__ELECTRON__` deve ser um objeto, não `true`.

### `shutdown: command not found`

Linux: instalar `systemd` (deve estar por default). Container: precisa do
binário `shutdown` ou trocar para `systemctl poweroff`.

### Comando executado mas máquina não desliga

Verificar permissão sudoers (Linux) ou Administrador (Windows). Logs do
Electron mostram a saída do `exec`.
