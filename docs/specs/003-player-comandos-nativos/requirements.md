# SPEC 003 — Player Comandos Nativos

Status: especificacao inicial
Data: 2026-05-22
Projeto: PlayWave

## Objetivo

Fazer com que os comandos remotos de energia (`restart_app`, `restart_device`, `shutdown_device`) executem de fato no dispositivo, hoje todos retornam falha silenciosa em Electron e APK porque o bridge nativo nao foi implementado de verdade. Tambem padronizar o ciclo de vida do comando para que o gerenciador mostre status real (pending / sent / received / executing / completed / failed / expired) em vez de "enviado" para sempre.

## Contexto

O cliente reclamou: "o player nao esta desligando pelo gerenciador". Auditoria em 2026-05-22 confirmou:

- Backend cria comando, marca como `SENT` quando o player faz polling, e aceita ACK de `received` / `started` / `completed` / `failed`.
- Frontend do gerenciador tem botoes "Desligar Dispositivo" e "Reiniciar Dispositivo" que chamam `POST /devices/{id}/command` com `command_type` correto.
- Player faz polling 10s, marca `received`, chama o handler, marca ACK.
- O handler invoca `window.__ELECTRON__?.player?.shutdownDevice()`, mas o Electron seta apenas `window.__ELECTRON__ = true` (boolean). O `.player` nao existe, entao toda chamada cai em `platformUnsupported` e o ACK eh sempre `success=false`.
- Em APK Capacitor, o handler invoca `window.PlayWaveNative` ou `window.AndroidPlayer`, mas nenhum plugin nativo foi implementado no projeto Android.

A consequencia operacional: o gerenciador recebe `failed` ou nem recebe ACK (timeout), o cliente acha que o sistema esta quebrado.

## Escopo

Esta SPEC cobre:

- bridge real entre renderer e processo principal no Electron via `preload.js` + `contextBridge`;
- IPC handlers reais no Electron para `restart_app`, `restart_device`, `shutdown_device`, `take_screenshot`;
- plugin Capacitor `PlayWaveNativePlugin` em Java/Kotlin com os mesmos comandos;
- assumir provisionamento como Device Owner para APK ter permissao de `reboot` e `shutdown` no Android;
- separacao logica entre `restart_app` (recarrega/reabre app), `restart_device` (reboot fisico), `shutdown_device` (desliga fisico);
- expansao do ciclo de vida de comando para tratar `expired` automaticamente no backend;
- mensagem de erro clara e padronizada quando a plataforma nao suporta o comando (web puro).

Esta SPEC nao cobre:

- comandos novos alem dos ja previstos em `VALID_COMMANDS`;
- central de comandos consolidada (escopo de SPEC futura);
- auditoria avancada de comandos sensiveis;
- factory_reset, update_player, get_logs (escopo de SPEC futura).

## Arquivos analisados

### Backend

- `backend/api/v1/devices.py`
- `backend/core/models.py`
- `backend/core/schemas_completos.py`
- `backend/crud/entidades/crud_device_command.py`
- `backend/alembic/versions/002_add_device_commands.py`
- `backend/alembic/versions/20260521_0915_device_command_lifecycle.py`

### Frontend (gerenciador)

- `frontend/src/pages/DispositivoDetalhe.jsx`
- `frontend/src/api/dispositivos.js`

### Player

- `frontend/src/pages/Player.jsx`
- `frontend/src/player-core/commands.js`
- `frontend/src/player-core/platform.js`
- `frontend/electron/main.js`
- `frontend/android/app/src/main/java/com/playwave/player/MainActivity.java`

## Estado atual encontrado

### Ja existe

- Tabela `device_commands` com lifecycle expandido (PENDING/SENT/RECEIVED/EXECUTING/COMPLETED/FAILED/EXPIRED/CANCELLED).
- Endpoints `/devices/{id}/command`, `/commands/pending`, `/commands/{id}/received`, `/commands/{id}/started`, `/commands/{id}/ack`.
- `VALID_COMMANDS` no backend inclui `restart_app`, `restart_device`, `shutdown_device`.
- Botoes correspondentes em `DispositivoDetalhe.jsx`.
- `commands.js` no player com handlers que tentam acionar bridge nativo.
- IPC `player:restart` e `player:fullscreen-toggle` no `main.js` do Electron.

### Existe parcialmente

- `main.js` do Electron tem IPC apenas para `player:restart` e `player:fullscreen-toggle`. Nao ha IPC para `restart_app`, `restart_device` ou `shutdown_device`.
- `main.js` injeta `window.__ELECTRON__ = true` (boolean) em vez de objeto exposto via `contextBridge` com metodos.
- `preload.js` existe (referenciado em `webPreferences.preload`), mas nao expoe API estruturada de comandos.
- `commands.js` chama `window.__ELECTRON__?.player?.[command]` — se feito direito, funciona, mas hoje `__ELECTRON__` eh booleano.

### Falta ou precisa consolidar

