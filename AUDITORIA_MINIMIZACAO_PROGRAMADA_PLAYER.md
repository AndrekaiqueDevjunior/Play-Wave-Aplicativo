# Auditoria Tecnica - Minimizacao Programada do Player

Data da auditoria: 2026-06-01

Escopo analisado: backend, frontend/player React, Electron, Capacitor Android, camada de comandos, documentacao de compatibilidade por sistema operacional, migrations e telas administrativas.

## Conclusao Executiva

O PlayWave ainda nao possui a feature de minimizar o Player remotamente, restaurar automaticamente e expor a area de trabalho por uma janela de tempo configuravel.

Existe, porem, uma infraestrutura forte e reaproveitavel para comandos remotos: backend com fila persistente em `device_commands`, endpoints de envio/consulta/ACK, SSE para notificacao em tempo real e motor local de comandos no Player. No Electron, o app ja usa `BrowserWindow` em fullscreen/kiosk e ja tem IPC para fullscreen/restart/shutdown/screenshot. Isso torna a implementacao em Windows/Linux via Electron de esforco baixo a medio.

O maior gap esta em configuracoes persistentes da feature, suporte por grupo/global, UI administrativa especifica e handlers nativos de `minimize`, `restore` e ciclo temporizado no Player.

## Respostas Objetivas

1. O PlayWave ja possui suporte para minimizar o player remotamente?

Nao. Nao ha comando `minimize`, `show_desktop`, `window_minimize` ou equivalente em `VALID_COMMANDS`, `COMMAND_HANDLERS`, `preload.js` ou `main.js`.

2. O PlayWave ja possui suporte para restaurar o player remotamente?

Nao. Ha apenas `fullscreenToggle` via Electron IPC, mas nao ha comando remoto nem handler de `restore`, `show`, `focus` ou `setAlwaysOnTop` para restaurar a janela.

3. Existe infraestrutura de comandos capaz de suportar essa feature?

Sim. A infraestrutura de comandos esta praticamente pronta para carregar novos command types. Ela ja suporta criacao admin, fila, polling, SSE, lifecycle `pending -> sent -> received -> executing -> completed/failed`, ACK com resultado JSON e historico.

4. Existe algum agente local que ja possa executar esse comportamento?

Parcialmente. O Electron funciona como agente local do Player em Windows/Linux e ja controla a janela. Nao ha Windows Service, Python Agent, tray app ou watchdog externo com controle de janela. No Android ha plugin Capacitor, mas ele nao implementa minimizar/restaurar Activity.

5. Percentual estimado ja implementado:

- Backend comandos remotos: 85%
- Backend configuracoes da feature: 15%
- Player web/React command engine: 70%
- Electron Windows/Linux window-control base: 60%
- Android/Capacitor para essa feature: 20%
- UI administrativa: 35%
- Implementacao total existente: 55%

## Evidencias Principais

### Backend - Endpoints e comandos

Arquivo: `backend/api/v1/devices.py`

- `VALID_COMMANDS` existe em `backend/api/v1/devices.py:1640` e contem:
  `sync`, `refresh_playlist`, `clear_cache`, `reload_player`, `restart_app`, `restart`, `restart_device`, `shutdown_device`, `screenshot`, `take_screenshot`, `set_volume`, `mute`, `unmute`.
- Envio de comando admin: `POST /devices/{device_id}/command` em `backend/api/v1/devices.py:1682`.
- Cancelamento: `POST /devices/{device_id}/commands/{command_id}/cancel` em `backend/api/v1/devices.py:1737`.
- Historico: `GET /devices/{device_id}/commands` em `backend/api/v1/devices.py:1769`.
- Pendentes para o player: `GET /devices/{device_id}/commands/pending` em `backend/api/v1/devices.py:1786`.
- SSE: `GET /devices/{device_id}/playlist/updates` em `backend/api/v1/devices.py:1810`.
- ACK: `POST /devices/{device_id}/commands/{command_id}/ack` em `backend/api/v1/devices.py:1980`.
- Lifecycle recebido/iniciado: `POST /received` em `backend/api/v1/devices.py:2011` e `POST /started` em `backend/api/v1/devices.py:2027`.

O endpoint de criacao publica `command:new` via Redis/SSE para acelerar a entrega, em vez de depender apenas do polling de 10 segundos.

Arquivo: `backend/services/event_bus.py`

- Canal por dispositivo: `pw:device:{device_id}:events`.
- `publish_device_event(...)` publica eventos diretos para um device.
- `publish_campaign_event(...)` faz fanout para dispositivos alvo de campanha.

### Backend - Banco de dados

