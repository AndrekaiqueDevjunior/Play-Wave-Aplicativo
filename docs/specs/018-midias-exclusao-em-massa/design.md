# SPEC 018 — Design

Status: implementada

## Fluxo esperado (bulk archive)

```text
UI: usuário entra em modo de seleção, marca N mídias, clica "Arquivar (N)"
  -> confirmação
  -> POST /media/bulk-archive { media_ids: [...] }
  -> Para cada media_id:
       _bulk_authorize_media(media_id): busca + checa tenant
       SE erro (não encontrada/sem permissão):
         -> results.append({ media_id, success: false, reason })
       SENAO:
         -> crud_media.update_status(media, "archived") — seta archived_at
         -> results.append({ media_id, success: true })
  -> Resposta: { requested, succeeded, failed, results }
  -> UI: toast com resumo; se houver falhas, lista "nome: motivo"
```

## Fluxo esperado (bulk delete)

```text
UI: usuário marca N mídias, clica "Excluir (N)"
  -> confirmação (texto deixa claro que mídias em uso serão puladas)
  -> POST /media/bulk-delete { media_ids: [...] }
  -> Para cada media_id:
       _bulk_authorize_media(media_id)
       SE erro: results.append(failure)
       SENAO:
         refs = get_in_use_references(media_id)  # CampaignPlaylistItem
         SE refs.campaign_playlist_items > 0:
           -> results.append(failure, motivo="N item(s) de playlist de campanha")
         SENAO:
           used_campaigns = _campaigns_using_media(media_id)  # legado JSON
           SE used_campaigns:
             -> results.append(failure, motivo="N campanha(s) (vínculo legado)")
           SENAO:
             -> remove PlaybackLog/ViewReport, remove arquivo físico, hard delete
             -> results.append(success)
  -> Resposta: { requested, succeeded, failed, results }
```

## Decisão técnica: por que criar `archived_at`/`ARCHIVED` nesta SPEC, e não esperar a SPEC 020

O documento mestre original pede, para mídias em uso: "avisar o usuário... permitir arquivar em vez de excluir". Sem um estado de arquivamento, essa alternativa simplesmente não existe — o único caminho possível seria excluir (bloqueado) ou nada. Adiar para a SPEC 020 deixaria esta SPEC incompleta em relação ao que o documento mestre pede. Confirmado com o usuário: implementar agora, seguindo exatamente o padrão já estabelecido nas SPECs 016/017 (`status` enum + `archived_at` sincronizado via override de `update()`), em vez de inventar um mecanismo novo.

## Decisão técnica: checagem de uso dupla (relacional + legado), e por que isso importa mais aqui que nas SPECs 016/017

Para `AudioTrack`, a checagem de uso (SPEC 016) cobria 3 tabelas de junção, todas relacionais. Para `AudioPlaylist` (SPEC 017), eram FKs diretas em `Device`/`Campaign`. Para `Media`, a auditoria encontrou uma situação mais delicada: **dois sistemas paralelos** referenciam mídia em uma campanha:

1. `CampaignPlaylistItem.media_id` — tabela relacional real, com FK `RESTRICT`, e é o que o player de fato lê para resolver o conteúdo (`backend/api/v1/devices.py`).
2. `Campaign.media_ids`/`Campaign.media_order` — campos JSON legados, mantidos por compatibilidade.

