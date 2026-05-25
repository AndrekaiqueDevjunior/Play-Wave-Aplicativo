# Checklist Tecnico de Implementacao — Player Etapa 2

Data: 2026-05-22
Escopo: SPECs 003 a 006 (correcao de bugs reclamados pelo cliente).

Este checklist agrega tarefas das 4 SPECs em ordem de execucao recomendada, com referencias a arquivo:linha quando aplicavel. Use junto com os `tasks.md` de cada SPEC.

---

## Ordem recomendada de execucao

| Sprint | SPEC | Justificativa |
|---|---|---|
| 1 (3-5d) | SPEC 003 — Comandos Nativos | Bug visivel e critico. Cliente nao consegue desligar TVs. |
| 1 (3d) | SPEC 004 — Pareamento Revocacao | Risco de seguranca real. Player antigo continua sincronizando. |
| 2 (3-4d) | SPEC 005 — Conflito Audio | UX quebrada. Audio misturado. |
| 2 (2-3d) | SPEC 006 — OSD Musica | Feature nova solicitada. Baixo risco. |

Total estimado: **8-15 dias uteis** em sequencia. Sprints 1 e 2 podem rodar parcialmente paralelos (backend de SPEC 005 enquanto frontend de SPEC 003 termina).

---

## SPEC 003 — Player Comandos Nativos

Detalhamento completo: [`docs/specs/003-player-comandos-nativos/`](specs/003-player-comandos-nativos/).

### Pre-requisitos

- [ ] **Decisao:** Aceitar `lockNow()` como fallback de shutdown em Android (sem firmware custom)?
- [ ] **Decisao:** Configurar `sudoers` em Linux para permitir `shutdown` sem senha?
- [ ] Validar acesso ao APK Play Console para deploy do plugin nativo.

### Backend (1d)

- [ ] Migration `2026XXXX_command_defaults_and_index.py`:
  - [ ] Coluna `is_destructive` em `device_commands`.
  - [ ] Indice composto `ix_device_commands_device_status_expires`.
- [ ] `crud_device_command.create` seta `expires_at = now + 600s` e `is_destructive` para destrutivos.
- [ ] Task Celery `expire_stale_commands` (beat 60s).
- [ ] Endpoint `POST /devices/{id}/command` valida `requested_by` para destrutivos.
- [ ] Publicar SSE `command:new` ao criar comando.
- [ ] Aceitar `expires_in_seconds` (60-3600) em `DeviceCommandCreate`.
- [ ] Padronizar `error_code` no `result` do ACK.

### Electron (1-2d)

- [ ] Reescrever [`frontend/electron/preload.js`](../frontend/electron/preload.js) usando `contextBridge.exposeInMainWorld("__ELECTRON__", { player: {...} })`.
- [ ] **REMOVER** linha em [`frontend/electron/main.js`](../frontend/electron/main.js) que injeta `window.__ELECTRON__ = true` boolean no `dom-ready`.
- [ ] Adicionar handlers `ipcMain.handle("player:restart_app"|"restart_device"|"shutdown_device"|"take_screenshot")` em `main.js`.
- [ ] Helper `runShell(cmd)` com `child_process.exec`.
- [ ] Manter `ipcMain.on("player:restart")` como alias legado.

### Android (2-3d)

- [ ] Criar [`frontend/android/app/src/main/java/com/playwave/player/PlayWaveDeviceAdminReceiver.java`](../frontend/android/app/src/main/java/com/playwave/player/).
- [ ] Criar `frontend/android/app/src/main/res/xml/device_admin_policies.xml`.
- [ ] Criar `PlayWaveNativePlugin.java` com 4 metodos (`restartApp`, `restartDevice`, `shutdownDevice`, `takeScreenshot`).
- [ ] Atualizar [`MainActivity.java`](../frontend/android/app/src/main/java/com/playwave/player/MainActivity.java) com `registerPlugin(PlayWaveNativePlugin.class)`.
- [ ] Atualizar [`AndroidManifest.xml`](../frontend/android/app/src/main/AndroidManifest.xml) com permissao `REBOOT` + `<receiver>` do Device Admin.
- [ ] Documentar provisionamento Device Owner em `docs/PROVISIONAMENTO_ANDROID.md`.
- [ ] Rebuild APK via `npm run build:apk` (verificar `.env.production`).

### Player JS (0.5d)

