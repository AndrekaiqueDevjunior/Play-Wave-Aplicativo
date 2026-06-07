# SPEC 009 - Player / Electron

## Player React

Arquivos:

- `frontend/src/pages/Player.jsx`
- `frontend/src/player-core/commands.js`
- `frontend/src/player-core/platform.js`

## Handlers novos em `commands.js`

Adicionar:

- `minimize_player`;
- `restore_player`;
- `show_desktop`.

Os handlers devem chamar o bridge nativo:

```js
window.PlayWaveNative || window.AndroidPlayer || window.__ELECTRON__?.player
```

Metodos esperados:

- `minimizeWindow`;
- `restoreWindow`;
- `showDesktop`.

Se ausente:

- web puro: `BROWSER_ENVIRONMENT`;
- plataforma reconhecida sem handler: `COMMAND_NOT_IMPLEMENTED`.

## Electron preload

Arquivo:

`frontend/electron/preload.js`

Adicionar:

```js
minimizeWindow: () => ipcRenderer.invoke("player:minimize_window"),
restoreWindow:  (opts) => ipcRenderer.invoke("player:restore_window", opts),
showDesktop:    (opts) => ipcRenderer.invoke("player:show_desktop", opts),
```

## Electron main

Arquivo:

`frontend/electron/main.js`

Adicionar handlers:

- `player:minimize_window`;
- `player:restore_window`;
- `player:show_desktop`.

Comportamento sugerido:

### minimize_window

1. guardar estado anterior de fullscreen;
2. `mainWindow.setFullScreen(false)` se necessario;
3. `mainWindow.setAlwaysOnTop(false)` se necessario;
4. `mainWindow.minimize()`.

### restore_window

1. `mainWindow.restore()`;
2. `mainWindow.show()`;
3. `mainWindow.focus()`;
4. restaurar fullscreen se `restore_fullscreen=true` ou se estado anterior indicava fullscreen;
5. restaurar alwaysOnTop quando aplicavel.

### show_desktop

1. chamar minimize;
2. aguardar `duration_seconds`;
3. chamar restore.

## Scheduler local

Novo helper opcional:

`frontend/src/player-core/windowExposureScheduler.js`

Responsabilidades:

- iniciar rotina;
- cancelar rotina;
- manter apenas um timeout ativo;
- chamar `executeCommand({ command_type: "show_desktop", payload })`;
- nao rodar durante `waiting`/`pairing`.

## Limitacoes

### Browser puro

Nao suporta minimizar/restaurar janela por seguranca do navegador.

### Android

Fora do escopo inicial. O plugin `PlayWaveNativePlugin.java` nao deve ser alterado no PR 1.

### Smart TV Web

Nao suportado sem app nativo.

## Teste manual minimo

Electron dev/prod:

1. abrir Player Electron;
2. enviar `show_desktop` com 5s;
3. confirmar que a area de trabalho fica visivel;
4. confirmar que o Player volta;
5. verificar historico do comando como `completed`.


