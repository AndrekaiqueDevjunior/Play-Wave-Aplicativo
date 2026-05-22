# SPEC 003 — Plano de Testes

## Backend (pytest)

### Lifecycle e expiracao

- `test_create_command_sets_default_expires_at`: criar comando sem `expires_in_seconds` resulta em `expires_at` = `now + 600s`.
- `test_create_command_with_custom_expires_in_seconds`: aceita 60-3600, rejeita fora.
- `test_create_destructive_command_sets_is_destructive`: criar `shutdown_device` resulta em `is_destructive = True`.
- `test_create_destructive_command_requires_requested_by`: criar sem usuario autenticado retorna 401/403.
- `test_get_pending_excludes_expired`: comando com `expires_at` no passado nao aparece em `/commands/pending`.
- `test_get_pending_marks_as_sent`: apos retorno, comandos viram `SENT`.
- `test_expire_stale_commands_task`: chamar task atualiza comandos antigos para `EXPIRED`.
- `test_expire_stale_commands_only_affects_correct_statuses`: nao mexe em `COMPLETED`, `FAILED`, `CANCELLED`.

### ACK

- `test_ack_with_platform_unsupported_marks_failed`: ACK com `result.platform_unsupported=true` resulta em `status=FAILED`.
- `test_ack_with_error_code`: ACK preserva `result.error_code`.
- `test_ack_pre_execution_for_destructive`: ACK `ack_phase=pre_execution` aceito para destrutivos, marca `COMPLETED`.
- `test_ack_post_execution_override`: ACK com `ack_phase=post_execution_override` apos pre_execution falhada sobrescreve para `FAILED`.

### Permissoes

- `test_cancel_command_only_pending_or_sent`: tentar cancelar comando `EXECUTING` retorna 409.
- `test_cancel_command_admin_only`: usuario sem permissao recebe 403.

### SSE

- `test_create_command_publishes_sse_event`: criar comando publica `command:new` no canal correto (mock Redis).

## Player (Vitest/JS)

### `commands.js`

- `test_platform_unsupported_throws_with_error_code`: chamar `shutdown_device` sem bridge nativo lanca erro com `code = COMMAND_NOT_IMPLEMENTED`.
- `test_execute_command_returns_platform_unsupported`: `executeCommand` retorna `result.platform_unsupported = true` quando handler lanca erro.
- `test_execute_unknown_command_returns_unknown`: comando inexistente retorna `error_code = UNKNOWN_COMMAND`.
- `test_set_volume_calls_setAudioVolume`: comando `set_volume` com payload `{volume: 0.5}` invoca `setAudioVolume(0.5)`.

### `Player.jsx` (integration com MSW)

- `test_pre_ack_for_destructive_commands`: ao processar `shutdown_device`, ACK pre_execution acontece ANTES de chamar `executeCommand`.
- `test_sse_command_new_triggers_immediate_poll`: ao receber evento SSE `command:new`, `buscarComandosPendentes` eh chamado em < 100ms.
- `test_command_lifecycle_sequence`: ordem chamada: received → started → executed/ack.

## Electron (manual)

Em maquina Linux:

1. Configurar `sudoers`: `playwave ALL=NOPASSWD: /sbin/shutdown`.
2. Rodar `npm run electron:dev`.
3. Disparar `shutdown_device` via gerenciador.
4. Verificar log do Electron mostra `IPC player:shutdown_device` e `shutdown -h +0`.
5. Verificar maquina desliga em ~5 segundos.

Em maquina Windows:

1. Rodar electron com permissoes de Administrador.
2. Disparar `shutdown_device`.
3. Verificar log mostra `shutdown /s /t 5`.
4. Verificar maquina desliga em ~5 segundos.

Em ambos:

- Verificar ACK pre_execution chega ao backend antes do shutdown.
- Verificar comando aparece como `COMPLETED` no gerenciador.

## Android APK (manual)

### Sem Device Owner

1. Instalar APK normalmente.
2. Disparar `restart_device` via gerenciador.
3. Verificar ACK retorna `failed` com `error_code = DEVICE_OWNER_REQUIRED`.
4. Gerenciador mostra "Nao suportado" com mensagem explicando provisionamento.

### Com Device Owner

1. Factory reset do dispositivo.
2. Pular configuracao de conta Google.
3. Conectar via ADB.
4. Executar: `adb shell dpm set-device-owner com.playwave.player/.PlayWaveDeviceAdminReceiver`.
5. Confirmar saida: `Success: Device owner set to package ComponentInfo{...}`.
6. Disparar `restart_device` via gerenciador.
7. Verificar tablet reinicia.

### Shutdown Android

- Disparar `shutdown_device` em APK Device Owner.
- Verificar ACK retorna `success=true` com `result.note` mencionando limitacao (`screen_locked`).
- Verificar tela bloqueia.

## Web puro (manual)

1. Abrir player em browser desktop sem Capacitor/Electron.
2. Disparar `shutdown_device` via gerenciador.
3. Verificar ACK retorna:
   - `success: false`
   - `error_code: COMMAND_NOT_IMPLEMENTED` ou `BROWSER_ENVIRONMENT`
   - `result.platform_unsupported: true`
4. Gerenciador mostra badge "Nao suportado".

## UI Gerenciador (manual)

- Lista de comandos atualiza a cada 5s automaticamente.
- Comando em `pending` tem botao "Cancelar".
- Comando `EXECUTING` mostra timestamp de cada transicao.
- Comando destrutivo dispara modal de confirmacao com nome do dispositivo.
- Modal de confirmacao mostra plataforma detectada e nivel de suporte.
- Comando expirado aparece como cinza com label "Expirou".
- Comando nao suportado aparece como cinza com label "Nao suportado".

## Carga (opcional)

- Simular 100 devices fazendo polling simultaneo a cada 10s.
- Verificar `/commands/pending` responde em < 100ms.
- Verificar uso do indice `ix_device_commands_device_status_expires` no EXPLAIN.

## Criterios de aceite finais

- [ ] Cliente confirma que comando "Desligar Dispositivo" funciona em pelo menos 1 dispositivo Electron e 1 Android Device Owner.
- [ ] Gerenciador mostra status colorido com timestamps de cada transicao.
- [ ] Comandos expirados aparecem automaticamente como `EXPIRED` sem intervencao.
- [ ] Comando em web puro retorna mensagem clara "Nao suportado".
- [ ] Documentacao de provisionamento Device Owner publicada e validada por operador real.