- [ ] Atualizar [`frontend/src/player-core/platform.js`](../frontend/src/player-core/platform.js) — wrapper Capacitor que expoe `window.PlayWaveNative`.
- [ ] Atualizar [`frontend/src/player-core/commands.js`](../frontend/src/player-core/commands.js) — `platformUnsupported` aceitar `reason` e setar `err.code`.
- [ ] Atualizar [`frontend/src/pages/Player.jsx`](../frontend/src/pages/Player.jsx) (linhas ~476-516):
  - [ ] Pre-ACK para destrutivos antes do executeCommand.
  - [ ] Escutar SSE `command:new` para disparar polling imediato.

### Frontend gerenciador (1d)

- [ ] Criar `frontend/src/utils/deviceCommands.js` com `COMMAND_LABELS`, `STATUS_LABELS`, `statusFor`.
- [ ] Criar `frontend/src/components/devices/CommandHistoryTimeline.jsx`.
- [ ] Criar `frontend/src/components/devices/DestructiveCommandConfirmDialog.jsx`.
- [ ] Atualizar [`DispositivoDetalhe.jsx`](../frontend/src/pages/DispositivoDetalhe.jsx):
  - [ ] Reorganizar botoes em 3 grupos (operacional, reset, energia).
  - [ ] Adicionar tooltips e modal destrutivo.
  - [ ] Substituir lista atual de comandos por `CommandHistoryTimeline`.
  - [ ] React Query `refetchInterval: 5000` para historico.

### Validacao

- [ ] Electron Linux: `shutdown_device` desliga maquina (com sudoers).
- [ ] Electron Windows: `shutdown_device` desliga maquina (com admin rights).
- [ ] APK Device Owner: `restart_device` reinicia TV box.
- [ ] APK sem Device Owner: retorna `failed` com `DEVICE_OWNER_REQUIRED`.
- [ ] Web puro: retorna `failed` com `BROWSER_ENVIRONMENT`.
- [ ] Job Celery marca comandos expirados.
- [ ] Cliente confirma: comando "Desligar Dispositivo" funciona.

---

## SPEC 004 — Pareamento e Revogacao

Detalhamento completo: [`docs/specs/004-pareamento-revocacao/`](specs/004-pareamento-revocacao/).

### Backend (1.5d)

- [ ] Migration `2026XXXX_device_pairing_events.py` (auditoria).
- [ ] Helper `auth_error(error_code, detail, status, **extra)`.
- [ ] Atualizar [`get_device_by_token`](../backend/api/v1/devices.py) (linhas 83-103):
  - [ ] Ler header `X-Device-Token-Version`.
  - [ ] Comparar com `device.token_version`.
  - [ ] Retornar 401 com `error_code=TOKEN_VERSION_MISMATCH` quando difere.
  - [ ] Compat-period: aceitar ausente com warning.
- [ ] Substituir HTTPException(401) por `auth_error` em todas as rotas player.
- [ ] Endpoint `POST /devices/{id}/force-repair`.
- [ ] Endpoint `GET /devices/{id}/pairing-events`.
- [ ] Registrar evento em todas as transicoes de pareamento (regenerate, force_repair, revoke, paired, blocked).
- [ ] Publicar SSE `pairing:revoked`.
- [ ] `GET /by-code/{code}/status` retorna `token_version` e `pairing_version` quando paired.

### Player (1d)

- [ ] Atualizar [`frontend/src/player-core/storage.js`](../frontend/src/player-core/storage.js):
  - [ ] Adicionar key `pw_player_token_version`.
  - [ ] Metodos `tokenVersion()`, `setTokenVersion(v)`.
- [ ] Criar `frontend/src/player-core/repair.js`:
  - [ ] `forceRepair(reason)` com anti-loop.
  - [ ] `onForceRepair(callback)` registry.
- [ ] Atualizar [`frontend/src/api/http.js`](../frontend/src/api/http.js):
  - [ ] Request interceptor injeta `X-Device-Token` + `X-Device-Token-Version`.
  - [ ] Response interceptor captura 401/403 com error_code em whitelist → `forceRepair`.
- [ ] Atualizar `verificarStatusPareamento` em [`dispositivos.js`](../frontend/src/api/dispositivos.js) para persistir `token_version`.
- [ ] Atualizar [`Player.jsx`](../frontend/src/pages/Player.jsx):
  - [ ] Registrar `onForceRepair` callback que reseta para fase pairing.
  - [ ] Exibir mensagem amigavel `REPAIR_MESSAGES[reason]` na tela de pareamento.
  - [ ] SSE listener para `pairing:revoked`.
  - [ ] Watchdog skip se `phase === "pairing"`.