Arquivo: `backend/core/models.py`

Tabela `devices`, classe `Device`, comeca em `backend/core/models.py:166`.

Campos relevantes encontrados:

- `tenant_id`
- `name`
- `pairing_code`
- `pairing_version`
- `token_version`
- `requires_repairing`
- `device_type`
- `location`
- `group`
- `status`
- `is_active`
- `is_blocked`
- `device_token`
- `paired_at`
- `last_connection`
- `last_seen_at`
- `config_version`
- `current_campaign`
- `current_campaign_id`
- `audio_playlist_id`
- `audio_volume`
- `audio_policy_default`
- `osd_*`
- `ip_address`
- `player_version`
- `os`
- `storage_used`

Nao foram encontrados campos como `fullscreen`, `kiosk_mode`, `minimize_interval`, `desktop_mode`, `restore_timeout` ou `player_behavior`.

Tabela `campaigns`, classe `Campaign`, comeca em `backend/core/models.py:285`.

Campos relevantes:

- `device_ids`
- `media_ids`
- `media_order`
- `schedule_all_day`
- `schedule_days`
- `schedule_start_time`
- `schedule_end_time`
- `loop_count`
- `target_groups`
- `config_version`

Esses campos ajudam a direcionar conteudo por dispositivo/grupo, mas nao configuram comportamento de janela do Player.

Tabela `device_commands`, classe `DeviceCommand`, comeca em `backend/core/models.py:962`.

Estrutura:

- `id`
- `device_id`
- `tenant_id`
- `command_type`
- `payload`
- `status`
- `requested_by`
- `requested_at`
- `sent_at`
- `received_at`
- `started_at`
- `executed_at`
- `expires_at`
- `result`
- `error_message`
- `is_destructive`

Migrations:

- `backend/alembic/versions/002_add_device_commands.py` cria `device_commands`.
- `backend/alembic/versions/20260521_0915_device_command_lifecycle.py:26-29` adiciona `received_at`, `started_at`, `expires_at`, `result`.
- `backend/alembic/versions/20260522_1000_command_defaults_and_index.py:33-60` adiciona `is_destructive` e indice composto para comandos pendentes.

### Sistema de comandos

Arquivo: `backend/crud/entidades/crud_device_command.py`

Funcionalidades encontradas:

- `create(...)`: cria comando com expiracao e status `PENDING`.
- `get_pending(...)`: retorna comandos validos, expira comandos antigos e reabilita `SENT` travado.
- `mark_many_sent(...)`: marca lote como `SENT`.
- `mark_received(...)`: marca como `RECEIVED`.
- `mark_executing(...)`: marca como `EXECUTING`.
- `ack(...)`: fecha como `COMPLETED` ou `FAILED`.
- `cancel(...)`: cancela comando pendente/enviado.

Comandos existentes:

- `sync`
- `refresh_playlist`
- `clear_cache`
- `reload_player`
- `restart`
- `restart_app`
- `restart_device`
- `shutdown_device`
- `screenshot`
- `take_screenshot`
- `set_volume`
- `mute`
- `unmute`

Comandos ausentes para a feature:

- `minimize_player`
- `restore_player`
- `show_desktop`
- `set_fullscreen`
- `set_kiosk`
- `configure_desktop_exposure`
- `start_desktop_exposure_cycle`
- `stop_desktop_exposure_cycle`

## Player / Frontend

### Player React

Arquivo: `frontend/src/pages/Player.jsx`

O Player tem polling de comandos e SSE:

- `POLL_COMMANDS_INTERVAL = 10_000` em `frontend/src/pages/Player.jsx:37`.
- Importa `buscarComandosPendentes`, `marcarComandoRecebido`, `marcarComandoIniciado`, `ackComando` e `abrirStreamPlaylistUpdates`.
- Executa comandos pendentes no bloco iniciado em `frontend/src/pages/Player.jsx:609`.
- Em evento SSE `command:new`, chama `pollCommands()` sem aguardar o proximo tick, em `frontend/src/pages/Player.jsx:770`.

Isso atende bem a entrega remota do comando. A lacuna e o handler de janela.

### Motor de comandos local

Arquivo: `frontend/src/player-core/commands.js`

`COMMAND_HANDLERS` implementa:

- `sync`
- `refresh_playlist`
- `reload_player`
- `clear_cache`
- `restart`
- `restart_app`
- `restart_device`
- `shutdown_device`
- `screenshot`
- `take_screenshot`
- `set_volume`
- `mute`
- `unmute`

O bridge nativo usado pelos comandos e:

