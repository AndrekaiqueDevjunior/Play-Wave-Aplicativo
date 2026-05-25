# SPEC 001 — API Contract

## Endpoints encontrados

### Midias

Arquivo: `backend/api/v1/media.py`

- `GET /media/`
- `GET /media/{media_id}`
- `POST /media/`
- `POST /media/upload`
- `PUT /media/{media_id}`
- `GET /media/{media_id}/usage`
- `GET /media/{media_id}/versions`
- `POST /media/{media_id}/replace-file`
- `DELETE /media/{media_id}`
- `PATCH /media/{media_id}/status`
- `GET /media/statistics/overview`
- `GET /media/available/list`
- `GET /media/processing/list`
- `GET /media/error/list`
- `GET /media/by-type/{media_type}`
- `GET /media/by-category/{category}`

### Campanhas

Arquivo: `backend/api/v1/campaigns.py`

- `GET /campaigns/`
- `GET /campaigns/{campaign_id}`
- `POST /campaigns/`
- `PUT /campaigns/{campaign_id}`
- `DELETE /campaigns/{campaign_id}`
- `PATCH /campaigns/{campaign_id}/status`
- `GET /campaigns/by-media/{media_id}`
- `POST /campaigns/{campaign_id}/publish`
- `POST /campaigns/{campaign_id}/pause`
- `POST /campaigns/{campaign_id}/resume`

### Player/Dispositivos

Arquivo: `backend/api/v1/devices.py`

- `GET /devices/{device_id}/playlist`
- `POST /devices/{device_id}/heartbeat`
- `POST /devices/{device_id}/playback-log`
- `GET /devices/{device_id}/commands/pending`
- `GET /devices/{device_id}/playlist/updates`
- `POST /devices/{device_id}/commands/{command_id}/ack`

## Contrato: POST /media/upload

Tipo: `multipart/form-data`

Campos:

- `file`: arquivo obrigatorio.
- `name`: string obrigatoria.
- `media_type`: `image | video | audio | external_url`.
- `description`: opcional.
- `category`: opcional.
- `tags`: string CSV opcional.
- `duration`: legado/opcional.
- `display_duration_seconds`: opcional.
- `starts_at`: opcional.
- `ends_at`: opcional.
- `notes`: opcional.

Resposta esperada: `MediaResponse`.

Regras:

- Video/audio devem calcular `duration_seconds`.
- Imagem/link devem receber `display_duration_seconds` ou padrao.
- Deve criar `media_versions`.

## Contrato: PUT /media/{media_id}

Tipo: JSON.

Campos editaveis:

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

Regras:

- Validar periodo.
- Sincronizar `duration` legado quando necessario.
- Atualizacao que afeta player deve invalidar cache de campanhas afetadas.

## Contrato: POST /media/{media_id}/replace-file

Tipo: `multipart/form-data`

Campos:

- `file`: arquivo obrigatorio.

Resposta: `MediaResponse`.

Regras obrigatorias:

- Nao criar nova midia.
- Manter o mesmo `media_id`.
- Recalcular `file_hash`, `file_size`, `mime_type`, `duration_seconds`.
- Incrementar `file_version`.
- Criar nova `media_versions`.
- Atualizar campanhas afetadas.
- Invalidar cache dos players afetados.

## Contrato: GET /media/{media_id}/usage

Resposta esperada:

```json
{
  "media_id": "uuid",
  "usage_count": 2,
  "campaigns": [
    {
      "id": "uuid",
      "name": "Campanha Maio",
      "status": "active",
      "config_version": "uuid"
    }
  ]
}
```

## Contrato: GET /media/{media_id}/versions

Resposta esperada: lista de `MediaVersionResponse`.

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

## Contrato: GET /devices/{device_id}/playlist

Payload de midia esperado:

```json
{
  "id": "uuid",
  "media_id": "uuid",
  "name": "Oferta Maio",
  "type": "video",
  "file_url": "/uploads/media/oferta.mp4",
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
```

## Endpoints nao existentes que podem ser criados depois

- `GET /media/{media_id}/processing-status`
- `POST /media/{media_id}/regenerate-thumbnail`
- `GET /devices/{device_id}/cache`
- `POST /devices/{device_id}/cache/clear-media/{media_id}`
- `POST /player/media-error`

Esses endpoints nao devem ser implementados nesta fase sem nova task aprovada.
