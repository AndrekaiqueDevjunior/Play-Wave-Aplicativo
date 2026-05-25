# SPEC 004 — Contrato de API

## Headers

### Todas as rotas autenticadas por device

| Header | Obrigatorio | Tipo | Descricao |
|---|---|---|---|
| `X-Device-Token` | sim | string | Token persistido no pareamento |
| `X-Device-Token-Version` | sim (compat 1 release) | string (int) | Version atual do token segundo o player |

**Compat-period:** Header ausente eh tratado como `version=1` por 1 release com warning no log do backend. Apos esse periodo: 401 com `error_code=TOKEN_VERSION_REQUIRED`.

### Resposta padrao de erro 401/403

```json
{
  "detail": "human-readable message",
  "error_code": "TOKEN_VERSION_MISMATCH",
  "current_version": 7,
  "received_version": 5
}
```

`error_code` enum:

- `TOKEN_REVOKED`
- `TOKEN_VERSION_MISMATCH`
- `TOKEN_VERSION_REQUIRED`
- `REQUIRES_REPAIRING`
- `DEVICE_BLOCKED`
- `PAIRING_CODE_EXPIRED`

## Endpoints existentes (mudancas)

### `POST /devices/pair-request`

Sem mudanca.

### `GET /devices/by-code/{code}/status`

**Response estendido** quando `status=paired`:

```json
{
  "status": "paired",
  "device_id": "uuid",
  "device_token": "abc...",
  "token_version": 1,
  "pairing_version": 1,
  "device_name": "TV Loja 01"
}
```

`token_version` e `pairing_version` adicionados — player precisa persistir.

### `POST /devices/{device_id}/pair-confirm`

Sem mudanca. Internamente registra evento `paired` ou `re_paired` em `device_pairing_events`.

### `POST /devices/{device_id}/pairing-code/regenerate`

**Request body** (estendido, opcional):

```json
{
  "reason": "Suspeita de cracha clonado"
}
```

**Response**:

```json
{
  "pairing_code": "TV-X7K2",
  "pairing_version": 2,
  "token_version": 2,
  "revoked_sessions_count": 1,
  "previous_pairing_code": "TV-AB12"
}
```

**Side effects**:

- `device.device_token = NULL`.
- Incrementa `pairing_version` e `token_version`.
- `requires_repairing = TRUE`.
- Revoga DeviceSessions.
- Insere `device_pairing_events` (`event_type=code_regenerated`).
- Publica SSE `pairing:revoked` no canal do device.

### `POST /devices/{device_id}/revoke-token` (legado)

Mantido. Comportamento: alias de `force-repair` sem `reason`.

### `GET /devices/{device_id}/sessions/active`

Sem mudanca. Frontend usa antes do modal de confirmacao de regenerate para mostrar impacto.

## Endpoints novos

### `POST /devices/{device_id}/force-repair`

Autenticacao: admin.

**Request body**:

```json
{
  "reason": "Player suspeito sem identificacao"
}
```

**Response**:

```json
{
  "token_version": 3,
  "revoked_sessions_count": 1,
  "pairing_code_unchanged": "TV-X7K2"
}
```

**Side effects**:

- `device.device_token = NULL`.
- Incrementa `token_version`.
- `requires_repairing = TRUE`.
- NAO altera `pairing_code` nem `pairing_version`.
- Revoga DeviceSessions.
- Insere `device_pairing_events` (`event_type=force_repair`).
- Publica SSE `pairing:revoked`.

### `GET /devices/{device_id}/pairing-events`

Autenticacao: admin.

**Query params**:

- `limit` (default 50, max 200).
- `event_type` opcional para filtrar.

**Response**:

```json
{
  "items": [
    {
      "id": "uuid",
      "event_type": "code_regenerated",
      "previous_token_version": 1,
      "new_token_version": 2,
      "previous_pairing_version": 1,
      "new_pairing_version": 2,
      "previous_pairing_code": "TV-AB12",
      "new_pairing_code": "TV-X7K2",
      "requested_by": {"id": "uuid", "name": "admin@playwave.com"},
      "reason": "Suspeita de cracha clonado",
      "metadata": {"revoked_sessions_count": 1},
      "created_at": "2026-05-22T10:00:00"
    }
  ],
  "total": 12
}
```

## Eventos SSE

Canal: `pw:device:{device_id}:events`

### `pairing:revoked`

Payload:

```json
{
  "event": "pairing:revoked",
  "reason": "code_regenerated",
  "revoked_at": "2026-05-22T10:00:00"
}
```

`reason` valores: `code_regenerated`, `force_repair`, `token_revoked`.

Player escuta e dispara `forceRepair(payload.reason)` imediatamente.

## Schema Pydantic

### Estender em `schemas_completos.py`

```python
class PairCodeStatusResponse(BaseModel):
    status: Literal["pending", "paired", "expired"]
    device_id: str | None = None
    device_token: str | None = None
    token_version: int | None = None   # NOVO
    pairing_version: int | None = None # NOVO
    device_name: str | None = None
    expires_at: datetime | None = None


class RegenerateCodeRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class RegenerateCodeResponse(BaseModel):
    pairing_code: str
    pairing_version: int
    token_version: int
    revoked_sessions_count: int
    previous_pairing_code: str | None = None


class ForceRepairRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class ForceRepairResponse(BaseModel):
    token_version: int
    revoked_sessions_count: int
    pairing_code_unchanged: str


class DevicePairingEventResponse(BaseModel):
    id: str
    event_type: str
    previous_token_version: int | None
    new_token_version: int | None
    previous_pairing_version: int | None
    new_pairing_version: int | None
    previous_pairing_code: str | None
    new_pairing_code: str | None
    requested_by: dict | None  # {id, name}
    reason: str | None
    metadata: dict | None
    created_at: datetime
```

## Erros padronizados (FastAPI exception handler)

Centralizar criacao de respostas de erro autenticacao em helper:

```python
def auth_error(error_code: str, detail: str, status: int = 401, **extra):
    return JSONResponse(
        status_code=status,
        content={"detail": detail, "error_code": error_code, **extra},
    )
```

Usar em todas as falhas de `get_device_by_token`.

## Compatibilidade

- Player sem `X-Device-Token-Version`: compat-period 1 release, depois 401.
- Cliente sem `error_code` parse: continua funcionando porque `detail` permanece humano.
- Endpoint `revoke-token` continua disponivel como atalho.
- `regenerate-code` mantem comportamento + retorna mais campos.
