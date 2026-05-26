# PlayWave — Technical Design Map

Data base: 2026-05-20

Este documento traduz os requisitos do `requirements.md` para arquitetura, entidades, fluxos, APIs e contratos tecnicos. Ele deve ser atualizado antes de qualquer implementacao relevante.

## Arquitetura Atual

### Backend

- FastAPI.
- SQLAlchemy.
- Alembic.
- Redis para cache de playlist e eventos.
- Celery para tarefas em background.
- Endpoints principais em `backend/api/v1`.
- Models em `backend/core/models.py`.
- Schemas em `backend/core/schemas_completos.py`.
- CRUDs em `backend/crud/entidades`.

### Frontend

- React + Vite.
- React Query para chamadas e cache client-side.
- Componentes administrativos em `frontend/src/pages` e `frontend/src/components`.
- APIs em `frontend/src/api`.
- Player web em `frontend/src/pages/Player.jsx`.

### Player

- Busca playlist por dispositivo.
- Mantem cache local.
- Executa midias visuais.
- Executa audio de fundo quando configurado.
- Envia heartbeat.
- Consulta comandos remotos.
- Escuta eventos SSE de atualizacao.

## Principios de Design

- Campanha define intencao.
- Player executa fila validada.
- Midia tem metadados reais e validade propria.
- Substituir arquivo nao altera identidade da midia.
- Toda alteracao que afeta player gera nova versao/configuracao.
- Cache deve ser invalidado por alvo afetado, nao globalmente.
- O painel deve mostrar estado operacional real, nao apenas cadastro.

## Entidades Principais

### Media

Responsavel por representar um arquivo, URL ou asset exibivel.

Campos essenciais:

- `id`
- `tenant_id`
- `name`
- `description`
- `type`
- `file_url`
- `thumbnail_url`
- `mime_type`
- `file_size`
- `file_hash`
- `duration`
- `duration_seconds`
- `display_duration_seconds`
- `resolution`
- `starts_at`
- `ends_at`
- `status`
- `is_active`
- `category`
- `tags`
- `notes`
- `file_version`
- `extra_metadata`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

Regras:

- `duration_seconds` e a duracao real detectada do arquivo.
- `display_duration_seconds` e a duracao operacional enviada ao player.
- Video/audio sem `display_duration_seconds` tocam ate o fim.
- Imagem/link precisam de duracao de exibicao.
- Midia expirada/agendada/inativa nao entra como item valido da fila.

### MediaVersion

Historico de substituicoes de arquivo mantendo o mesmo `media_id`.

Campos:

- `id`
- `media_id`
- `file_url`
- `thumbnail_url`
- `file_name`
- `mime_type`
- `file_size`
- `file_hash`
- `duration_seconds`
- `version_number`
- `is_current`
- `created_at`
- `created_by`

### Campaign

Representa o plano de exibicao.

Campos principais:

- `id`
- `name`
- `status`
- `priority`
- `start_date`
- `end_date`
- `schedule_all_day`
- `schedule_days`
- `schedule_start_time`
- `schedule_end_time`
- `device_ids`
- `media_ids`
- `media_order`
- `audio_playlist_id`
- `video_muted`
- `loop_count`
- `config_version`

Estado futuro recomendado:

- Migrar `device_ids`, `media_ids` e `media_order` de JSON para tabelas relacionais.
- Separar rascunho/publicacao.
- Criar snapshots de fila por device.

### CampaignPlaylistItem

Tabela futura para substituir checkbox/listas JSON.

Campos:

- `id`
- `campaign_id`
- `media_id`
- `order_index`
- `display_duration_seconds`
- `starts_at`
- `ends_at`
- `is_active`
- `repeat_count`
- `playback_mode`
- `created_at`
- `updated_at`

### Device

Representa TV/player.

Campos principais:

- `id`
- `tenant_id`
- `name`
- `status`
- `device_token`
- `pairing_code`
- `pairing_version` (migration 20260521_0900)
- `token_version` (migration 20260521_0900)
- `requires_repairing` (migration 20260521_0900)
- `current_campaign_id`
- `current_campaign`
- `config_version`
- `player_version`
- `os`
- `screen_resolution`
- `last_seen_at`
- `audio_playlist_id`