- `preload.js` expor objeto `window.__ELECTRON__ = { player: { restartApp, restartDevice, shutdownDevice, takeScreenshot } }` via `contextBridge.exposeInMainWorld`.
- IPC handlers reais no `main.js`:
  - `player:restart_app` → `app.relaunch(); app.quit()`.
  - `player:restart_device` → `child_process.exec` com `shutdown /r /t 0` (Windows) ou `shutdown -r now` (Linux).
  - `player:shutdown_device` → `shutdown /s /t 0` (Windows) ou `shutdown -h now` (Linux).
  - `player:take_screenshot` → `webContents.capturePage()` + upload ou retorno base64.
- Plugin Capacitor `PlayWaveNativePlugin` em `frontend/android/app/src/main/java/com/playwave/player/`:
  - `restartApp()` → `recreate()` da Activity.
  - `restartDevice()` → `PowerManager.reboot(null)`, requer permissao `REBOOT` e Device Owner.
  - `shutdownDevice()` → `DevicePolicyManager.lockNow()` + intent de shutdown, requer Device Owner.
- Registro do plugin em `MainActivity.java` (`registerPlugin(PlayWaveNativePlugin.class)`).
- Permissoes no `AndroidManifest.xml`: `REBOOT`, `SHUTDOWN`, `DEVICE_POWER`.
- Documentacao de provisionamento como Device Owner.
- Worker/scheduler que marque comandos `expired` quando `expires_at < now`.
- Mensagem de erro padronizada `{ "platform_unsupported": true, "platform": "web", "command": "shutdown_device" }` ao gerar resultado de comando.

## Requisitos funcionais

### RF003-01 — Bridge Electron deve expor API real

O `preload.js` do Electron deve expor um objeto `window.__ELECTRON__.player` via `contextBridge.exposeInMainWorld` com os metodos `restartApp`, `restartDevice`, `shutdownDevice`, `takeScreenshot`.

Critérios:

- Cada metodo invoca o IPC correspondente via `ipcRenderer.invoke`.
- Retorna `Promise` que resolve em `void` no sucesso ou rejeita com `Error` no erro.
- `contextIsolation` permanece `true`.
- `nodeIntegration` permanece `false`.

### RF003-02 — IPC handlers reais no Electron

O processo principal do Electron deve responder aos canais `player:restart_app`, `player:restart_device`, `player:shutdown_device`, `player:take_screenshot`.

Comportamento esperado:

- `player:restart_app` → `app.relaunch()` + `app.quit()`.
- `player:restart_device` → executar comando de OS para reboot, retornar antes do reboot acontecer.
- `player:shutdown_device` → executar comando de OS para shutdown, retornar antes do shutdown acontecer.
- `player:take_screenshot` → capturar tela via `webContents.capturePage()` e retornar base64 PNG.

Detalhes por plataforma:

- Windows: usar `shutdown /r /t 0` e `shutdown /s /t 0`.
- Linux: usar `shutdown -r now` e `shutdown -h now` (assume permissao via sudoers ou execucao como root).
- macOS: fora de escopo desta SPEC.

Critérios:

- Cada handler usa `child_process.exec` ou `spawn`.
- Em caso de falha de spawn, lanca erro descritivo.
- Loga acao no console do Electron.
- Antes de chamar `shutdown` real, registra ACK de execucao no backend para nao perder o trace.

### RF003-03 — Plugin Capacitor para Android

O APK Android deve ter um plugin Capacitor `PlayWaveNativePlugin` expondo `restartApp`, `restartDevice`, `shutdownDevice`, `takeScreenshot`.

Critérios:

- Plugin esta em `frontend/android/app/src/main/java/com/playwave/player/PlayWaveNativePlugin.java`.
- Registrado em `MainActivity.java` via `registerPlugin(PlayWaveNativePlugin.class)`.
- Exposto no JS como `window.PlayWaveNative` (ou via `Capacitor.Plugins.PlayWaveNative`, e a camada `commands.js` adapta).
- `restartApp` invoca `((Activity) getContext()).recreate()` ou similar.
- `restartDevice` invoca `((PowerManager) getContext().getSystemService(Context.POWER_SERVICE)).reboot(null)`.
- `shutdownDevice` invoca metodo equivalente usando `DevicePolicyManager` (necessita Device Owner).
- `takeScreenshot` captura a view e retorna base64.

### RF003-04 — APK Android deve estar provisionado como Device Owner

Comandos `restart_device` e `shutdown_device` no Android sem root ou sem MDM exigem que o APK PlayWave seja Device Owner.

Critérios:

- Documentar passo a passo de provisionamento via ADB (`adb shell dpm set-device-owner com.playwave.player/.PlayWaveDeviceAdminReceiver`).
- Documentar opcao alternativa de provisionamento via QR code.
- Criar `PlayWaveDeviceAdminReceiver` em `frontend/android/app/src/main/java/com/playwave/player/`.
- Criar `device_admin_policies.xml` em `frontend/android/app/src/main/res/xml/`.
- Quando o APK nao estiver provisionado como Device Owner, os comandos devem retornar `failed` com `error_code = "DEVICE_OWNER_REQUIRED"` e mensagem explicativa.

