# SPEC 006 — Contrato de API

## Endpoints existentes (estendidos)

### `GET /devices/{device_id}/playlist`

Response ganha bloco `osd_config`:

```json
{
  "device_name": "TV Loja 01",
  "osd_config": {
    "show_current_audio": true,
    "position": "top_right",
    "duration_seconds": 8,
    "opacity": 0.6,
    "font_size": "medium"
  },
  "campaign": {...},
  "media": [...],
  "audio_playlist": {...}
}
```

`osd_config` resolvido com hierarquia device > tenant > default. Sempre presente.

### `POST /devices/{device_id}/heartbeat`

Body ganha campos opcionais:

```json
{
  "config_version": "...",
  "current_campaign_id": "...",
  "current_media_id": "...",
  "current_audio_track_id": "uuid",
  "current_audio_track_name": "Nome da Musica",
  "current_audio_track_started_at": "2026-05-22T10:00:00",
  "playback_status": "playing",
  "storage_used": 12345
}
```

Backend persiste novos campos em `devices.current_audio_track_*`.

Quando audio nao esta tocando, player envia `current_audio_track_id: null`. Backend zera as colunas.

### `GET /devices/{device_id}` (admin)

Response inclui:

```json
{
  "id": "...",
  "name": "...",
  "osd_config_local": {              // configuracao deste device (pode ter NULL)
    "show_current_audio": null,
    "position": null,
    "duration_seconds": null,
    "opacity": null,
    "font_size": null
  },
  "osd_config_effective": {          // resolvida apos hierarquia
    "show_current_audio": true,
    "position": "top_right",
    "duration_seconds": 8,
    "opacity": 0.6,
    "font_size": "medium"
  },
  "current_audio_track_id": "uuid",
  "current_audio_track_name": "Nome",
  "current_audio_track_started_at": "2026-05-22T10:00:00"
}
```

## Endpoints novos

### `PATCH /devices/{device_id}/osd-config`

Autenticacao: admin do tenant.

**Request body** (campos opcionais; null = reset para herancar):

```json
{
  "show_current_audio": true,
  "position": "top_right",
  "duration_seconds": 8,
  "opacity": 0.6,
  "font_size": "medium"
}
```

**Response**: `osd_config_effective` recalculado.

**Side effects**:

- Salva valores no device (incluindo null = reset).
- Invalida cache do device.
- Publica SSE `playlist_invalidated`.

### `PATCH /tenants/{tenant_id}/osd-config`

Autenticacao: super_admin ou admin do tenant.

**Request body** (todos obrigatorios — tenant eh topo da hierarquia):

```json
{
  "show_current_audio": true,
  "position": "top_right",
  "duration_seconds": 8,
  "opacity": 0.6,
  "font_size": "medium"
}
```

**Validacoes**:

- `position`: enum.
- `duration_seconds`: 0-3600.
- `opacity`: 0.0-1.0.
- `font_size`: enum.

**Response**: configuracao salva.

**Side effects**:

- Salva valores no tenant.
- Invalida cache de todos os devices do tenant que tem `osd_*` NULL.
- Publica SSE `playlist_invalidated` para cada um.

## Schema Pydantic

### `OSDPosition` e `OSDFontSize`

```python
class OSDPosition(str, Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"

class OSDFontSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
```

### `OSDConfig`

```python
class OSDConfig(BaseModel):
    show_current_audio: bool
    position: OSDPosition
    duration_seconds: int = Field(ge=0, le=3600)
    opacity: float = Field(ge=0.0, le=1.0)
    font_size: OSDFontSize
```

### `OSDConfigUpdate` (para PATCH em device — todos opcionais/nullable)

```python
class DeviceOSDConfigUpdate(BaseModel):
    show_current_audio: bool | None = None
    position: OSDPosition | None = None
    duration_seconds: int | None = Field(None, ge=0, le=3600)
    opacity: float | None = Field(None, ge=0.0, le=1.0)
    font_size: OSDFontSize | None = None
```

### `TenantOSDConfigUpdate` (para PATCH em tenant — todos obrigatorios)

```python
class TenantOSDConfigUpdate(BaseModel):
    show_current_audio: bool
    position: OSDPosition
    duration_seconds: int = Field(ge=0, le=3600)
    opacity: float = Field(ge=0.0, le=1.0)
    font_size: OSDFontSize
```

### `HeartbeatRequest` (estender)

```python
class HeartbeatRequest(BaseModel):
    # ... campos existentes ...
    current_audio_track_id: str | None = None
    current_audio_track_name: str | None = Field(None, max_length=500)
    current_audio_track_started_at: datetime | None = None
```

### `PlayerPlaylistResponse` (estender)

Adicionar `osd_config: OSDConfig` no nivel raiz.

### `DeviceResponse` (estender — admin)

```python
class DeviceResponse(BaseModel):
    # ... campos existentes ...
    osd_config_local: dict           # com nulls
    osd_config_effective: OSDConfig  # resolvido
    current_audio_track_id: str | None
    current_audio_track_name: str | None
    current_audio_track_started_at: datetime | None
```

## SSE

Reusa `playlist_invalidated` quando `osd_config` muda.

Sem evento novo dedicado — a invalidacao de playlist ja forca o player a recarregar e pegar novo `osd_config`.

## Cache busting

- Mudanca em `device.osd_*`: invalida cache desse device.
- Mudanca em `tenant.osd_*`: invalida cache de todos os devices do tenant com `osd_*` NULL no campo equivalente.

Implementacao: helper `find_devices_inheriting_osd_field(tenant, field_name)` retorna ids de devices afetados.

## Compatibilidade

- Player legado sem suporte a `osd_config`: ignora campo, mostra OSD existente (apenas nome da midia visual).
- Player legado nao envia `current_audio_track_*` no heartbeat: colunas DB permanecem NULL.
- Tenant criado antes desta SPEC: defaults setados via migration.
- Device criado antes desta SPEC: campos NULL → herdam tenant.
