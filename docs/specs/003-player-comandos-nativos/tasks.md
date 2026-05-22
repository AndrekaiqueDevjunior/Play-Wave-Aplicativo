# SPEC 003 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Pre-requisitos

- [ ] Decidir politica de `sudoers` no Linux para `shutdown` (documentar).
- [ ] Validar acesso ao APK production e provisionamento Device Owner.
- [!] Decidir se shutdown Android limitado a `lockNow()` eh aceitavel ou se precisa integracao MDM (Knox/SureMDM/etc).

## Backend

- [ ] Criar migration `2026XXXX_command_defaults_and_index`:
  - [ ] Indice composto `ix_device_commands_device_status_expires`.
  - [ ] Coluna `is_destructive` (boolean, default false).
  - [ ] Backfill de `is_destructive` para registros historicos.
- [ ] Atualizar `crud_device_command.create` para setar `expires_at` default (now + 10min, configuravel via `expires_in_seconds`).
- [ ] Atualizar `crud_device_command.create` para setar `is_destructive` baseado em `command_type`.
- [ ] Atualizar `crud_device_command.get_pending` para filtrar `expires_at IS NULL OR expires_at > now`.
- [ ] Criar `crud_device_command.mark_expired_batch`.
- [ ] Validar `requested_by` obrigatorio para comandos destrutivos no endpoint `POST /devices/{id}/command`.
- [ ] Aceitar `expires_in_seconds` (60-3600) no schema `DeviceCommandCreate`.
- [ ] Expandir schema `DeviceCommandResponse` com `is_destructive`.
- [ ] Migrar schema `DeviceCommandAck.result` para `CommandAckResult` (manter `extra="allow"`).
- [ ] Publicar evento SSE `command:new` quando comando eh criado (em `services/event_bus` ou similar).

## Celery

- [ ] Criar task `tasks.commands.expire_stale_commands`.
- [ ] Registrar no beat schedule (`backend/core/celery.py`): rodar a cada 60s.
- [ ] Confirmar fila e prioridade adequada.

## Electron

- [ ] Reescrever `frontend/electron/preload.js` para usar `contextBridge.exposeInMainWorld("__ELECTRON__", { player: {...} })`.
- [ ] Remover injecao de `window.__ELECTRON__ = true` em `main.js` no `dom-ready`.
- [ ] Adicionar `child_process.exec` helper `runShell` em `main.js`.
- [ ] Adicionar IPC handlers `player:restart_app`, `player:restart_device`, `player:shutdown_device`, `player:take_screenshot`.
- [ ] Manter `ipcMain.on("player:restart", ...)` como alias de `restart_app`.
- [ ] Logar no console todas as invocacoes IPC.

## Android (APK Capacitor)

- [ ] Criar `PlayWaveDeviceAdminReceiver.java`.
- [ ] Criar `res/xml/device_admin_policies.xml`.
- [ ] Criar `PlayWaveNativePlugin.java`.
- [ ] Atualizar `MainActivity.java` para `registerPlugin(PlayWaveNativePlugin.class)`.
- [ ] Adicionar `uses-permission android:name="android.permission.REBOOT"` no `AndroidManifest.xml`.
- [ ] Adicionar `<receiver>` do Device Admin no `AndroidManifest.xml`.
- [ ] Rebuild APK e testar em ao menos 1 TV Box.

## Player (JS)

- [ ] Adicionar wrapper Capacitor em `player-core/platform.js` que expoe `window.PlayWaveNative` a partir do plugin nativo.
- [ ] Atualizar `player-core/commands.js`:
  - [ ] `platformUnsupported` aceitar `reason` e setar `err.code`.
  - [ ] `executeCommand` propagar `error_code` e `platform_unsupported` no `result`.
- [ ] Atualizar `Player.jsx`:
  - [ ] Pre-ACK para comandos destrutivos (`restart_app`, `restart_device`, `shutdown_device`).
  - [ ] Escutar evento SSE `command:new` e disparar `buscarComandosPendentes()` imediatamente.

## Frontend Gerenciador

- [ ] Reorganizar botoes de comando em `DispositivoDetalhe.jsx` em 3 grupos (operacional / reset / energia).
- [ ] Adicionar tooltips explicativos.
- [ ] Adicionar modal `DestructiveCommandConfirmDialog` para comandos destrutivos.
- [ ] Criar `frontend/src/utils/deviceCommands.js` com `COMMAND_LABELS`, `STATUS_LABELS`, `statusFor`.
- [ ] Criar `frontend/src/components/devices/CommandHistoryTimeline.jsx`.
- [ ] Substituir lista atual de comandos por `CommandHistoryTimeline`.
- [ ] Implementar acao "Cancelar" para comandos `pending`/`sent` (chama `POST /commands/{id}/cancel` — verificar se ja existe; se nao, criar).
- [ ] React Query `refetchInterval` 5s para lista de comandos do dispositivo aberto.
- [ ] Aceitar `expires_in_seconds` opcional em `enviarComando`.

## Documentacao

- [ ] Criar `docs/PROVISIONAMENTO_ANDROID.md` com:
  - [ ] Passo a passo `adb shell dpm set-device-owner`.
  - [ ] Passo a passo provisionamento via QR code.
  - [ ] Troubleshooting comum (conta Google bloqueia, factory reset necessario).
- [ ] Atualizar `frontend/electron/README.md` (se nao existir, criar) com instrucoes de:
  - [ ] Permissoes para shutdown em Linux (`sudoers`).
  - [ ] Permissoes para shutdown em Windows (executar como Administrador).

## Testes

- [ ] Teste backend: `expire_stale_commands` marca comandos antigos como `EXPIRED`.
- [ ] Teste backend: `/commands/pending` exclui expirados.
- [ ] Teste backend: criar comando destrutivo sem `requested_by` retorna 400.
- [ ] Teste backend: criar comando com `expires_in_seconds=30` retorna 422 (fora do range).
- [ ] Teste player E2E (manual): comando `restart_app` em Electron Linux reinicia o processo.
- [ ] Teste player E2E (manual): comando `shutdown_device` em Windows desliga a maquina.
- [ ] Teste player E2E (manual): comando `restart_device` em APK Android Device Owner reinicia o tablet.
- [ ] Teste player E2E (manual): comando `shutdown_device` em web puro retorna `failed` com `error_code=BROWSER_ENVIRONMENT`.
- [ ] Teste UI: badge "Nao suportado" aparece para `failed` com `platform_unsupported=true`.

## Rollout

- [ ] Deploy backend (migration + Celery task) em ambiente de staging.
- [ ] Build novo APK com plugin nativo.
- [ ] Build novo Electron com preload corrigido.
- [ ] Atualizar instalacoes Electron existentes (auto-update se houver).
- [ ] Validar com cliente que comando shutdown agora funciona em ao menos 1 dispositivo cada de cada plataforma.

## Pos-rollout

- [ ] Monitorar taxa de comandos `failed` com `platform_unsupported` para entender mix de plataformas.
- [ ] Decidir se vale implementar MDM Android (SPEC futura) baseado em volume de TVs Android nao-Device-Owner.
