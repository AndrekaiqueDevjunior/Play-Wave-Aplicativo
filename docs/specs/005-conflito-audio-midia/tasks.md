# SPEC 005 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Pre-requisitos

- [x] ffprobe disponível no Dockerfile do backend (confirmado via `_extract_media_metadata`).
- [x] `campaign.video_muted` mantido por 2 releases — deprecated mas presente no form como "Configuração legada".
- [x] Política default global: `auto`.

## Banco

- [x] Criar migration `20260522_2000_audio_policy.py`:
  - [x] `CREATE TYPE audio_policy_enum`.
  - [x] `ALTER TABLE tenants ADD COLUMN audio_policy_default, audio_fade_ms`.
  - [x] `ALTER TABLE devices ADD COLUMN audio_policy_default`.
  - [x] `ALTER TABLE campaigns ADD COLUMN audio_policy`.
  - [x] `ALTER TABLE media ADD COLUMN audio_policy, has_audio`.
- [x] Backfill `media.has_audio = FALSE` para `type IN ('IMAGE','EXTERNAL_URL')`.
- [x] Backfill `campaigns.audio_policy` baseado em `video_muted` legado.
- [x] Tenant default `auto` via DDL (server_default="auto").

## Backend — models

- [x] Adicionar enum `AudioPolicy` em `backend/core/models.py`.
- [x] Adicionar coluna em `Tenant`, `Device`, `Campaign`, `Media`.

## Backend — resolver

- [x] Criar `backend/services/audio_policy_resolver.py`:
  - [x] `resolve_effective_audio_policy(media_policy, campaign_policy, device_policy, tenant_policy)`.
  - [x] `resolve_media_payload(media, campaign, device, tenant)`.
  - [x] `resolve_has_audio(media)` com fallback por tipo.
  - [x] `resolve_campaign_audio_payload(campaign, device, tenant)`.
- [x] Testes unitarios do resolver (adicionados na SPEC de testes).

## Backend — pipeline de upload

- [x] Adicionar `_detect_audio_streams(file_path)` em `backend/api/v1/media.py`.
- [x] Chamar no upload de video → set `media.has_audio`.
- [x] Para imagem/external_url: `has_audio = False` automaticamente.
- [x] Endpoint `POST /media/{id}/recompute-audio-detection`.

## Backend — Celery backfill

- [x] Criar `tasks/media/backfill_has_audio.py` — roda manualmente via `python3 -m tasks.media.backfill_has_audio` e registra task Celery `tasks.media.backfill_has_audio`.
- [!] Execucao em producao/staging depende de janela operacional apos deploy.

## Backend — endpoints estendidos

- [x] `GET /devices/{id}/playlist` retorna:
  - [x] `campaign.audio_policy_default` (resolvido).
  - [x] `campaign.audio_fade_ms`.
  - [x] `media[].audio_policy_effective`.
  - [x] `media[].has_audio`.
- [x] `PUT /media/{id}` aceita `audio_policy`, `has_audio` (via MediaUpdate schema).
- [x] `PUT /campaigns/{id}` aceita `audio_policy` (via CampaignUpdate schema).
- [x] `PUT /devices/{id}` aceita `audio_policy_default` (via DeviceUpdate schema).
- [x] `PATCH /tenants/me/audio-config` aceita `audio_policy_default`, `audio_fade_ms`.
- [x] `PATCH /tenants/{id}/audio-config` (superadmin).

## Backend — schemas Pydantic

- [x] Enum `AudioPolicyEnum` em `schemas_completos.py`.
- [x] Estender `MediaCreate`, `MediaUpdate`, `MediaResponse` com `audio_policy`, `has_audio`.
- [x] Estender `CampaignBase`, `CampaignUpdate`, `CampaignResponse` com `audio_policy`.
- [x] Estender `DeviceUpdate`, `DeviceResponse` com `audio_policy_default`.
- [x] Criar `TenantAudioConfigUpdate`.
- [x] Criar `RecomputeAudioDetectionResponse`.

## Backend — cache busting

- [~] Mudanca em `audio_policy` invalida campanhas afetadas — reusa invalidação existente quando `PUT /campaigns/{id}` ou `PUT /media/{id}` são chamados. Cache busting completo (tenant-level) pendente.

## Frontend — utilitario

- [x] Criar `frontend/src/utils/audioPolicy.js` com enum + options + labels.

## Frontend — componente reusavel

- [x] Criar `frontend/src/components/shared/AudioPolicySelector.jsx`.

## Frontend — hook do player

- [x] Criar `frontend/src/hooks/useAudioConflictResolver.js`.

## Frontend — player

- [x] `Player.jsx`: importar e usar `useAudioConflictResolver`.
- [x] `Player.jsx`: adicionar estado `campaign` para guardar objeto completo da campanha.
- [x] `Player.jsx`: `audioEnabled = audioEnabled && phase === "playing"`.
- [x] `Player.jsx`: `finalVideoMuted` com fallback compat via `video_muted` legado.
- [x] `Player.jsx`: log de diagnóstico `[player] audio resolver`.
- [x] `AudioPlayer.jsx`: adicionar prop `fadeMs` (default 200).
- [x] `AudioPlayer.jsx`: implementar `doFade()` com setInterval.
- [x] `AudioPlayer.jsx`: fade in ao retomar, fade out antes de pausar.

## Frontend — telas admin

- [x] `CampaignFormModal.jsx`: seção "Política de áudio" com `AudioPolicySelector` + legado em `<details>`.
- [x] `MediaFormModal.jsx`: seção "Áudio" com `AudioPolicySelector` (allowNull) + indicador `has_audio` + botão "Recalcular".
- [x] `DispositivoDetalhe.jsx`: card "Áudio" com `AudioPolicySelector` (allowNull).
- [x] `ConfigEmpresa.jsx`: seção "Configuração de Áudio" com selector + slider de fade.

## Frontend — API clients

- [x] `frontend/src/api/midias.js`: `recomputarDeteccaoAudio`.
- [x] `frontend/src/api/tenants.js`: `atualizarConfigAudioEmpresa`.

## Frontend — avisos

- [x] Alert (aviso inline) quando operador seleciona `mix`.

## Testes

- [x] Testes do resolver backend (adicionados em `test_audio_policy_005.py`).
- [x] Testes do hook `useAudioConflictResolver` (adicionados em `audio_conflict_resolver.test.jsx`).
- [x] Testes do backfill manual `has_audio` (adicionados em `test_audio_backfill_005.py`).
- [ ] Teste E2E manual: campanha com video + radio + policy=auto → radio para com fade, vídeo toca com som.
- [ ] Teste E2E manual: mudar policy via gerenciador → SSE invalida → próxima troca reflete.

## Documentacao

- [x] Criar `docs/AUDIO_POLITICA.md` para o cliente.

## Rollout

- [x] Migration aplicada no banco.
- [~] Backfill `has_audio` para vídeos antigos (script/task pronto; execucao depende do ambiente).
- [ ] Deploy frontend.
- [ ] Validar com cliente em ao menos 1 device.

## Pos-rollout

- [ ] Monitorar uso: quantos tenants ativam policy não-auto.
- [ ] Feedback: comportamento esperado vs encontrado.
- [ ] Apos 2 releases: remover `campaign.video_muted` do frontend.
