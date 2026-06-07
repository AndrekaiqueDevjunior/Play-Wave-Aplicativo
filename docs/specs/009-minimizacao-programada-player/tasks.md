# SPEC 009 - Tasks

Status: `[ ]` pendente - `[~]` parcial - `[x]` concluido - `[!]` bloqueado/decisao.

## Pre-requisitos

- [x] Auditoria tecnica criada em `AUDITORIA_MINIMIZACAO_PROGRAMADA_PLAYER.md`.
- [x] Definir dominio principal: `devices`.
- [x] Confirmar ambiente alvo inicial: Windows/Linux Electron no PR inicial.
- [x] Confirmar limites desejados de intervalo/duracao com o usuario final (10-86400s intervalo, 1-300s duracao).

## PR 1 - Comandos manuais de janela (baixo risco)

### Backend

- [x] TDD: teste para aceitar `minimize_player`, `restore_player`, `show_desktop`.
- [x] Atualizar `VALID_COMMANDS` em `backend/api/v1/devices.py`.
- [x] Validar payload `duration_seconds` de `show_desktop` se presente.

### Player

- [x] TDD: teste de `show_desktop` sem bridge retorna `platform_unsupported`.
- [x] Adicionar handlers em `frontend/src/player-core/commands.js`.
- [x] Garantir ACK com `platform`, `command_type`, `completed_at` ou `failed_at`.

### Electron

- [x] TDD/manual: definir checklist antes da implementacao.
- [x] Expor `minimizeWindow`, `restoreWindow`, `showDesktop` em `frontend/electron/preload.js`.
- [x] Implementar IPC em `frontend/electron/main.js`.
- [x] Preservar/restaurar fullscreen/alwaysOnTop.

### Frontend Admin

- [x] Adicionar labels em `frontend/src/utils/deviceCommands.js`.
- [x] Adicionar botoes em `frontend/src/pages/DispositivoDetalhe.jsx`.
- [x] Adicionar opcao de payload `duration_seconds` para "Mostrar desktop agora".

### Testes

- [x] Rodar testes backend afetados. Dependência Python `python-jose` instalada.
- [x] Rodar testes frontend/player afetados. `node_modules` e `vitest` instalados.
- [x] Teste manual Electron.

## PR 2 - Config persistente por dispositivo

### Banco

- [x] TDD backend falhando para config inexistente.
- [x] Criar migration `20260601_1800_desktop_exposure_config.py`.
- [x] Adicionar campos `desktop_exposure_*` em `Device`.
- [x] Backfill defaults desligados.

### Backend

- [x] Criar schema `DeviceDesktopExposureConfigUpdate`.
- [x] Criar endpoint `PATCH /devices/{device_id}/desktop-exposure-config`.
- [x] Incluir config em response de device.
- [x] Incluir config em `/devices/{device_id}/playlist`.
- [x] Publicar SSE `config:desktop_exposure_updated`.

### Testes

- [x] Valida config ativa correta.
- [x] Rejeita duracao >= intervalo.
- [x] Rejeita duracao fora do range.
- [x] Garante default desligado para device antigo.

## PR 3 - Cronometro frontend e scheduler local

### Frontend Admin

- [x] Criar secao "Comportamento do Player".
- [x] Toggle ativar/desativar rotina.
- [x] Inputs intervalo/duracao.
- [x] Preview "A cada X segundos...".
- [x] Botao "Salvar".
- [x] Botao "Testar agora".

### Player

- [x] Criar `windowExposureScheduler.js`.
- [x] Aplicar config recebida por playlist.
- [x] Aplicar config recebida por SSE.
- [x] Cancelar timers em cleanup/reconfig.
- [x] Nao rodar scheduler em `waiting`/`pairing`.

### Testes

- [x] Teste unitario scheduler start/stop.
- [x] Teste de validacao UI.
- [x] Teste manual ciclo 20s/5s.

## PR 4 - Hardening, docs e rollout

### Bugs

- [x] Testar comandos concorrentes.
- [x] Testar reconnect SSE.
- [x] Testar restore depois de app sair de fullscreen.
- [x] Testar player sem campanha.

### Seguranca

- [x] Confirmar permissoes admin/tenant no endpoint.
- [x] Confirmar payload sanitizado.
- [x] Confirmar sem shell para window-control no PR inicial.

### Performance

- [x] Confirmar sem novo polling backend.
- [x] Confirmar um timer ativo por Player.
- [x] Confirmar sem crescimento de comandos automaticos no banco.

### Documentacao

- [x] Atualizar `frontend/electron/README.md`.
- [x] Atualizar auditoria com resultado implementado.
- [x] Registrar limitacoes Android/Smart TV.

## Fora do PR inicial

- [ ] Config global por tenant.
- [ ] Config por grupo de dispositivos.
- [ ] Agente externo Windows/Linux.
- [ ] Android Device Owner/Lock Task Mode para minimizar/restaurar.
