# SPEC 016 — API Contract

Status: implementada

## `GET /api/v1/audio/tracks` (campo novo)

Parâmetros de query adicionados:

```
include_archived: bool = false
```

Comportamento:

- `status` não informado + `include_archived=false` (default): exclui `status=archived`.
- `status` não informado + `include_archived=true`: nenhum filtro de status (retorna todos).
- `status=<valor>` informado: filtra exatamente por esse valor, **independente** de `include_archived`.

Exemplos:

```http
GET /audio/tracks                          → exclui arquivadas (NOVO comportamento)
GET /audio/tracks?include_archived=true     → inclui arquivadas (comportamento antigo)
GET /audio/tracks?status=archived           → só arquivadas (já existia, inalterado)
GET /audio/tracks?status=active             → só ativas (já existia, inalterado)
```

## `AudioTrackResponse` (campo novo)

```json
{
  "id": "track-uuid",
  "name": "Jingle Promoção",
  "status": "archived",
  "archived_at": "2026-06-18T12:00:00",
  "...": "demais campos inalterados"
}
```

`archived_at` é `null` quando `status` não é `archived`.

## `DELETE /api/v1/audio/tracks/{track_id}` (novo erro)

Resposta de sucesso inalterada:

```json
{ "message": "Faixa de áudio removida com sucesso" }
```

Novo erro quando a faixa está em uso:

```http
HTTP 409 Conflict
```

```json
{
  "detail": "Faixa em uso e não pode ser excluída definitivamente (playlists: 2, pastas: 0, spots: 1). Arquive a faixa ou remova-a dos locais que a utilizam antes de excluir."
}
```

Antes desta SPEC, a mesma situação resultava em `500 Internal Server Error` (IntegrityError do Postgres por violação da constraint `RESTRICT`), sem mensagem útil para o frontend exibir.

## `PUT /api/v1/audio/tracks/{track_id}` (comportamento estendido, sem mudança de payload)

Nenhum campo novo no payload de entrada. Mudança é só no efeito colateral: ao enviar `{"status": "archived"}`, o backend agora também seta `archived_at`. Ao enviar `{"status": "active"}` ou `{"status": "inactive"}`, `archived_at` é limpo.

## Migration

`backend/alembic/versions/20260618_1200_audio_track_archived_at.py`:

- `ADD COLUMN archived_at TIMESTAMP NULL` em `audio_tracks`.
- Backfill: `UPDATE audio_tracks SET archived_at = now() WHERE status = 'archived' AND archived_at IS NULL`.

Migration é puramente aditiva — nenhuma coluna existente é alterada/removida, `downgrade()` reverte limpo.

## Compatibilidade

- Todos os call sites existentes que já passavam `status=active` continuam recebendo exatamente o mesmo resultado.
- Clientes que chamavam `GET /audio/tracks` sem nenhum filtro de status e esperavam ver arquivadas (comportamento antigo, com bug) precisam adicionar `include_archived=true` explicitamente — única mudança de contrato que pode afetar integrações externas, documentada aqui propositalmente.