### Frontend gerenciador (1d)

- [ ] `dispositivos.js`: `buscarSessoesAtivas`, `forcarReparamento`, `listarEventosPareamento`.
- [ ] `RegenerateCodeDialog.jsx` com lista de sessoes ativas + motivo + confirmacao forte.
- [ ] `ForceRepairDialog.jsx` similar mas mantem codigo.
- [ ] `PairingEventTimeline.jsx`.
- [ ] [`DispositivoDetalhe.jsx`](../frontend/src/pages/DispositivoDetalhe.jsx) — reorganizar card de pareamento, adicionar acao "Forcar reparamento", adicionar secao "Historico de pareamento".

### Validacao

- [ ] Regenerar codigo via gerenciador expulsa player em < 5s (SSE) ou < 10s (polling).
- [ ] Force-repair mantem codigo, player precisa reparear com mesmo codigo.
- [ ] Player com token version errado recebe 401 e dispara forceRepair.
- [ ] Tela de pareamento mostra banner amarelo com motivo.
- [ ] PairingEventTimeline lista historico com filtros.

---

## SPEC 005 — Conflito de Audio

Detalhamento completo: [`docs/specs/005-conflito-audio-midia/`](specs/005-conflito-audio-midia/).

### Pre-requisitos

- [ ] Validar `ffprobe` disponivel no Dockerfile do backend.

### Backend (2d)

- [ ] Migration `2026XXXX_audio_policy.py`:
  - [ ] Type `audio_policy_enum`.
  - [ ] Colunas em `tenants`, `devices`, `campaigns`, `media`.
  - [ ] `has_audio` em `media`.
  - [ ] Backfill de `audio_policy` baseado em `video_muted` legado.
- [ ] Adicionar enum `AudioPolicy` em [`backend/core/models.py`](../backend/core/models.py).
- [ ] Criar `backend/services/audio_policy_resolver.py` com `resolve_effective_audio_policy`.
- [ ] Adicionar `detect_audio_streams(file_path)` em pipeline de upload.
- [ ] Endpoint `POST /media/{id}/recompute-audio-detection`.
- [ ] Estender `GET /devices/{id}/playlist` com `audio_policy_effective` por midia + `audio_policy_default` na campaign.
- [ ] Task Celery `backfill_has_audio` para midias antigas.
- [ ] Cache busting: mudancas em qualquer nivel invalidam campanhas afetadas.

### Player (1d)

- [ ] Criar `frontend/src/utils/audioPolicy.js` (compartilhado com admin).
- [ ] Criar `frontend/src/hooks/useAudioConflictResolver.js`.
- [ ] Atualizar [`AudioPlayer.jsx`](../frontend/src/components/audio/AudioPlayer.jsx):
  - [ ] Prop `fadeMs` (default 200).
  - [ ] Helper `doFade(audio, target, durationMs, onComplete)`.
- [ ] Atualizar [`Player.jsx`](../frontend/src/pages/Player.jsx) (linha 600-606):
  - [ ] Usar `useAudioConflictResolver` para decidir `videoMuted` e `audioEnabled`.
  - [ ] Manter fallback compat com `campaign.video_muted`.
  - [ ] Log `[player] audio resolver` para debug.

### Frontend admin (1.5d)

- [ ] Criar `frontend/src/components/shared/AudioPolicySelector.jsx`.
- [ ] [`CampaignFormModal.jsx`](../frontend/src/components/campaigns/CampaignFormModal.jsx) — secao Audio + colapsar `video_muted` legado.
- [ ] [`MediaFormModal.jsx`](../frontend/src/components/media/MediaFormModal.jsx) — selector + indicador `has_audio` + botao Recalcular.
- [ ] `DeviceEditDrawer.jsx` ou `DispositivoDetalhe.jsx` — card Audio.
- [ ] [`ConfigEmpresa.jsx`](../frontend/src/pages/ConfigEmpresa.jsx) — secao Configuracao de Audio + slider fade.
- [ ] Tag de politica efetiva no `CampanhaPreview.jsx`.

### Validacao

- [ ] Video com audio + radio + policy=auto: video toca com som, radio pausa.
- [ ] Imagem + radio + policy=auto: radio toca, imagem sem audio.
- [ ] Override por midia funciona.
- [ ] Override por device funciona.
- [ ] Mudanca via gerenciador reflete na proxima troca de midia.
- [ ] Cliente confirma: audio nao mais misturado.

---

## SPEC 006 — OSD Musica Atual