### RF003-05 — Erro padronizado quando plataforma nao suporta

Quando o comando nao tem implementacao para a plataforma atual (web browser puro, smart TV nao suportada, APK sem Device Owner), o ACK do comando deve retornar resultado padronizado.

Formato:

```
{
  "success": false,
  "error_message": "shutdown_device nao suportado em web",
  "result": {
    "platform_unsupported": true,
    "platform": "web",
    "command": "shutdown_device",
    "reason": "browser_environment"
  }
}
```

Reasons aceitos:

- `browser_environment` (web puro).
- `device_owner_required` (APK sem provisionamento).
- `permission_denied` (faltou permissao do OS).
- `command_not_implemented` (plataforma reconhecida mas nao implementada).

### RF003-06 — Comandos `expired` devem ser marcados automaticamente

Comandos com `expires_at` no passado devem ser marcados como `EXPIRED` automaticamente, sem depender do player.

Critérios:

- Default de `expires_at` ao criar comando: `now + 10 minutos`.
- Comandos `pending`, `sent` ou `received` com `expires_at < now` viram `expired` em batch.
- Job Celery roda a cada 1 minuto e marca expired.
- Endpoint `/commands/pending` filtra `expires_at > now`.

### RF003-07 — UI do gerenciador mostra status detalhado

Em `DispositivoDetalhe.jsx`, ao listar comandos historicos, mostrar:

- timestamp de cada transicao (`requested_at`, `sent_at`, `received_at`, `started_at`, `executed_at`);
- status final colorido (verde completed, vermelho failed, cinza expired, azul executing);
- mensagem de erro com `error_code` quando houver;
- botao "Cancelar" para comandos ainda em `pending` ou `sent`.

### RF003-08 — Separacao clara entre app e dispositivo

Botoes no gerenciador devem deixar claro o que cada comando faz:

- "Recarregar Player" → `reload_player` (soft, recarrega URL).
- "Reiniciar App" → `restart_app` (relaunch do processo).
- "Reiniciar Dispositivo" → `restart_device` (reboot fisico do OS).
- "Desligar Dispositivo" → `shutdown_device` (shutdown fisico do OS).

Cada um com tooltip explicando o impacto e plataformas suportadas.

## Requisitos nao funcionais

- Nao quebrar IPC `player:restart` existente (manter como alias de `player:restart_app`).
- Nao quebrar comandos atualmente funcionais (`sync`, `refresh_playlist`, `clear_cache`, `set_volume`, `mute`, `unmute`).
- Comandos de energia devem retornar ACK ao backend ANTES de executar o shutdown/reboot, porque o processo do player morre durante a operacao.
- Logs do Electron devem ficar em `~/.config/PlayWave/logs/main.log` (ou equivalente) para suporte.
- Comandos sensiveis (`restart_device`, `shutdown_device`) devem ser auditados com `requested_by` obrigatorio nao nulo.
- Build de APK Android deve continuar funcionando sem mudancas no fluxo do `build:apk`.
- Build de Electron deve continuar funcionando para Windows e Linux.

## Decisoes de compatibilidade

- Estado existente `EXECUTED` permanece como alias de `COMPLETED` ate proxima limpeza.
- `window.__ELECTRON__ = true` (legado) substituido por `window.__ELECTRON__ = { player: { ... } }`. Codigo cliente que conferia `window.__ELECTRON__` truthy continua funcionando porque objeto eh truthy.
- `Platform.isElectron` detecta presenca do objeto, nao mudou.
- `commands.js` continua tentando `window.PlayWaveNative` primeiro e cai para `window.__ELECTRON__?.player` depois.

## Riscos

- Permissao `SHUTDOWN` no Android nem sempre eh concedida mesmo com Device Owner em dispositivos custom (TV Boxes baratos).
- `shutdown` no Linux pode exigir `sudo` configurado sem senha para o usuario que roda o player.
- Reboot/shutdown remoto pode deixar TV inacessivel se nao houver wake-on-LAN.
- `recreate()` da Activity Android pode nao reiniciar completamente o WebView/Capacitor em todos os builds — testar.
- Plugin Capacitor exige rebuild + reassinatura do APK.
- Se `expires_at` for muito curto, comando legitimo pode expirar antes do player buscar (player faz polling a cada 10s, considerar minimo 60s).

## Fora de escopo imediato

- Comando `factory_reset`.
- Comando `update_player` (OTA).
- Comando `get_logs` (envia logs para o backend).
- Comando `identify_screen` (pisca tela para localizar).
- Comandos em lote por campanha/local.
- Permissoes RBAC granulares para comandos sensiveis (parte de SPEC de auditoria).
- Suporte a smart TVs (Tizen, webOS) — Saira como `command_not_implemented`.
- Versao macOS do Electron.