```js
const nativeBridge = window.PlayWaveNative || window.AndroidPlayer || window.__ELECTRON__?.player;
```

Nao ha handler de minimizar/restaurar. Em navegador puro, mesmo que o handler existisse, o browser nao pode minimizar a janela por seguranca; no maximo pode usar Fullscreen API em resposta a gesto do usuario.

### Plataforma/browser

Arquivo: `frontend/src/player-core/platform.js`

Encontrado:

- Deteccao de Electron, Capacitor, Tizen, webOS, Android TV e browser.
- `supportsFullscreen`.
- `requestFullscreen()`.
- `acquireWakeLock()`.

Nao encontrado:

- API para minimizar janela.
- API para restaurar janela.
- API para mostrar desktop.
- politica temporizada de exposicao da area de trabalho.

## Electron

Arquivo: `frontend/electron/main.js`

Evidencias:

- Importa `BrowserWindow` em `frontend/electron/main.js:9`.
- Cria `BrowserWindow` em `frontend/electron/main.js:84`.
- Configura `fullscreen: KIOSK` em `frontend/electron/main.js:87`.
- Configura `kiosk: KIOSK` em `frontend/electron/main.js:88`.
- Usa `mainWindow.show()` em `frontend/electron/main.js:113`.
- Implementa `player:fullscreen-toggle` e chama `mainWindow.setFullScreen(...)` em `frontend/electron/main.js:215-217`.
- Implementa IPC para `restart_app`, `restart_device`, `shutdown_device`, `take_screenshot`.

Nao encontrado:

- `mainWindow.minimize()`
- `mainWindow.restore()`
- `mainWindow.hide()`
- `mainWindow.focus()`
- comando de `show desktop`
- agendamento local para minimizar por X segundos e restaurar depois.

Conclusao Electron: e o alvo mais simples para implementar a feature. A base existe, mas falta expor IPC e comandos remotos.

Arquivo: `frontend/electron/preload.js`

Bridge atual:

- `restartApp`
- `restartDevice`
- `shutdownDevice`
- `takeScreenshot`
- `fullscreenToggle`

Nao ha `minimize`, `restore`, `showDesktop` ou `configureDesktopExposure`.

## Capacitor / Android

Arquivo: `frontend/android/app/src/main/java/com/playwave/player/PlayWaveNativePlugin.java`

Plugin nativo existente:

- `restartApp()`
- `restartDevice()`
- `shutdownDevice()`
- `takeScreenshot()`

Nao ha API de minimizar/restaurar. Em Android, o equivalente a "mostrar area de trabalho" pode envolver sair da Activity, mover task para background ou abrir launcher, mas restaurar automaticamente e manter kiosk depende de Device Owner/Lock Task Mode e tem limitacoes de seguranca/plataforma.

## Browser / Smart TV

O Player pode rodar diretamente em browser (`/player`) e em Smart TVs. Para browser puro:

- Nao ha capacidade confiavel de minimizar janela.
- Nao ha permissao padrao para trazer janela para frente automaticamente.
- Fullscreen API e limitada e frequentemente exige gesto do usuario.

Portanto, browser/Smart TV nao e alvo viavel para "minimizar e mostrar desktop" sem app nativo/agent.

## Servicos e agentes locais

Encontrado:

- Electron desktop para Windows/Linux.
- Capacitor APK para Android.
- `backend/compatibilidade_SO/linux/playwave-player.service` com systemd, `Restart=always` e `PLAYER_KIOSK=true`.
- Documentacao de Windows com executavel fullscreen/kiosk.

Nao encontrado:

- Windows Service dedicado.
- Python Agent.
- Tray application.
- Watchdog externo com controle de janelas.
- Uso de `xdotool` ou `wmctrl`.
- Integracao nativa Windows com PowerShell/Win32 para minimizar/restaurar janelas.

## Comunicacao com dispositivos

Fluxo atual encontrado:

Backend admin cria comando:

`POST /devices/{id}/command`

Backend persiste:

`device_commands`

Backend notifica:

Redis Pub/Sub -> SSE `/devices/{id}/playlist/updates` -> evento `command:new`

Player busca:

`GET /devices/{id}/commands/pending`

Player executa:

`frontend/src/player-core/commands.js`

Player confirma:

`POST /devices/{id}/commands/{command_id}/received`

`POST /devices/{id}/commands/{command_id}/started`

`POST /devices/{id}/commands/{command_id}/ack`

Fallback:

polling a cada 10 segundos.

## Configuracoes administrativas

Encontrado:

