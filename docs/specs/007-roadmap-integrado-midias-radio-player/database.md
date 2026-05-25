# SPEC 007 — Banco de dados

## Ja existente

- `media.duration_seconds`, `display_duration_seconds`, `starts_at`, `ends_at`, `file_hash`, `file_version`, `has_audio`, `audio_policy`.
- `media_versions`.
- `campaign_playlist_items`.
- `audio_tracks`.
- `audio_playlists` com `track_ids` JSON.
- `device_commands` com ciclo de vida.
- `device_pairing_events`.
- colunas OSD e musica atual em `tenants` e `devices`.

## Novas migrations propostas

### `2026XXXX_audio_playlist_items.py`

Criar tabela:

- `id`
- `playlist_id`
- `track_id`
- `order_index`
- `volume`
- `is_active`
- `starts_at`
- `ends_at`
- `created_at`
- `updated_at`

Backfill:

- para cada `audio_playlists.track_ids`, criar itens ordenados.

Indices:

- `(playlist_id, order_index)`
- `(track_id)`

### `2026XXXX_audio_folders.py`

Criar:

- `audio_folders`
  - `id`, `tenant_id`, `name`, `description`
  - `starts_at`, `ends_at`
  - `start_time`, `end_time`
  - `status`
  - `play_mode`
  - `priority`
- `audio_folder_tracks`
  - `folder_id`, `track_id`, `order_index`, `is_active`

Indices:

- `(tenant_id, status)`
- `(starts_at, ends_at)`
- `(start_time, end_time)`

### `2026XXXX_audio_playlist_folder_schedules.py`

Criar:

- `playlist_id`
- `folder_id`
- `start_time`
- `end_time`
- `starts_at`
- `ends_at`
- `days_of_week`
- `priority`
- `play_mode`
- `is_active`

Regra:

- conflito de horario dentro da mesma playlist deve ser impedido ou exigir prioridade explicita.

### `2026XXXX_audio_spots.py`

Criar:

- `audio_spots`
  - `id`, `tenant_id`, `track_id`, `name`, `status`
  - `insertion_policy`
  - `created_at`, `updated_at`
- `audio_spot_schedules`
  - `spot_id`, `playlist_id` ou `radio_point_id`
  - `interval_seconds`
  - `start_time`, `end_time`
  - `starts_at`, `ends_at`
  - `priority`, `is_active`
- `audio_playback_events`
  - `device_id`, `playlist_id`, `track_id`, `spot_id`
  - `event_type`, `started_at`, `ended_at`, `result`

## Decisoes pendentes

- `radio_points`: criar entidade propria agora ou mapear inicialmente para `device.audio_playlist_id`.
- Uma faixa pode pertencer a varias pastas: sim, via N:N.
- Playlist de audio deve permitir faixa repetida: recomendado sim, via `audio_playlist_items`.
