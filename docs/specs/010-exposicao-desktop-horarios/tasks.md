# SPEC 010 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Pre-requisitos

- [x] Auditoria do Player atual (Electron, IPC show_desktop, scheduler, integração) — 2026-06-03.
- [x] Decisão: função nova e independente da exposição por intervalo (SPEC 009).
- [x] Decisão: organizar como nova SPEC 010.
- [x] Decisão: `weekdays` (dias da semana) **entra** nesta entrega, junto do horário.

## Banco

- [ ] Criar migration `2026XXXX_device_desktop_exposure_events.py`.
- [ ] Tabela `device_desktop_exposure_events` (FK device CASCADE, índice device_id, checks time/duration).

## Backend — models

- [ ] Model `DeviceDesktopExposureEvent` + relação em `Device`.

## Backend — endpoints

- [ ] `GET /devices/{id}/desktop-exposure-events`.
- [ ] `POST /devices/{id}/desktop-exposure-events`.
- [ ] `PATCH /devices/{id}/desktop-exposure-events/{event_id}`.
- [ ] `DELETE /devices/{id}/desktop-exposure-events/{event_id}`.
- [ ] Incluir `desktop_exposure_events` na playlist response.
- [ ] Publicar SSE `desktop_exposure_events_updated` em cada mutação.

## Backend — schemas Pydantic

- [ ] `DesktopExposureEventCreate` / `Update` / `Read` (validação time HH:MM, duration 1–300, name 1–120).

## Backend — outros

- [ ] Permissão admin/mesmo-tenant nos 4 endpoints (reusar padrão SPEC 009).

## Frontend Admin

- [ ] Funções de API em `frontend/src/api/`.
- [ ] Seção "Exposição de Desktop (por horário)" em `DispositivoDetalhe.jsx`.
- [ ] Lista + formulário (nome, time, duração, ativo) + remover/editar.

## Player

- [x] Novo `frontend/src/player-core/desktopExposureTimeScheduler.js`.
- [x] Cálculo do próximo horário + máquina de estados RUNNING→…→RUNNING (com weekdays).
- [x] Persistência da ação pendente via `PlayerState` (`storage.js`, chave `desktop_exposure_pending`).
- [x] `recover()` no boot (CA-009).
- [x] Fiação em `Player.jsx` (estado `desktopExposureEvents`, ref, effects, cleanup, SSE).
- [x] Electron: reuso de `player:show_desktop` via `executeCommand` (sem mudança no Electron).
- [x] Capacitor/Android: no-op silencioso (scheduler só agenda quando `isElectron`).
- [x] Log de execução local (`logger.log` em cada transição). Report remoto = fora do PR.
- [x] Bug latente corrigido: import ausente de `createWindowExposureScheduler` (SPEC 009) em `Player.jsx`.

## Documentacao

- [ ] Atualizar `frontend/electron/README.md` com a função por horário.
- [ ] README desta SPEC.

## Testes

- [ ] Backend: CRUD, validação, permissão, playlist, SSE, cascade.
- [x] Player (vitest): próximo horário, múltiplos eventos, weekdays, fase, estado, recover() — 13/13 passando.
- [ ] Manual E2E (Windows) cobrindo CA-001..CA-010, com roteiro CA-009.

## Rollout

- [ ] Deploy backend (migration).
- [ ] Deploy player.
- [ ] Deploy frontend admin.
- [ ] Validar com cliente (caso "Mostrar ERP às 08:00").

## Pos-rollout

- [ ] Observar logs de execução e recuperação após restart.

## Fora do PR inicial

- [ ] `weekdays` / janela de validade por data (se não entrar agora).
- [ ] Config por grupo de dispositivos / tenant.
- [ ] Report remoto estruturado de execuções (dashboard).