Campos adicionados por SPECs 005-006 (em pasta `docs/specs/`):

- `audio_policy_default` (SPEC 005, nullable — herda do tenant).
- `osd_show_current_audio`, `osd_position`, `osd_duration_seconds`, `osd_opacity`, `osd_font_size` (SPEC 006, nullable — herdam do tenant).
- `current_audio_track_id`, `current_audio_track_name`, `current_audio_track_started_at` (SPEC 006, populated via heartbeat).

Campos futuros recomendados:

- `current_config_version`
- `current_media_id`
- `current_media_name`
- `queue_version`
- `storage_used`
- `storage_free`
- `last_error`
- `playback_status`

### DeviceCommand

Representa comando remoto.

Campos principais:

- `id`
- `device_id`
- `tenant_id`
- `command_type`
- `payload`
- `status`
- `requested_by`
- `requested_at`
- `sent_at`
- `received_at` (migration 20260521_0915)
- `started_at` (migration 20260521_0915)
- `executed_at`
- `expires_at` (migration 20260521_0915)
- `result` (JSON, migration 20260521_0915)
- `error_message`

Adicionado por SPEC 003:

- `is_destructive` (boolean, true para restart_device/shutdown_device/factory_reset).

Estados (DeviceCommandStatus enum):

- PENDING
- SENT
- RECEIVED
- EXECUTING
- COMPLETED (alias: EXECUTED)
- FAILED
- EXPIRED
- CANCELLED

### Audio

Entidades recomendadas:

- `audio_tracks`
- `audio_playlists`
- `audio_playlist_items`
- `radio_points`
- `radio_point_playlists`
- `audio_spots`
- `audio_spot_schedules`

## Tabelas Recomendadas

### Ja implementadas ou em andamento

- `media`
- `media_versions`
- `campaigns`
- `campaign_playlist_items` (migration 20260520_1400)
- `devices` (com pairing_version/token_version/requires_repairing via migration 20260521_0900)
- `device_commands` (com lifecycle expandido via migration 20260521_0915)
- `playback_logs`
- `view_reports`
- `audio_tracks`
- `audio_playlists`

### Adicionadas pelas SPECs 003-006 (em pasta `docs/specs/`)

- `device_pairing_events` (SPEC 004) — auditoria de regenerate/force-repair/etc.
- Colunas `audio_policy_*` em `tenants`, `devices`, `campaigns`, `media` (SPEC 005).
- Coluna `has_audio` em `media` (SPEC 005).
- Colunas `osd_*` em `tenants` e `devices` (SPEC 006).
- Colunas `current_audio_track_*` em `devices` (SPEC 006).
- Coluna `is_destructive` em `device_commands` (SPEC 003).
- Indice `ix_device_commands_device_status_expires` (SPEC 003).

### Proximas tabelas

- `campaign_devices`
- `campaign_delivery_status`
- `device_queue_snapshots`
- `device_heartbeats`
- `device_command_results`
- `player_events`
- `media_processing_jobs`
- `media_playback_errors`
- `device_cache_status`
- `campaign_conflicts`
- `audit_logs`
- `device_groups`
- `device_group_members`
- `campaign_target_rules`
- `audio_folders`, `audio_folder_tracks` (radio v2)
- `audio_playlist_items`, `audio_playlist_schedules` (radio v2)
- `audio_spots`, `audio_spot_schedules` (radio v2)

## Fluxos Operacionais

### Fluxo: Upload de Midia

1. Admin envia arquivo.
2. Backend valida MIME, extensao e tamanho.
3. Backend salva arquivo.
4. Backend calcula `file_hash`.
5. Backend extrai metadados via `ffprobe` quando video/audio.
6. Backend salva `duration_seconds`.
7. Backend define `display_duration_seconds` conforme tipo.
8. Backend cria primeira linha em `media_versions`.
9. Frontend mostra duracao detectada e status.

### Fluxo: Substituir Arquivo

