# SPEC 004 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Pre-requisitos

- [x] Definir duracao do compat-period: **1 release**. Header ausente = versao 1 com warning.
- [x] Decidir SSE vs polling 401: **ambos** (SSE otimista + polling como fallback).

## Banco

- [x] Criar migration `20260522_1500_device_pairing_events`:
  - [x] Tabela `device_pairing_events`.
  - [x] Indices `device_id+created_at` e `event_type`.
- [x] Sem alteracoes em `devices` (colunas ja existem desde `20260521_0900_device_pairing_token_version`).

## Backend — validacao de token_version

- [x] Atualizar dependency `get_device_by_token` em `backend/api/v1/devices.py`:
  - [x] Ler header `X-Device-Token-Version` (string → int).
  - [x] Comparar com `device.token_version`.
  - [x] Retornar 401 com `error_code=TOKEN_VERSION_MISMATCH` quando difere.
  - [x] Compat-period: header ausente = aceita com warning no log.
  - [x] Retornar 401 com `error_code=TOKEN_VERSION_REQUIRED` apos compat-period.
- [x] Criar helper `DeviceAuthError` em `backend/api/v1/devices.py` (lines 96-162).
- [~] Substituir todas as `HTTPException(401, "...")` por `DeviceAuthError`: feito em get_device_by_token; endpoint SSE ainda usa HTTPException (aceitavel — SSE autentica via query param, nao header).

## Backend — endpoint force-repair

- [x] Adicionar `POST /devices/{device_id}/force-repair`.
- [x] Incrementar `token_version`, setar `device_token=NULL`, `requires_repairing=True`.
- [x] Registrar evento `force_repair` em `device_pairing_events`.
- [x] Publicar SSE `pairing:revoked` no canal do device.
- [x] Retornar `ForceRepairResponse`.

## Backend — endpoint pairing-events

- [x] Adicionar `GET /devices/{device_id}/pairing-events`.
- [x] Implementar `crud_device_pairing_event.list_by_device(device_id, limit, event_type)`.
- [x] Filtrar por tenant + permissao admin.

## Backend — auditoria nos endpoints existentes

- [x] `regenerate_pairing_code` registra `code_regenerated` com previous/new versions, reason, revoked_sessions_count.
- [x] `revoke_token` (legado) registra `token_revoked`.
- [x] Pareamento (via `check_pairing_status`) registra `paired` ou `re_paired` via `_log_paired_event`.
- [x] `block_device` / `unblock_device` registram `device_blocked` / `device_unblocked`.

## Backend — response estendido

- [x] `GET /devices/by-code/{code}/status` retorna `token_version` e `pairing_version` quando `status=paired` (via `_paired_response`).
- [~] `POST /devices/{device_id}/pair-confirm` (admin): retorna `DeviceResponse` — endpoint legado, nao usado pelo player; sem alteracao necessaria.
- [x] `regenerate_pairing_code` retorna `previous_pairing_code`.

## Backend — schemas Pydantic

- [x] Atualizar `PairCodeStatusResponse` com `token_version`, `pairing_version`.
- [x] Criar `RegenerateCodeRequest`, `RegenerateCodeResponse`.
- [x] Criar `ForceRepairRequest`, `ForceRepairResponse`.
- [x] Criar `DevicePairingEventResponse`.

## Backend — SSE

- [x] Publicar evento `pairing:revoked` via `_publish_pairing_revoked` em `devices.py`.
- [x] Canal confirmado: `pw:device:{device_id}:events`.

## Player — storage

- [x] Atualizar `frontend/src/player-core/storage.js`:
  - [x] Nova key `pw_player_token_version` (LS_TOKEN_VERSION).
  - [x] Metodo `PairingStorage.tokenVersion()`.
  - [x] Metodo `PairingStorage.setTokenVersion(v)`.
  - [x] `PairingStorage.save` aceita `tokenVersion` e `pairingVersion`.
  - [x] `PairingStorage.clear` remove todas as keys pw_player_*.

## Player — repair

- [x] Criar `frontend/src/player-core/repair.js`:
  - [x] `forceRepair(reason)` com anti-loop (max 3 em 5min, backoff 30s).
  - [x] `onForceRepair(callback)` registry.
  - [x] `RepairTriggeredError` class.
  - [x] Idempotente: multiplas chamadas paralelas retornam mesma Promise.

## Player — http interceptors

