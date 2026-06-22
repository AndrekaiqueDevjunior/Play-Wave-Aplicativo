# SPEC 018 — API Contract

Status: implementada

## `GET /api/v1/media` (campo novo)

```
include_archived: bool = false
```

Mesma semântica das SPECs 016/017:

```http
GET /media                          → exclui arquivadas (NOVO)
GET /media?include_archived=true     → inclui arquivadas
GET /media?status=archived           → só arquivadas
```

## `MediaResponse` (campo novo)

```json
{
  "id": "media-uuid",
  "name": "Banner Promoção",
  "status": "archived",
  "archived_at": "2026-06-18T14:00:00",
  "...": "demais campos inalterados"
}
```

## `DELETE /api/v1/media/{media_id}` (checagem estendida)

Comportamento novo: bloqueia com 409 quando a mídia está em `CampaignPlaylistItem`, **mesmo com `force=true`**:

```http
HTTP 409 Conflict
```

```json
{
  "detail": "Mídia em uso em playlists de campanha (2 item(s)) e não pode ser excluída definitivamente. Remova-a da playlist da campanha antes de excluir."
}
```

O comportamento existente (checagem dos campos legados `Campaign.media_ids`/`media_order`, com `force=true` desvinculando-os automaticamente) é mantido sem alteração — a checagem nova roda **antes** dessa, e é a única que nunca é contornável por `force`.

## `POST /api/v1/media/bulk-archive` (novo)

```http
POST /media/bulk-archive
```

```json
{
  "media_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

Resposta:

```json
{
  "requested": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [
    { "media_id": "uuid-1", "success": true, "reason": null },
    { "media_id": "uuid-2", "success": true, "reason": null },
    { "media_id": "uuid-3", "success": false, "reason": "Mídia não encontrada" }
  ]
}
```

`media_ids`: lista de 1 a 200 itens. Arquivar nunca falha por "em uso" — só por mídia não encontrada ou sem permissão de tenant.

## `POST /api/v1/media/bulk-delete` (novo)

```http
POST /media/bulk-delete
```

```json
{
  "media_ids": ["uuid-1", "uuid-2"]
}
```

Resposta (mesmo formato de `bulk-archive`):

```json
{
  "requested": 2,
  "succeeded": 1,
  "failed": 1,
  "results": [
    { "media_id": "uuid-1", "success": true, "reason": null },
    { "media_id": "uuid-2", "success": false, "reason": "Em uso em 3 item(s) de playlist de campanha" }
  ]
}
```

Sem parâmetro `force` — mídias vinculadas (relacional ou legado) são sempre reportadas como falha, nunca desvinculadas automaticamente.

## Migration

`backend/alembic/versions/20260618_1400_media_archived_at.py`:

- `ALTER TYPE mediastatus ADD VALUE IF NOT EXISTS 'archived'`.
- `ADD COLUMN archived_at TIMESTAMP NULL` em `media`.

Sem backfill: o valor `archived` não existia antes desta migration, então não há linhas pré-existentes com esse status para retroagir o timestamp.

## Compatibilidade

- Mesma ressalva das SPECs 016/017: clientes que chamavam `GET /media` sem filtro de status, esperando ver arquivadas (cenário só possível após esta SPEC, já que `archived` não existia antes), precisam adicionar `include_archived=true` explicitamente.
- `DELETE /media/{id}?force=true` continua funcionando para o caso legado (`Campaign.media_ids`/`media_order`), mas passa a falhar (novo, antes não verificado) quando há `CampaignPlaylistItem` vinculado.