Detalhamento completo: [`docs/specs/006-osd-musica-atual/`](specs/006-osd-musica-atual/).

### Backend (1d)

- [ ] Migration `2026XXXX_osd_config.py`:
  - [ ] Types `osd_position_enum`, `osd_font_size_enum`.
  - [ ] Colunas `osd_*` em `tenants` (NOT NULL com defaults).
  - [ ] Colunas `osd_*` em `devices` (nullable).
  - [ ] Colunas `current_audio_track_*` em `devices`.
- [ ] Atualizar models `Tenant` e `Device`.
- [ ] Criar `backend/services/osd_config_resolver.py`.
- [ ] Estender `GET /devices/{id}/playlist` com bloco `osd_config` resolvido.
- [ ] Heartbeat aceita `current_audio_track_*`.
- [ ] Endpoint `PATCH /devices/{id}/osd-config`.
- [ ] Endpoint `PATCH /tenants/{id}/osd-config`.
- [ ] Estender `GET /devices/{id}` (admin) com `osd_config_local` + `osd_config_effective` + `current_audio_track_*`.

### Player (1d)

- [ ] Atualizar [`AudioPlayer.jsx`](../frontend/src/components/audio/AudioPlayer.jsx) — prop `onTrackChange` com debounce 500ms, nao re-reportar mesma faixa, reportar null quando disabled.
- [ ] Atualizar [`PlayerOSD.jsx`](../frontend/src/components/player/PlayerOSD.jsx) — slot novo configuravel.
- [ ] Atualizar [`Player.jsx`](../frontend/src/pages/Player.jsx):
  - [ ] State `currentAudioTrack`.
  - [ ] Passar callback ao AudioPlayer.
  - [ ] Ler `osd_config` da playlist e passar ao PlayerOSD.
  - [ ] Estender heartbeat com `current_audio_track_*`.

### Frontend admin (1.5d)

- [ ] Criar `frontend/src/components/shared/OSDConfigForm.jsx`.
- [ ] Criar `frontend/src/components/shared/OSDConfigPreview.jsx`.
- [ ] [`ConfigEmpresa.jsx`](../frontend/src/pages/ConfigEmpresa.jsx) — secao "Overlay de musica".
- [ ] [`DispositivoDetalhe.jsx`](../frontend/src/pages/DispositivoDetalhe.jsx):
  - [ ] Card "Overlay OSD" com form (allowNull) + preview.
  - [ ] Card "Estado atual" exibe "Tocando agora" com elapsed.
  - [ ] React Query refetch a cada 10s.
- [ ] APIs: `atualizarOSDConfigDispositivo`, `atualizarOSDConfigEmpresa`.

### Validacao

- [ ] Tenant config + sem device override: TV mostra overlay no canto configurado.
- [ ] Device override funciona.
- [ ] `duration_seconds=0` mantem overlay sempre visivel.
- [ ] Nome longo trunca com ellipsis.
- [ ] Painel admin mostra "Tocando agora: X (ha Ns)".
- [ ] Mudanca via gerenciador reflete em < 30s.

---

## Migrations consolidadas (ordem de aplicacao)

1. `2026XXXX_command_defaults_and_index.py` (SPEC 003).
2. `2026XXXX_device_pairing_events.py` (SPEC 004).
3. `2026XXXX_audio_policy.py` (SPEC 005) — inclui backfill.
4. `2026XXXX_osd_config.py` (SPEC 006).

Sao independentes — podem ser aplicadas em qualquer ordem desde que mantida sequencia alembic.

---

## Endpoints consolidados (novos ou estendidos)

### Novos

- `POST /media/{id}/recompute-audio-detection` (SPEC 005).
- `PATCH /tenants/{id}/audio-config` (SPEC 005).
- `PATCH /tenants/{id}/osd-config` (SPEC 006).
- `PATCH /devices/{id}/osd-config` (SPEC 006).
- `POST /devices/{id}/force-repair` (SPEC 004).
- `GET /devices/{id}/pairing-events` (SPEC 004).

### Estendidos

- `GET /devices/{id}/playlist` ganha `osd_config`, `audio_policy_effective` por midia, `audio_policy_default`/`audio_fade_ms` na campaign.
- `POST /devices/{id}/heartbeat` ganha `current_audio_track_*`.
- `POST /devices/{id}/command` valida `requested_by` para destrutivos e aceita `expires_in_seconds`.
- `GET /devices/by-code/{code}/status` retorna `token_version` e `pairing_version`.
- `POST /devices/{id}/pairing-code/regenerate` retorna mais info + audita.
- `GET /devices/{id}` (admin) ganha `osd_config_local/effective`, `current_audio_track_*`.