- [x] Atualizar `frontend/src/api/http.js`:
  - [x] Request interceptor injeta `X-Device-Token` e `X-Device-Token-Version`.
  - [x] Response interceptor captura 401/403 com `error_code` em whitelist → dispara `forceRepair`.

## Player — dispositivos.js

- [x] `verificarStatusPareamento`: player persiste `token_version` em Player.jsx apos retorno.
- [x] `confirmarPareamento`: endpoint admin legado, nao usado no fluxo do player.

## Player — Player.jsx

- [x] Importar `onForceRepair` e registrar callback que reseta para fase `waiting`.
- [x] Adicionar estado `forceRepairReason` e passar para `PairingScreen`.
- [x] Adicionar SSE listener para `pairing:revoked` que dispara `forceRepair`.
- [x] Watchdog desabilitado durante `phase === "waiting"` ou `"pairing"`.
- [x] Tratar `status === "expired"` no polling: gera novo codigo e mostra banner.
- [x] Tratar `reason === "code_regenerated"` no forceRepair callback: gera novo codigo (pairing_code do device mudou no backend).

## Player — pairing screen

- [x] `PairingScreen` aceita prop `forceRepairReason` e exibe banner amarelo.
- [x] Mapa `REPAIR_MESSAGES` interno com todos os `error_code` + razoes SSE.

## Frontend Gerenciador — API client

- [x] Adicionar `buscarSessoesAtivas(deviceId)`.
- [x] Adicionar `forcarReparamento(deviceId, reason)`.
- [x] Adicionar `listarEventosPareamento(deviceId, params)`.
- [x] `regenerarCodigoPareamento(deviceId, reason)` aceita reason e passa no body.

## Frontend Gerenciador — UI

- [x] Reorganizar secao "Pareamento" em `DispositivoDetalhe.jsx`.
- [x] Criar `RegenerateCodeDialog.jsx` com lista de sessoes ativas + motivo + confirmacao forte.
- [x] Criar `ForceRepairDialog.jsx` sem trocar codigo, com campo reason.
- [x] Criar `PairingEventTimeline.jsx` com todos os event_types.
- [x] Adicionar secao "Historico de pareamento" no DispositivoDetalhe.
- [x] Toasts de sucesso/erro apos cada acao.

## Testes

- [ ] Teste backend: regenerate cria row em `device_pairing_events`.
- [ ] Teste backend: force-repair nao altera `pairing_code`.
- [ ] Teste backend: request com `X-Device-Token-Version` errado retorna 401 `TOKEN_VERSION_MISMATCH`.
- [ ] Teste backend: request sem header (compat) aceita com warning.
- [ ] Teste backend: pairing-events listagem paginada e por event_type.
- [ ] Teste player: forceRepair limpa localStorage e IndexedDB.
- [ ] Teste player: anti-loop limita 3 forceRepairs em 5min.
- [ ] Teste player: interceptor 401 com error_code valido dispara forceRepair.
- [ ] Teste player: interceptor 500 ou outro erro nao dispara forceRepair.
- [ ] Teste E2E manual: regenerar codigo via gerenciador expulsa player em < 5s (SSE) ou < 10s (polling).
- [ ] Teste E2E manual: force-repair mantem codigo, player precisa reparear com mesmo codigo.
- [ ] Teste E2E manual: codigo expirado (aguardar 30min) — TV gera novo codigo automaticamente.

## Documentacao

- [ ] Atualizar `docs/specs/004-pareamento-revocacao/README.md` com diagrama de fluxo.
- [ ] Documentar `error_code` enum em `docs/API.md` (criar se nao existir).
- [ ] Atualizar manual do operador com diferenca entre "Regenerar codigo" e "Forcar reparamento".

## Rollout

- [ ] Deploy backend (migration + endpoint + audit).
- [ ] Deploy frontend gerenciador.
- [ ] Deploy player com persistencia de `token_version` (sem ativar validacao estrita ainda).
- [ ] Aguardar 1 release ou 2 semanas (compat-period).
- [ ] Ativar validacao estrita: header obrigatorio.
- [ ] Monitorar 401 spike e ajustar se necessario.

## Pos-rollout

- [ ] Monitorar metricas:
  - quantidade de force-repairs/dia.
  - quantidade de regenerate-codes/dia.
  - players com header `X-Device-Token-Version` ausente (devem zerar apos compat).
- [ ] Coletar feedback do cliente sobre fluxo de reparamento.
