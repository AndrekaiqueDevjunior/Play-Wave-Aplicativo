# SPEC 011 — API Contract

Status: diagnostico inicial concluido

## Endpoints reais encontrados

Esta SPEC deve preferir endpoints ja existentes. A auditoria inicial indica que a primeira correcao pode ser feita sem endpoint novo.

### Solicitar/renovar codigo de pareamento

```http
POST /api/v1/devices/pair-request
```

Usado por `frontend/src/pages/Player.jsx` quando `phase === "waiting"`.

### Consultar status do pareamento

```http
GET /api/v1/devices/by-code/{code}/status
```

Retorna `device_id`, `device_token`, `token_version` e `pairing_version` quando pareado.

### Buscar playlist/config do player

```http
GET /api/v1/devices/{device_id}/playlist
```

Autenticacao:

```http
X-Device-Token: ...
X-Device-Token-Version: ...
```

Esse endpoint ja funciona como revalidacao pratica da sessao: se token ou versao forem invalidos, o backend retorna erro estruturado.

### Heartbeat do player

```http
POST /api/v1/devices/{device_id}/heartbeat
```

Request real usado pelo Player:

```json
{
  "timestamp": "2026-06-15T12:00:00.000Z",
  "status": "online",
  "player_version": "3.1.0",
  "ip_address": null,
  "storage_used": 0,
  "current_campaign_id": null,
  "current_config_version": null,
  "current_media_id": null,
  "current_media_name": null,
  "current_audio_track_id": null,
  "current_audio_track_name": null,
  "current_audio_track_started_at": null,
  "last_error": null,
  "playback_status": "playing"
}
```

Response real:

```json
{
  "ok": true,
  "is_blocked": false,
  "config_version": null,
  "has_update": false,
  "playlist_updated": false,
  "pending_commands": 0,
  "server_time": "2026-06-15T12:00:00.000000"
}
```

## Endpoint novo opcional

Nao criar inicialmente. Se a implementacao mostrar que `GET /playlist` + `POST /heartbeat` nao cobrem revalidacao de boot, avaliar endpoint separado em uma revisao da SPEC.

## Erros reais esperados

- `TOKEN_REVOKED`
- `DEVICE_BLOCKED`
- `REQUIRES_REPAIRING`
- `TOKEN_VERSION_REQUIRED`
- `TOKEN_VERSION_MISMATCH`

## Lacuna de contrato

O heartbeat atual nao tem campo `boot_mode`. Para fechar a SPEC sem migration, o evento de boot pode ficar inicialmente em log local/console e o backend continua registrando `last_seen_at` no primeiro heartbeat.

## Compatibilidade

- Se ja existir endpoint de sync que tambem atualiza `last_seen_at`, reaproveitar.
- Se ja existir endpoint de pairing/reconnect, adaptar o contrato real em vez de duplicar.
- Backend deve manter respostas explicitas para diferenciar rede indisponivel, token expirado e pareamento revogado.

