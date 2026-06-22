# SPEC 016 — Design

Status: implementada

## Fluxo esperado (listagem)

```text
Qualquer consumidor de listarFaixas() (seletor de playlist, rádio, campanha,
spots, ou a tela de gerenciamento)
  -> GET /audio/tracks?...
  -> Backend monta query:
       SE status foi passado explicitamente:
         -> filtra por esse status exato (comportamento já existente, intocado)
       SENAO SE include_archived=false (default):
         -> filtra status != 'archived' (NOVO — fecha o leak)
       SENAO (include_archived=true):
         -> nenhum filtro de status adicional
  -> Retorna lista já filtrada
```

## Fluxo esperado (arquivar/restaurar)

```text
UI (FaixasAudio.jsx) clica Arquivar/Restaurar
  -> atualizarFaixa(id, { status: "archived" | "active" })
  -> PUT /audio/tracks/{id}
  -> crud_audio_track.update() [override]:
       SE "status" está no payload:
         -> status == "archived": archived_at = now()
         -> caso contrário: archived_at = None
       -> delega para CRUDBase.update() (lógica genérica de PUT, intocada)
  -> Resposta inclui archived_at atualizado
```

## Fluxo esperado (excluir definitivamente)

```text
UI clica "Excluir definitivamente" (só visível quando já arquivada)
  -> Confirmação explícita ("não pode ser desfeita")
  -> DELETE /audio/tracks/{id}
  -> crud_audio_track.get_in_use_references(track_id):
       conta AudioPlaylistItem + AudioFolderTrack + AudioSpot referenciando a faixa
  -> SE in_use:
       -> 409 Conflict, mensagem com contagem por tipo
  -> SENAO:
       -> remove arquivo físico (se houver)
       -> crud_audio_track.remove() -> hard DELETE real (intocado)
```

## Decisão técnica: por que `archived_at` sincroniza no `update()` genérico, não só em `update_status()`

A auditoria revelou que o fluxo real usado pela UI (`atualizarFaixa` → `PUT /audio/tracks/{id}` → `crud_audio_track.update()`) é diferente do endpoint dedicado `PATCH /audio/tracks/{id}/status` (que usa `update_status()`). Sincronizar `archived_at` apenas em `update_status()` teria sido um fix que nunca dispara na prática, porque a UI não usa esse endpoint.

Por isso a lógica foi movida para um override de `CRUDAudioTrack.update()`, que intercepta qualquer mudança de `status` (vinda de `PUT` genérico ou de `update_status()`, que agora delega para `update()` internamente) e sincroniza `archived_at` de forma centralizada — independente de qual call site iniciou a mudança.

## Decisão técnica: checagem de uso via contagem direta, não via `try/except IntegrityError`

A alternativa mais simples seria deixar o `DELETE` tentar normalmente e capturar `IntegrityError` da constraint `RESTRICT` existente, convertendo para uma mensagem amigável. Isso foi descartado porque:

- Não permite informar *quais* tipos de referência existem (playlist vs pasta vs spot) sem fazer parsing de mensagem de erro do driver do banco (fragio e específico do Postgres).
- Faz uma operação de escrita (que falha) antes de saber se ela vai falhar — desperdício e, em alguns drivers, pode deixar a transação em estado inconsistente exigindo rollback explícito.

Em vez disso, `get_in_use_references()` faz 3 `COUNT()` simples antes do delete, permitindo uma mensagem precisa e nenhuma tentativa de escrita malsucedida.

## Decisão técnica: `include_archived` como flag explícita, não inferida de `status`

Foi considerado fazer `status=archived` implicar automaticamente "mostrar arquivadas" e qualquer outro valor escondê-las, sem uma flag separada. Isso foi descartado porque um cliente futuro poderia querer listar "todas, inclusive arquivadas, mas sem filtrar por status específico" (ex.: a própria tela de gerenciamento, que aplica o filtro de status no client, não no servidor). A flag `include_archived` cobre esse caso sem ambiguidade.

## Pontos de auditoria realizados

- [x] Confirmar que `DELETE /audio/tracks/{id}` já fazia hard delete real (`crud_audio_track.remove()` → `db.delete()`) — não era um bug de "exclusão fake".
- [x] Confirmar que `GET /audio/tracks` não filtrava arquivadas por padrão — causa raiz do leak relatado.
- [x] Confirmar que o endpoint de player (`backend/api/v1/devices.py`, função `_audio_playlist_track_payload`) já filtra por `status == "active"` corretamente — sem mudança necessária.
- [x] Confirmar `ondelete="RESTRICT"` nas 3 tabelas que referenciam `AudioTrack` (`AudioFolderTrack`, `AudioPlaylistItem`, `AudioSpot`).
- [x] Confirmar que a UI (`FaixasAudio.jsx`) usa `PUT` genérico para arquivar, não o `PATCH /status` dedicado — guiou a decisão de onde sincronizar `archived_at`.
- [x] Confirmar ausência de UI de restaurar individual e de excluir definitivamente — apenas "Arquivar" existia, rotulado incorretamente como exclusão.

## Arquivos impactados

- `backend/core/models.py` — campo `archived_at` em `AudioTrack`.
- `backend/core/schemas_completos.py` — `archived_at` em `AudioTrackResponse`.
- `backend/api/v1/audio/tracks.py` — `include_archived` em `GET /`, checagem de uso em `DELETE /{id}`.
- `backend/crud/entidades/crud_audio_track.py` — override de `update()` (sincroniza `archived_at`), `update_status()` delega para `update()`, novo `get_in_use_references()`.
- `backend/alembic/versions/20260618_1200_audio_track_archived_at.py` — migration aditiva com backfill.
- `frontend/src/pages/FaixasAudio.jsx` — separação de ações Arquivar/Restaurar/Excluir, dois diálogos de confirmação distintos, `include_archived=true` na query da própria tela.
- `backend/tests/test_audio_track_archive_delete.py` — testes novos.

Não foram necessárias mudanças em:

- `backend/api/v1/devices.py` — resolução de playlist do player já correta.
- `frontend/src/components/audio/AudioTrackSelector.jsx` — recebe `tracks` via prop do componente pai, já corrigido na origem.
- `frontend/src/pages/Spots.jsx`, `PlaylistDetalhe.jsx`, `AudioPlaylistsFormModal.jsx`, `CampaignFormModal.jsx` — já passavam `status: "active"` explicitamente, comportamento preservado.

## Riscos

- `PlaylistsSonoras.jsx` calcula duração total de uma playlist buscando faixas por id em `tracks` (agora sem arquivadas por padrão); se uma faixa referenciada por `track_ids` foi arquivada, `getTotalDuration` vai subestimar o total (a faixa não é encontrada na lista). Aceitável: é uma exibição secundária (duração estimada), não afeta playback real, e arguably correto (uma faixa arquivada não deveria contar para "o que está tocando").
- Migration tem um `UPDATE` de backfill (`archived_at = now()` para faixas já arquivadas) — a data exata do arquivamento original é desconhecida, então o backfill usa o momento da migration como aproximação. Aceitável para fins de auditoria/UI, documentado explicitamente no comentário da migration.
- Migration não aplicada em produção (VPS) nesta sessão — mesma situação já registrada nas SPECs anteriores.