A checagem de uso que já existia (`_campaigns_using_media`, usada pelo `DELETE` individual) só olhava o caminho legado (#2). Isso significava que uma mídia referenciada **apenas** via `CampaignPlaylistItem` (#1) não era detectada pela checagem — a exclusão seguiria adiante e estouraria um `IntegrityError` do Postgres (FK `RESTRICT`) sem nenhuma mensagem amigável. Esse bug já existia antes desta SPEC, mas como o bulk delete reaproveita a mesma lógica de checagem, replicá-lo no bulk significaria multiplicar o problema por N itens de um lote. Por isso `CRUDMedia.get_in_use_references()` foi escrito para checar **ambos** os caminhos, e o `DELETE` individual foi corrigido para usar essa checagem nova também — não só o bulk.

## Decisão técnica: bulk-delete sem parâmetro `force`

O `DELETE /media/{id}` individual tem `force=true`, que desvincula a mídia dos campos legados (`Campaign.media_ids`/`media_order`) antes de excluir. Para o bulk, essa opção foi deliberadamente omitida: desvincular automaticamente uma mídia de N campanhas, para N itens de um lote, é uma mudança de conteúdo muito mais ampla e silenciosa do que fazer isso para um único item de cada vez com o admin observando o resultado. Se o usuário quiser excluir uma mídia vinculada, o fluxo esperado é: arquivar em massa primeiro (não bloqueia), ou desvincular explicitamente da campanha, e só então excluir.

`CampaignPlaylistItem` nunca é auto-removido, nem no `DELETE` individual com `force=true`, nem no bulk — isso é consistente com a decisão já tomada na SPEC 017 (não desvincular automaticamente Device/Campaign de uma playlist).

## Pontos de auditoria realizados

- [x] Confirmar ausência de `ARCHIVED`/`archived_at` no model `Media` — única SPEC das 016-018 que precisou criar a capacidade do zero.
- [x] Confirmar que `DELETE /media/{id}` já faz hard delete real, com checagem de uso incompleta (só `Campaign.media_ids`/`media_order`).
- [x] Confirmar `CampaignPlaylistItem.media_id` com `ondelete="RESTRICT"` — caminho relacional real, não coberto pela checagem antiga.
- [x] Confirmar que `backend/api/v1/devices.py` lê de `CampaignPlaylistItem` para resolver o conteúdo da campanha no player — não precisa de alteração, mas explica por que essa tabela é o caminho que importa de verdade.
- [x] Confirmar ausência total de seleção múltipla em `BibliotecaMidias.jsx`, em contraste com `FaixasAudio.jsx`/`PlaylistsSonoras.jsx` (já corrigidas nas SPECs 016/017).
- [x] Confirmar os 4 call sites de `listarMidias()` que não precisam de `include_archived` (seletores: `agenda.jsx`, `CampanhaPreview.jsx`, `EditorPlaylist.jsx`, `Campanhas.jsx`) — beneficiados automaticamente pelo filtro padrão novo, sem qualquer alteração de código.

## Arquivos impactados

- `backend/core/models.py` — `MediaStatus.ARCHIVED`, campo `archived_at` em `Media`.
- `backend/core/schemas_completos.py` — `MediaStatusEnum.ARCHIVED`, `archived_at` em `MediaResponse`, novos schemas `MediaBulkActionRequest`/`MediaBulkActionItemResult`/`MediaBulkActionResponse`.
- `backend/api/v1/media.py` — `include_archived` em `GET /`, checagem de `CampaignPlaylistItem` em `DELETE /{id}`, novos endpoints `POST /bulk-archive` e `POST /bulk-delete`.
- `backend/crud/entidades/crud_media.py` — override de `update()` (sincroniza `archived_at`), `update_status()` delega para `update()`, novo `get_in_use_references()` (checagem dupla).
- `backend/alembic/versions/20260618_1400_media_archived_at.py` — migration aditiva (novo valor de enum + coluna).
- `frontend/src/api/midias.js` — `arquivarMidiasEmMassa`, `excluirMidiasEmMassa`.
- `frontend/src/pages/BibliotecaMidias.jsx` — modo de seleção, checkboxes (grid e lista), barra de ações em lote, filtro de status, ações individuais de arquivar/restaurar, dois `ConfirmDialog` para as ações em massa.
- `backend/tests/test_media_bulk_archive_delete.py` — testes novos.

Não foram necessárias mudanças em:

- `backend/api/v1/devices.py` — resolução de campanha do player já lê de `CampaignPlaylistItem` com seus próprios filtros, sem relação com arquivamento de mídia.
- `frontend/src/pages/agenda.jsx`, `CampanhaPreview.jsx`, `EditorPlaylist.jsx`, `Campanhas.jsx` — seletores que chamam `listarMidias()` sem filtro já se beneficiam do novo default (excluir arquivadas) sem qualquer alteração de código.

## Riscos

- A migration adiciona um valor a um enum Postgres (`ALTER TYPE ... ADD VALUE`) seguido de `ADD COLUMN` no mesmo `upgrade()` — mesmo padrão já usado em `20260521_0915_device_command_lifecycle.py` (precedente real no projeto), mas downgrade não remove o valor do enum (limitação nativa do Postgres, documentada no próprio arquivo de migration).
- Migration não aplicada em produção (VPS) nesta sessão.
- A UI de seleção em massa não tem teste automatizado (página sem suíte de testes unitários, mesma situação de `FaixasAudio.jsx`/`PlaylistsSonoras.jsx` após as SPECs 016/017) — validado por lint e revisão manual.