1. Admin abre midia existente.
2. Admin aciona "Substituir arquivo".
3. Backend valida tipo do novo arquivo.
4. Backend salva novo arquivo.
5. Backend recalcula hash, duracao e metadata.
6. Backend incrementa `file_version`.
7. Backend marca versoes antigas como nao atuais.
8. Backend cria nova `media_versions`.
9. Backend atualiza `config_version` das campanhas afetadas.
10. Backend invalida cache dos devices afetados.
11. Player recebe novo `file_hash/file_version` e baixa arquivo atualizado.

### Fluxo: Publicar Campanha

1. Admin monta playlist.
2. Sistema valida midias.
3. Sistema valida alvos.
4. Sistema valida agenda.
5. Sistema verifica conflitos/prioridade.
6. Sistema gera `config_version`.
7. Sistema publica campanha.
8. Sistema invalida cache dos players afetados.
9. Players sincronizam.
10. Painel de entrega mostra resultado por device.

### Fluxo: Player Sync

1. Player chama playlist do dispositivo.
2. Backend resolve campanha ativa.
3. Backend ordena midias.
4. Backend remove midias invalidas:
   - expirada;
   - agendada;
   - inativa;
   - erro;
   - sem arquivo valido.
5. Backend retorna campanha, midias, audio, versoes e regras.
6. Player compara cache local com `file_hash/file_version`.
7. Player executa fila.
8. Player envia heartbeat e playback logs.

### Fluxo: Entrega da Campanha

1. Admin abre campanha.
2. Backend lista dispositivos alvo.
3. Backend compara versao esperada e versao atual.
4. Backend compara fila esperada e fila reportada.
5. Backend mostra status final:
   - sincronizado;
   - pendente;
   - offline;
   - erro;
   - executando.

## Contratos de API

### Midias

- `POST /media/upload`
- `GET /media`
- `GET /media/{id}`
- `PUT /media/{id}`
- `POST /media/{id}/replace-file`
- `GET /media/{id}/usage`
- `GET /media/{id}/versions`
- `DELETE /media/{id}`

### Campanhas

- `POST /campaigns`
- `GET /campaigns`
- `GET /campaigns/{id}`
- `PUT /campaigns/{id}`
- `DELETE /campaigns/{id}`
- `POST /campaigns/{id}/publish`
- `POST /campaigns/{id}/pause`
- `POST /campaigns/{id}/resume`
- `POST /campaigns/{id}/archive`
- `GET /campaigns/{id}/delivery`
- `POST /campaigns/{id}/sync`
- `GET /campaigns/{id}/conflicts`

### Playlist de Campanha

- `POST /campaigns/{id}/items`
- `PUT /campaigns/{id}/items/{item_id}`
- `DELETE /campaigns/{id}/items/{item_id}`
- `PATCH /campaigns/{id}/items/reorder`

### Player e Dispositivos

- `POST /devices/pair-request`
- `GET /devices/by-code/{code}/status`
- `GET /devices/{device_id}/playlist`
- `POST /devices/{device_id}/heartbeat`
- `POST /devices/{device_id}/playback`
- `GET /devices/{device_id}/commands/pending`
- `POST /devices/{device_id}/commands/{command_id}/ack`
- `GET /devices/{device_id}/playlist/updates`

### Comandos

- `POST /devices/{device_id}/commands`
- `GET /devices/{device_id}/commands`
- `GET /commands`
- `GET /commands/{id}`
- `POST /commands/{id}/cancel`
- `POST /commands/bulk`

### Audio e Radio

- `POST /audio/upload`
- `POST /audio/bulk-upload`
- `GET /audio/tracks`
- `POST /audio/playlists`
- `GET /audio/playlists`
- `POST /audio/playlists/{id}/items`
- `PATCH /audio/playlists/{id}/items/reorder`
- `POST /radio-points`
- `POST /radio-points/{id}/playlists`
- `POST /audio-spots`
- `GET /audio-spots`
- `PATCH /audio-spots/{id}`

### Cache, Logs e Relatorios

