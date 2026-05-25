# SPEC NNN — Player

## Arquivos afetados

- `frontend/src/pages/Player.jsx`
- `frontend/src/player-core/...`
- `frontend/src/components/player/...`
- `frontend/src/components/audio/...`
- `frontend/electron/...` (se aplicavel)
- `frontend/android/...` (se aplicavel)

## Mudancas no player web/JS

### `Player.jsx`

{O que muda.}

```javascript
{pseudocodigo}
```

### `player-core/{arquivo}.js`

{O que muda ou novo arquivo.}

## Mudancas no Electron (se aplicavel)

### `electron/main.js`

{IPC handlers, configuracoes.}

### `electron/preload.js`

{contextBridge.}

## Mudancas no Capacitor / Android (se aplicavel)

### Java/Kotlin

{Plugins, permissoes, activity.}

### `AndroidManifest.xml`

{Permissoes, receivers.}

## Verificacoes pre-deploy

- {check manual em web}.
- {check em Electron Linux/Windows}.
- {check em APK Android}.

## Logging para debug

```javascript
console.log("[player] ...");
```