### Headers novos

- `X-Device-Token-Version` em todas as rotas autenticadas por device (SPEC 004).

---

## SSE consolidado

Canais existentes (`pw:device:{device_id}:events`) ganham eventos novos:

- `command:new` (SPEC 003) — notifica player de comando recem-criado.
- `pairing:revoked` (SPEC 004) — notifica player que pareamento foi revogado.

Eventos existentes (`playlist_invalidated`, `snapshot`) sao reusados.

---

## Componentes novos no frontend

| Arquivo | SPEC |
|---|---|
| `frontend/src/utils/deviceCommands.js` | 003 |
| `frontend/src/components/devices/CommandHistoryTimeline.jsx` | 003 |
| `frontend/src/components/devices/DestructiveCommandConfirmDialog.jsx` | 003 |
| `frontend/src/player-core/repair.js` | 004 |
| `frontend/src/components/devices/RegenerateCodeDialog.jsx` | 004 |
| `frontend/src/components/devices/ForceRepairDialog.jsx` | 004 |
| `frontend/src/components/devices/PairingEventTimeline.jsx` | 004 |
| `frontend/src/utils/audioPolicy.js` | 005 |
| `frontend/src/hooks/useAudioConflictResolver.js` | 005 |
| `frontend/src/components/shared/AudioPolicySelector.jsx` | 005 |
| `frontend/src/components/shared/OSDConfigForm.jsx` | 006 |
| `frontend/src/components/shared/OSDConfigPreview.jsx` | 006 |

---

## Arquivos chave alterados

| Arquivo | SPECs que tocam |
|---|---|
| `backend/api/v1/devices.py` | 003, 004, 005, 006 |
| `backend/core/models.py` | 003, 004, 005, 006 |
| `backend/core/schemas_completos.py` | 003, 004, 005, 006 |
| `frontend/src/pages/Player.jsx` | 003, 004, 005, 006 |
| `frontend/src/pages/DispositivoDetalhe.jsx` | 003, 004, 005, 006 |
| `frontend/src/pages/ConfigEmpresa.jsx` | 005, 006 |
| `frontend/src/api/http.js` | 004 |
| `frontend/src/api/dispositivos.js` | 003, 004, 006 |
| `frontend/src/player-core/commands.js` | 003 |
| `frontend/src/player-core/platform.js` | 003 |
| `frontend/src/player-core/storage.js` | 004 |
| `frontend/src/components/audio/AudioPlayer.jsx` | 005, 006 |
| `frontend/src/components/player/PlayerOSD.jsx` | 006 |
| `frontend/electron/main.js` | 003 |
| `frontend/electron/preload.js` | 003 |
| `frontend/android/app/src/main/java/com/playwave/player/MainActivity.java` | 003 |
| `frontend/android/app/src/main/AndroidManifest.xml` | 003 |

Risco de conflito merge: medio. Recomendado fazer SPECs sequencialmente ou em branches separadas com rebase frequente.

---

## Criterios de pronto da Etapa 2 (validacao com cliente)

- [ ] Comando "Desligar Dispositivo" funciona em Electron Windows.
- [ ] Comando "Desligar Dispositivo" funciona em Electron Linux.
- [ ] Comando "Reiniciar Dispositivo" funciona em APK Android Device Owner.
- [ ] Comando em web puro retorna "nao suportado" claro.
- [ ] Regenerar codigo de pareamento expulsa player antigo em < 10s.
- [ ] Force-repair disponivel como acao separada (mantem codigo).
- [ ] Historico de pareamento visivel no gerenciador.
- [ ] Video com audio + radio: politica `auto` pausa radio durante video.
- [ ] Operador escolhe politica em campanha/midia/device/tenant.
- [ ] Mudanca de politica reflete na proxima troca de midia.
- [ ] Nome da musica aparece no canto da TV.
- [ ] Operador configura posicao/duracao/opacidade do overlay.
- [ ] Painel admin mostra musica atual de cada player.

---

## Pos-Etapa 2

Apos validar SPECs 003-006 com o cliente:

- Etapa 3: Radio Indoor v2 (upload multiplo, pastas, schedule, spots).
- Etapa 4: SPECs futuras (Central de Entrega, Auditoria, Cache por midia).

Cada SPEC nova segue o template em `docs/specs/_TEMPLATE/`.