- `GET /devices/{id}/cache`
- `POST /devices/{id}/cache/clear`
- `GET /logs/player-events`
- `GET /reports/campaigns`
- `GET /reports/media`
- `GET /reports/devices`
- `GET /reports/commands`

## Payload do Player

### Playlist Response

```json
{
  "device_name": "TV Loja 01",
  "campaign": {
    "id": "uuid",
    "name": "Campanha Maio",
    "config_version": "uuid",
    "video_muted": true,
    "loop_count": null,
    "start_date": "2026-05-20T00:00:00",
    "end_date": null
  },
  "media": [
    {
      "id": "uuid",
      "media_id": "uuid",
      "name": "Oferta Maio",
      "type": "video",
      "file_url": "/uploads/media/file.mp4",
      "thumbnail_url": null,
      "duration": null,
      "duration_seconds": 60,
      "display_duration_seconds": null,
      "play_until_end": true,
      "file_version": 2,
      "file_hash": "sha256",
      "mime_type": "video/mp4",
      "status": "available",
      "starts_at": null,
      "ends_at": null
    }
  ],
  "audio_playlist": null
}
```

## Frontend Administrativo

### Central de Midias

- Upload de midia.
- Edicao de metadados.
- Duracao detectada.
- Duracao customizada.
- Periodo de exibicao.
- Substituir arquivo.
- Uso em campanhas.
- Status de disponibilidade.

### Central de Campanhas

- Lista de campanhas.
- Status operacional.
- Criacao/edicao.
- Construtor de playlist.
- Drag and drop.
- Validacao antes de publicar.
- Preview.

### Central de Players

- Lista de dispositivos.
- Status online/offline.
- Campanha atual.
- Midia atual.
- Ultimo heartbeat.
- Comandos rapidos.

### Central de Entrega

- Entrega por campanha.
- Comparacao esperado vs atual.
- Erros por player.
- Sync em lote.

### Central de Comandos

- Historico.
- Status.
- Resultado.
- Envio em lote.

### Central de Audio

- Trilhas.
- Playlists.
- Pontos/radios.
- Spots.

### Saude do Sistema

- Redis.
- Celery.
- Banco.
- Backend.
- Players atrasados.

## Decisoes Tecnicas Atuais

- Usar `ffprobe` para extrair duracao de video/audio.
- Usar `file_hash` e `file_version` para cache busting do player.
- Manter compatibilidade com campo legado `duration`.
- Usar Redis para cache de playlist por device.
- Invalidar cache somente dos devices afetados quando possivel.
- Bloquear exclusao de midia em uso sem `force`.

## Riscos Tecnicos

- Relacionamentos campanha/midia/dispositivo ainda em JSON dificultam integridade.
- Thumbnail real de video ainda precisa pipeline.
- Processamento pesado de midia deve migrar para Celery.
- Player precisa reportar mais estado para fechar entrega operacional.
- Sem tabelas relacionais, relatorios e conflitos ficam mais caros.

## Especificacoes em Pasta Detalhada

A partir de 2026-05-22, as especificacoes detalhadas vivem em `docs/specs/NNN-nome-curto/` com a estrutura:

- `requirements.md` — RFs numerados, escopo, riscos.
- `design.md` — fluxos, decisoes tecnicas, pseudocodigo.
- `database.md` — migrations e modelos.
- `api-contract.md` — endpoints, schemas Pydantic, headers, SSE.
- `frontend.md` — componentes admin.
- `player.md` — mudancas no player/Electron/Capacitor.
- `tasks.md` — backlog executavel.
- `tests.md` — plano de testes.

Template em `docs/specs/_TEMPLATE/`. Specs ativas:

- `001-midias-inteligentes/` — em andamento.
- `002-radio-audio-player/` — apenas `diagnostico.md` (auditoria 2026-05-21).
- `003-player-comandos-nativos/` — completa (2026-05-22).
- `004-pareamento-revocacao/` — completa (2026-05-22).
- `005-conflito-audio-midia/` — completa (2026-05-22).
- `006-osd-musica-atual/` — completa (2026-05-22).
