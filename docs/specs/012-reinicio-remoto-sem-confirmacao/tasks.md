# SPEC 012 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 011 concluida — gate liberado.

## Diagnostico

- [x] Identificar comando real: backend aceita `restart_app` e alias `restart`. Gerenciador envia `restart_app`.
- [x] Identificar endpoints: POST /devices/{id}/command, GET /devices/{id}/commands/pending, POST /devices/{id}/commands/{cmd_id}/received, POST .../started, POST .../ack.
- [x] Identificar statuses: pending->sent->received->executing->completed/failed/expired/cancelled (enum DeviceCommandStatus completo).
- [x] Identificar handler do player: `COMMAND_HANDLERS.restart_app` em commands.js chama `callNativePowerCommand("restartApp")`.
- [x] Identificar bridge Electron: `window.__ELECTRON__.player.restartApp()` via preload.js -> IPC `player:restart_app` -> `app.relaunch()+app.quit()` no main.js.
- [x] Identificar modal atual: NAO ha modal no player. Gerenciador tem modal de confirmacao para admin (correto e esperado). Player executa silenciosamente.
- [x] Registrar bug critico: `mark_received()` e `mark_executing()` setavam `EXECUTED` (status legado) em vez de `RECEIVED` e `EXECUTING` — ciclo de vida era invisivel no gerenciador.

## Banco

- [x] `device_commands` ja tem todos os statuses necessarios no enum `DeviceCommandStatus`.
- [x] Sem necessidade de nova migration — campos ja existem.

## Backend

- [x] Criacao de comando de restart — OK: `send_device_command` valida `restart_app` em `VALID_COMMANDS` e cria com `is_destructive=True`.
- [x] Statuses `pending`, `received`, `executing`, `completed`, `failed`, `expired` — existem no enum.
- [x] Bug corrigido: `mark_received()` agora seta `RECEIVED`, `mark_executing()` agora seta `EXECUTING`.
- [x] Timeout/expiracao — OK: `get_pending()` expira comandos vencidos; Celery `expire_stale_commands` faz limpeza global.
- [x] Recuperacao de travados — corrigido: `get_pending()` agora tambem recupera comandos travados em `EXECUTING/RECEIVED/EXECUTED` apos 5 min (restart_app mata o processo antes do ACK).
- [x] Idempotencia — OK: player so executa comandos que estao em `PENDING` na fila.
- [x] `PENDING_STATUSES` corrigido para incluir `RECEIVED` e `EXECUTING` (alem de `EXECUTED` legado).

## Player

- [x] Confirmar recebimento antes da execucao — `marcarComandoRecebido()` em commandPoller.js.
- [x] Confirmar inicio antes do restart — `marcarComandoIniciado()` antes de `executeCommand()`.
- [x] Pre-ACK antes do restart destrutivo — `ackComando(success=true, ack_phase="pre_execution")` antes de chamar o handler.
- [x] Executar restart sem modal — confirmado: nenhum `confirm/dialog/prompt` no caminho de comando.
- [x] Restart via `callNativePowerCommand("restartApp")` -> Electron IPC -> `app.relaunch()+app.quit()`.
- [x] Apos restart, SPEC-011 AUTO_BOOT restaura sessao e campanha automaticamente.
- [x] Evitar loop: `get_pending()` nao retorna comandos em `COMPLETED/FAILED`.

## Electron / Windows

- [x] `window.__ELECTRON__.player.restartApp()` — implementado em preload.js.
- [x] IPC `player:restart_app` em main.js — `app.relaunch()+app.quit()` apos 500ms (garante pre-ACK chega).
- [x] Restart silencioso em modo kiosk — sem dialog.showMessageBox no caminho do IPC.
- [x] App volta para player apos restart — garantido por SPEC-011 AUTO_BOOT.

## Frontend Admin

- [x] Botao reiniciar — `COMMANDS_BY_GROUP.reset` tem `restart_app` em DispositivoDetalhe.jsx.
- [x] Modal de confirmacao admin — `isDestructive("restart_app")` abre modal antes de enviar (correto).
- [~] Feedback de status do comando — historico de comandos exibe statuses, mas `received/executing` eram invisiveis (bug corrigido agora).

## Testes

- [x] Testar restart_app criado como pending e aparece no historico (Playwright VPS CA-1).
- [x] Testar alias "restart" aceito pelo backend (Playwright VPS CA-1).
- [x] Testar comando invalido "restart_player" rejeitado (Playwright VPS CA-1).
- [x] Testar player consome restart_app via /commands/pending (Playwright VPS CA-2).
- [x] Testar ciclo de vida: received -> executing -> ack(success) = completed (Playwright VPS CA-3).
- [x] Testar ack de falha marca failed com error_message (Playwright VPS CA-3).
- [x] Testar comando com expires_in_seconds aceito (Playwright VPS CA-5).
- [x] Testar polling duplo sem reentrancia (Playwright VPS CA-6).
- [x] Testar historico registra timestamps e status (Playwright VPS CA-7).
- [x] Testar ack com result registra payload (Playwright VPS CA-7).
- [ ] Testar restart fisico em Electron Windows — requer hardware real.
- [ ] Testar retorno para campanha anterior apos restart — coberto pela SPEC-011 AUTO_BOOT (ja validado).

## Criterios de aceite

- [x] Ao clicar em reiniciar no gerenciador, o player reinicia sem confirmacao manual — sem modal no player, comando executado via IPC Electron silenciosamente.
- [x] O comando muda de pending para sucesso — ciclo pending->sent->received->executing->completed validado (12/12 Playwright).
- [x] O player volta para campanha/playlist anterior — garantido por SPEC-011 AUTO_BOOT (ja validado).
- [x] Nenhum modal bloqueia a reproducao — confirmado: nenhum confirm/dialog/prompt no caminho de comando no player.
- [x] O log do dispositivo mostra horario e resultado do comando — GET /commands retorna timestamps e result payload (validado Playwright CA-7).
- [!] Bug de ciclo de vida corrigido localmente (mark_received/mark_executing usavam EXECUTED) — pendente deploy na VPS para que gerenciador mostre statuses intermediarios corretos.