- Tela de detalhe do dispositivo com grupos de comandos em `frontend/src/pages/DispositivoDetalhe.jsx`.
- Catalogo visual de comandos em `frontend/src/utils/deviceCommands.js`.
- Configuracao OSD por tenant/device em backend e frontend.
- Configuracao de audio por tenant/device.

Nao encontrado:

- Tela de "comportamento do player".
- Configuracao `minimize_interval_seconds`.
- Configuracao `desktop_visible_seconds`.
- Toggle `desktop_exposure_enabled`.
- Aplicacao por grupo/global para essa feature.
- Historico especifico de alteracoes dessa configuracao.

## Gap Analysis

### O que ja existe

- Fila persistente de comandos por dispositivo.
- Endpoint admin para enfileirar comandos.
- Endpoint do player para buscar comandos pendentes.
- ACK completo com resultado estruturado.
- SSE para reduzir latencia.
- Player executa comandos remotos.
- Electron ja controla fullscreen/kiosk.
- Electron ja tem IPC seguro via preload.
- Capacitor ja tem plugin nativo para alguns comandos.
- UI administrativa ja lista e envia comandos operacionais/power.

### O que pode ser reaproveitado

- `backend/api/v1/devices.py`: endpoints de comandos.
- `backend/core/models.py`: `DeviceCommand`.
- `backend/crud/entidades/crud_device_command.py`: lifecycle da fila.
- `backend/services/event_bus.py`: evento `command:new`.
- `frontend/src/pages/Player.jsx`: polling/SSE/ACK.
- `frontend/src/player-core/commands.js`: registry de handlers.
- `frontend/electron/main.js`: `BrowserWindow` e IPC.
- `frontend/electron/preload.js`: bridge para renderer.
- `frontend/src/utils/deviceCommands.js`: labels/grupos para UI.
- `frontend/src/pages/DispositivoDetalhe.jsx`: tela para acionar comandos.

### O que esta faltando

BAIXO ESFORCO:

- Adicionar command types no backend: `minimize_player`, `restore_player`, `show_desktop`.
- Adicionar labels e botoes na UI de dispositivo.
- Adicionar handlers em `frontend/src/player-core/commands.js`.
- Expor metodos no `frontend/electron/preload.js`.
- Implementar IPC Electron usando `mainWindow.minimize()`, `restore()`, `show()`, `focus()` e controle de fullscreen/kiosk.

MEDIO ESFORCO:

- Criar comando/configuracao de ciclo temporizado:
  `desktop_exposure_enabled`, `minimize_interval_seconds`, `desktop_visible_seconds`.
- Persistir config por dispositivo e/ou tenant.
- Aplicar configuracao automaticamente no Player, nao apenas por comando manual.
- Adicionar validacao de conflito com kiosk/fullscreen/alwaysOnTop.
- Testar comportamento real em Windows e Linux.

ALTO ESFORCO:

- Suporte robusto para Android/Smart TV com kiosk e restauracao automatica.
- Criar agente externo para Windows/Linux quando Electron nao estiver controlando a janela.
- Implementar "show desktop" real por SO:
  Windows com Win32/PowerShell ou Electron/Node nativo;
  Linux com `xdotool`/`wmctrl`/compositor especifico.
- Governanca global/grupo com heranca e overrides.
- Telemetria detalhada da execucao do ciclo.

## Arquitetura recomendada para implementacao

### Comandos manuais

Adicionar comandos:

- `minimize_player`
- `restore_player`
- `show_desktop`
- `set_fullscreen`

No Electron:

- `minimize_player`: sair temporariamente de fullscreen/kiosk se necessario, desativar `alwaysOnTop`, chamar `mainWindow.minimize()`.
- `restore_player`: `mainWindow.restore()`, `mainWindow.show()`, `mainWindow.focus()`, reativar fullscreen/kiosk conforme config.
- `show_desktop`: equivalente a minimizar por um periodo, preferencialmente com `duration_seconds` no payload.

### Configuracao programada

Adicionar configuracao por device e tenant:

- `desktop_exposure_enabled: boolean`
- `desktop_exposure_interval_seconds: integer`
- `desktop_exposure_duration_seconds: integer`
- `desktop_exposure_restore_fullscreen: boolean`
- `desktop_exposure_platforms: json/array`

O Player deve carregar a configuracao no `/devices/{id}/playlist` ou endpoint especifico de settings. O ciclo deve rodar localmente para nao depender de roundtrip a cada intervalo.

### Compatibilidade

- Windows/Linux Electron: viavel.
- Browser puro: nao suportado, retornar `platform_unsupported`.
- Android: tratar como futuro/experimental.
- Smart TV web: nao suportado sem app nativo.



