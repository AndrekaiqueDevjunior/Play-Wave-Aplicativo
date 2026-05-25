# SPEC 001 — Database

## Tabelas analisadas

- `media`
- `media_versions`
- `campaigns`
- `devices`
- `playback_logs`
- `view_reports`
- `audio_tracks`
- `audio_playlists`

## Tabela media

Model atual: `backend/core/models.py`

Campos existentes relevantes:

- `id`
- `tenant_id`
- `name`
- `description`
- `file_url`
- `thumbnail_url`
- `type`
- `mime_type`
- `duration`
- `duration_seconds`
- `display_duration_seconds`
- `file_size`
- `file_hash`
- `file_version`
- `resolution`
- `status`
- `is_active`
- `starts_at`
- `ends_at`
- `extra_metadata`
- `tags`
- `notes`
- `category`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

## Tabela media_versions

Model atual: `MediaVersion`.

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

## Tabela campaigns

Campos usados nesta SPEC:

- `id`
- `status`
- `device_ids`
- `media_ids`
- `media_order`
- `audio_playlist_id`
- `config_version`

Observacao:

- `media_ids` e `media_order` sao JSON.
- Esta SPEC nao deve migrar esses campos para tabela relacional.
- Ao substituir midia, os JSONs nao devem ser alterados.

## Migration relacionada

Arquivo encontrado:

- `backend/alembic/versions/20260520_1000_media_metadata_versions.py`

Responsabilidades:

- Adicionar campos de metadata na tabela `media`.
- Criar tabela `media_versions`.
- Backfill parcial de `duration_seconds` e `display_duration_seconds`.

## Campos faltantes recomendados para futuro

Nao obrigatorios nesta SPEC:

- `media_processing_jobs`
- `media_playback_errors`
- `device_cache_status`
- `campaign_playlist_items`

## Regras de integridade

- `media_versions.media_id` deve referenciar `media.id`.
- Ao deletar uma midia, suas versoes podem ser apagadas em cascata.
- `ends_at` deve ser maior ou igual a `starts_at`.
- `file_version` deve iniciar em 1.
- Apenas uma versao deve ter `is_current = true` por midia.

## Backfill

Para midias antigas:

- `duration_seconds` pode receber valor de `duration` temporariamente.
- `display_duration_seconds` pode receber `duration` para imagem/link.
- `file_version` deve ser 1.
- `file_hash` pode ficar nulo ate arquivo ser reprocessado.
- `media_versions` pode ser populada em tarefa posterior.

## Indices recomendados

- `media.starts_at`
- `media.ends_at`
- `media.file_hash`
- `media_versions.media_id`

## Riscos de banco

- Campos JSON em campanha impedem FK real entre campanha e midia.
- Consulta de uso de midia exige varredura em campanhas.
- Backfill de hash exige acesso ao arquivo fisico.
- Remover arquivo fisico antes de remover registros pode deixar referencias quebradas se ocorrer erro.
