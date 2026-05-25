# SPEC 005 — Contrato de API

## Endpoints existentes (estendidos)

### `GET /devices/{device_id}/playlist`

**Response** ganha campos novos:

```json
{
  "device_name": "TV Loja 01",
  "campaign": {
    "id": "uuid",
    "name": "Maio Promo",
    "config_version": "uuid",
    "video_muted": false,
    "audio_policy_default": "auto",
    "audio_fade_ms": 200,
    "loop_count": null,
    "start_date": "2026-05-01T00:00:00",
    "end_date": null
  },
  "media": [
    {
      "id": "uuid",
      "name": "Promo Maio Video 1",
      "type": "video",
      "file_url": "/uploads/...",
      "duration_seconds": 30,
      "audio_policy_effective": "auto",
      "has_audio": true
    },
    {
      "id": "uuid",
      "name": "Banner Estatico",
      "type": "image",
      "file_url": "/uploads/...",
      "duration_seconds": 10,
      "audio_policy_effective": "radio_only",
      "has_audio": false
    }
  ],
  "audio_playlist": {
    "id": "uuid",
    "name": "Manha",
    "tracks": [...]
  }
}
```

Campos novos por midia:

- `audio_policy_effective`: resultado do resolver hierarquico. Sempre presente.
- `has_audio`: boolean ou null (raro — nullable somente em videos antigos sem deteccao).

Campos novos na campanha:

- `audio_policy_default`: politica resolvida no nivel campanha+device+tenant (fallback se midia nao tiver override).
- `audio_fade_ms`: inteiro (default 200).

`campaign.video_muted` mantido por compat. Players novos ignoram em favor de `audio_policy_effective`.

## Endpoints novos

### `POST /media/{media_id}/recompute-audio-detection`

Autenticacao: admin do tenant.

**Action:** Re-roda `ffprobe` no arquivo da midia e atualiza `has_audio`.

**Response:**

```json
{
  "media_id": "uuid",
  "has_audio": true,
  "detected_at": "2026-05-22T10:00:00"
}
```

Erros:

- 404 se midia nao existe.
- 400 se tipo nao eh video.
- 500 se `ffprobe` falha (com `error_code = FFPROBE_FAILED`).

## Endpoints alterados (admin)

### `PUT /media/{id}`

Aceita novos campos:

```json
{
  "audio_policy": "auto" | "radio_only" | ... | null,
  "has_audio": true | false | null
}
```

- `audio_policy` nullable: NULL = herda da campanha.
- `has_audio` editavel manualmente (override do detector).

### `PUT /campaigns/{id}`

Aceita:

```json
{
  "audio_policy": "auto" | ... | null
}
```

Setar `audio_policy` invalida cache dos devices afetados (publica SSE `playlist_invalidated`).

### `PUT /devices/{id}`

Aceita:

```json
{
  "audio_policy_default": "auto" | ... | null
}
```

### `PATCH /tenants/{id}/audio-config` (novo endpoint dedicado)

```json
{
  "audio_policy_default": "auto",
  "audio_fade_ms": 250
}
```

Validacoes:

- `audio_fade_ms` entre 0 e 2000.
- `audio_policy_default` no enum.

Autenticacao: super_admin ou admin do tenant.

## Schema Pydantic

### `AudioPolicy` enum

```python
from enum import Enum

class AudioPolicy(str, Enum):
    AUTO = "auto"
    RADIO_ONLY = "radio_only"
    MEDIA_AUDIO_ONLY = "media_audio_only"
    MIX = "mix"
    MUTED_VIDEO_WITH_RADIO = "muted_video_with_radio"
```

### `MediaUpdate` (estender)

```python
class MediaUpdate(BaseModel):
    # ... campos existentes ...
    audio_policy: AudioPolicy | None = None
    has_audio: bool | None = None
```

### `MediaResponse` (estender)

```python
class MediaResponse(BaseModel):
    # ... campos existentes ...
    audio_policy: AudioPolicy | None = None
    has_audio: bool | None = None
```

### `MediaPlayerItem` (novo, para o payload do player)

```python
class MediaPlayerItem(BaseModel):
    id: str
    name: str
    type: str
    file_url: str
    duration_seconds: int | None
    display_duration_seconds: int | None
    audio_policy_effective: AudioPolicy
    has_audio: bool
    # ... outros campos ja existentes do payload do player ...
```

### `CampaignUpdate` (estender)

```python
class CampaignUpdate(BaseModel):
    # ... campos existentes ...
    audio_policy: AudioPolicy | None = None
```

### `CampaignResponse` (estender)

Adicionar `audio_policy: AudioPolicy | None`.

### `CampaignPlayerInfo` (novo, no payload do player)

```python
class CampaignPlayerInfo(BaseModel):
    id: str
    name: str
    config_version: str
    video_muted: bool                                # legado
    audio_policy_default: AudioPolicy                # resolvido
    audio_fade_ms: int
    loop_count: int | None
    start_date: datetime | None
    end_date: datetime | None
```

### `DeviceUpdate` (estender)

Adicionar `audio_policy_default: AudioPolicy | None`.

### `TenantAudioConfigUpdate` (novo)

```python
class TenantAudioConfigUpdate(BaseModel):
    audio_policy_default: AudioPolicy
    audio_fade_ms: int = Field(ge=0, le=2000)
```

### `RecomputeAudioDetectionResponse`

```python
class RecomputeAudioDetectionResponse(BaseModel):
    media_id: str
    has_audio: bool
    detected_at: datetime
```

## Eventos SSE

Sem evento novo. Reusa `playlist_invalidated` quando admin muda `audio_policy` em qualquer nivel.

## Cache busting

Mudanca de `audio_policy` em qualquer nivel (tenant/device/campaign/media) precisa:

1. Incrementar `campaign.config_version` das campanhas afetadas.
2. Invalidar `device_playlist:{device_id}` em Redis.
3. Publicar SSE `playlist_invalidated` para cada device afetado.

Determinar "afetados":

- Mudanca em `tenant.audio_policy_default`: todas as campanhas do tenant que tem `audio_policy=NULL`.
- Mudanca em `device.audio_policy_default`: todas as campanhas associadas a este device com `audio_policy=NULL`.
- Mudanca em `campaign.audio_policy`: campanha e devices vinculados.
- Mudanca em `media.audio_policy`: todas as campanhas que usam esta midia.
- Mudanca em `media.has_audio`: todas as campanhas que usam esta midia E tem politica `auto`.

## Compatibilidade

- Player legado sem suporte a `audio_policy_effective` continua usando `campaign.video_muted`.
- Player novo prioriza `audio_policy_effective`, ignora `video_muted`.
- Tenant antigo sem `audio_policy_default` recebe `auto` (default DDL).
- Campos `audio_policy` nullable em todos os niveis exceto tenant.
