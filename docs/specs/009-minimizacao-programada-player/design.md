# SPEC 009 - Design Tecnico

## Decisao principal

A feature pertence ao dominio de **Dispositivos / Player Behavior**.

Nao implementar em:

- `campaigns`: campanha e conteudo/programacao de midia;
- `media`: midia e arquivo/conteudo;
- `schedule`: agenda de campanhas;
- `reports`: apenas leitura/auditoria.

Implementar em:

- `backend/api/v1/devices.py`;
- `backend/core/models.py` em `Device`;
- `frontend/src/pages/DispositivoDetalhe.jsx`;
- `frontend/src/player-core/commands.js`;
- `frontend/electron/main.js` e `frontend/electron/preload.js`.

## Arquitetura alvo

### Comando manual

```text
Admin UI
  -> POST /devices/{device_id}/command
  -> device_commands
  -> Redis/SSE command:new
  -> Player.jsx pollCommands()
  -> commands.js handler
  -> Electron preload bridge
  -> Electron main BrowserWindow
  -> ACK /commands/{command_id}/ack
```

### Configuracao cronometrada

```text
Admin UI
  -> PATCH /devices/{device_id}/desktop-exposure-config
  -> devices.desktop_exposure_*
  -> publish_device_event("config:desktop_exposure_updated")
  -> Player.jsx reload/merge config
  -> player-core/windowExposureScheduler.js
  -> commands.js show_desktop
  -> Electron BrowserWindow
```

## Componentes novos

### Backend

- campos em `Device`;
- schema Pydantic `DeviceDesktopExposureConfigUpdate`;
- endpoint `PATCH /devices/{device_id}/desktop-exposure-config`;
- inclusion da config no retorno de `GET /devices/{device_id}/playlist` ou endpoint especifico;
- novos `VALID_COMMANDS`.

### Frontend Admin

- secao "Comportamento do Player" em `DispositivoDetalhe.jsx`;
- toggle para ativar;
- inputs numericos para intervalo/duracao;
- botao "Testar agora";
- preview/cronometro da regra.

### Player

- handlers `minimize_player`, `restore_player`, `show_desktop`;
- scheduler local para rotina cronometrada;
- bridge nativa para Electron.

### Electron

Novos metodos expostos no preload:

- `minimizeWindow()`;
- `restoreWindow()`;
- `showDesktop(durationSeconds)`;
- `setFullscreen(enabled)`.

Novos IPC handlers no main:

- `player:minimize_window`;
- `player:restore_window`;
- `player:show_desktop`;
- `player:set_fullscreen`.

## Ciclo temporizado

O ciclo deve ficar no Player local.

Razoes:

- nao depende da latencia do backend;
- evita criar milhares de comandos no banco;
- continua funcionando em queda temporaria de rede;
- reduz carga em Redis/SSE.

Fluxo:

1. Player recebe config.
2. Se `enabled=false`, cancela timers.
3. Se `enabled=true`, agenda proxima minimizacao.
4. Ao chegar o intervalo, executa `show_desktop(duration)`.
5. Ao restaurar, agenda proxima rodada.

## Estimativa de linhas

Entrega completa aproximada:

- backend model/schema/endpoint/migration: 180-260 linhas;
- frontend admin: 180-300 linhas;
- player scheduler/handlers: 150-230 linhas;
- Electron preload/main: 60-120 linhas;
- testes: 250-500 linhas.

Total esperado: 800-1400 linhas.

Portanto, dividir em sub-tarefas/PRs e obrigatorio.

## Divisao recomendada em PRs pequenos

### PR 1 - Comandos manuais Electron

Escopo:

- backend aceita `minimize_player`, `restore_player`, `show_desktop`;
- `commands.js` implementa handlers;
- Electron expose/IPC;
- UI adiciona botoes "Minimizar", "Restaurar", "Mostrar desktop agora";
- testes unitarios basicos.

Sem banco novo.

### PR 2 - Config persistente por dispositivo

Escopo:

- migration campos `desktop_exposure_*` em `devices`;
- schema update/response;
- endpoint PATCH;
- incluir config em playlist/device response;
- testes backend.

### PR 3 - Cronometro frontend e scheduler do Player

Escopo:

- UI de config com intervalo/duracao;
- scheduler local no Player;
- SSE/config reload;
- testes frontend/player.

### PR 4 - Hardening e rollout

Escopo:

- limites e edge cases;
- docs Windows/Linux;
- testes manuais E2E;
- monitorar ACKs `platform_unsupported`.

## Bugs previstos e mitigacoes

- Timer duplicado: manter refs e cleanup no unmount/config change.
- Minimizar durante pairing: scheduler so roda em `playing` ou `no_campaign`.
- Kiosk impede minimizar: desativar fullscreen antes de minimizar se necessario.
- Restore nao volta ao foco: usar `show`, `restore`, `focus`, `setFullScreen` conforme config.
- `show_desktop` concorrente: se ja esta em execucao, ignorar ou reiniciar timer de restore.

## Seguranca

- Sem shell no PR inicial.
- Validar payloads no backend.
- Apenas usuarios autorizados podem alterar config/enviar comando.
- Nao expor APIs de janela no browser puro.

## Performance

- Sem novo polling.
- Scheduler local com um unico timeout ativo.
- Config update via SSE best-effort com fallback por reload de playlist.


