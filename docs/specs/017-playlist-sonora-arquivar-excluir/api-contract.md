# SPEC 017 — API Contract

Status: implementada

## `GET /api/v1/audio/playlists` (campo novo)

```
include_archived: bool = false
```

Mesma semântica da SPEC 016 (`GET /audio/tracks`):

```http
GET /audio/playlists                          → exclui arquivadas (NOVO)
GET /audio/playlists?include_archived=true     → inclui arquivadas
GET /audio/playlists?status=archived           → só arquivadas (já existia)
GET /audio/playlists?status=active             → só ativas (já existia)
```

## `AudioPlaylistResponse` (campo novo)

```json
{
  "id": "playlist-uuid",
  "name": "Playlist Loja Centro",
  "status": "archived",
  "archived_at": "2026-06-18T13:00:00",
  "...": "demais campos inalterados"
}
```

## `DELETE /api/v1/audio/playlists/{playlist_id}` (novo erro)

```http
HTTP 409 Conflict
```

```json
{
  "detail": "Playlist em uso e não pode ser excluída definitivamente (dispositivos: 2, campanhas: 1). Desvincule a playlist desses locais ou arquive-a antes de excluir."
}
```

Antes desta SPEC: `500 Internal Server Error` (violação de constraint implícita do Postgres), sem mensagem útil.

## `GET /api/v1/audio/devices/{device_id}/playlist` (comportamento estendido)

Endpoint secundário (não usado pelo frontend atual, mas registrado e alcançável). Novo comportamento:

```http
HTTP 404 Not Found
```

```json
{ "detail": "Playlist de áudio arquivada/inativa" }
```

quando a playlist do device tem `status != "active"`. Antes desta SPEC, retornava o conteúdo da playlist normalmente, mesmo arquivada.

## Migration

`backend/alembic/versions/20260618_1300_audio_playlist_archived_at.py`:

- `ADD COLUMN archived_at TIMESTAMP NULL` em `audio_playlists`.
- Backfill: `UPDATE audio_playlists SET archived_at = now() WHERE status = 'archived' AND archived_at IS NULL`.

Aditiva, `downgrade()` reverte limpo.

## Compatibilidade

- Mesma ressalva da SPEC 016: clientes que chamavam `GET /audio/playlists` sem filtro de status, esperando ver arquivadas, precisam adicionar `include_archived=true` explicitamente.
