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
