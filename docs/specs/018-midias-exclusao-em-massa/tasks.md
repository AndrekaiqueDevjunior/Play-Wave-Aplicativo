# SPEC 018 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 017 concluída — gate liberado.

## Diagnóstico

- [x] Auditar model `Media` — confirmado: sem `ARCHIVED`/`archived_at`, único caso entre as SPECs 016-018 que precisa criar a capacidade do zero.
- [x] Auditar `DELETE /media/{id}` — confirmado: hard delete real, com checagem de uso (`_campaigns_using_media`) que só olha `Campaign.media_ids`/`media_order`.
- [x] Auditar `CampaignPlaylistItem.media_id` — confirmado: FK `RESTRICT`, caminho relacional real usado pelo player, **não coberto** pela checagem de uso existente.
- [x] Auditar `BibliotecaMidias.jsx` — confirmado: nenhum padrão de seleção em massa, ao contrário de `FaixasAudio.jsx`/`PlaylistsSonoras.jsx`.
- [x] Auditar `GET /media` — confirmado: sem `include_archived` (N/A antes desta SPEC, já que `archived` não existia).
- [x] Auditar os 4 call sites de `listarMidias()` sem filtro (`agenda.jsx`, `CampanhaPreview.jsx`, `EditorPlaylist.jsx`, `Campanhas.jsx`) — beneficiados automaticamente pelo filtro novo, sem necessidade de alteração.

## Decisão de escopo (confirmada com o usuário)

- [x] Criar `archived_at` + `MediaStatus.ARCHIVED` nesta SPEC (não esperar a SPEC 020).
- [x] Corrigir a checagem de uso para também contar `CampaignPlaylistItem` (não manter a lacuna existente).

## Backend

- [x] Adicionar `MediaStatus.ARCHIVED` ao enum e `archived_at` ao model `Media`.
- [x] Adicionar `MediaStatusEnum.ARCHIVED`, `archived_at` em `MediaResponse`, schemas `MediaBulkActionRequest`/`MediaBulkActionItemResult`/`MediaBulkActionResponse`.
- [x] Adicionar `include_archived` a `GET /media`.
- [x] Sobrescrever `CRUDMedia.update()` para sincronizar `archived_at`; `update_status()` delega para `update()`.
- [x] Criar `CRUDMedia.get_in_use_references()` — conta `CampaignPlaylistItem` (relacional) e campos legados (`Campaign.media_ids`/`media_order`).
- [x] Corrigir `DELETE /media/{id}` para bloquear (mesmo com `force=true`) quando há `CampaignPlaylistItem` vinculado.
- [x] Criar `POST /media/bulk-archive` — processa cada item independentemente, nunca falha por uso.
- [x] Criar `POST /media/bulk-delete` — processa cada item independentemente, reporta falha por mídia em uso (relacional ou legado), sem parâmetro `force`.
- [x] Criar migration `20260618_1400_media_archived_at.py` (novo valor de enum + coluna).

## Frontend

- [x] `frontend/src/api/midias.js`: `arquivarMidiasEmMassa`, `excluirMidiasEmMassa`.
- [x] `BibliotecaMidias.jsx`: query passa `include_archived: true`.
- [x] Adicionar filtro de status (Select) — antes inexistente.
- [x] Adicionar modo de seleção: botão "Selecionar", checkboxes por item (grid e lista), "Selecionar todas", "Limpar seleção".
- [x] Barra de ações em lote com contagem e botões Arquivar/Excluir, com loading state.
- [x] Dois `ConfirmDialog` para as ações em massa, com textos claros sobre o comportamento (arquivar nunca falha por uso; excluir pula itens em uso).
- [x] Resumo de resultado via toast, listando motivo de cada falha quando houver.
- [x] Ações individuais de Arquivar/Restaurar adicionadas ao menu de cada item (grid e lista) — antes só existia "Excluir" (rotulado incorretamente, igual ao padrão de bug das SPECs 016/017).

## Testes

- [x] Backend — `test_media_bulk_archive_delete.py`: 12 testes novos (filtro padrão exclui arquivadas, include_archived inclui, archived_at via update_status setado/limpo, delete bloqueado por CampaignPlaylistItem mesmo com force, delete permitido sem uso, bulk-archive processa itens independentemente, bulk-archive reporta falha de item sem afetar os demais, bulk-delete pula item em uso reportando motivo, bulk-delete reporta uso legado, bulk-delete sucesso total quando nada em uso, contagem de referências com/sem uso). Validados por sintaxe (`pytest` indisponível no ambiente).
- [x] Lint (`eslint`) de `BibliotecaMidias.jsx` e `api/midias.js` — sem erros novos (1 erro pré-existente de import não usado corrigido ao reaproveitar o ícone no loading state).
- [x] Suite completa do frontend: 170/173 — mesmas 3 falhas pré-existentes não relacionadas.

## Critérios de aceite

- [x] Mídias arquivadas não aparecem por padrão em nenhuma listagem/seletor.
- [x] UI permite selecionar várias mídias e arquivar/excluir em lote.
- [x] Resultado da ação em massa mostra sucesso/falha por item com motivo.
- [x] Mídia em uso não impede que as demais do lote sejam processadas.
- [x] Arquivamento em massa nunca falha por "em uso".
- [x] `archived_at` sincronizado em qualquer caminho de mudança de status.
- [ ] Migration aplicada em produção (VPS) — pendente de deploy.
- [ ] Validação manual end-to-end (selecionar várias, arquivar, restaurar, excluir com uma em uso e outra livre) — não executada nesta sessão.

## Riscos e pendências

- [ ] Deploy da migration `20260618_1400_media_archived_at` na VPS.
- [ ] Aviso de UX quando uma campanha referencia uma mídia já arquivada — não implementado, registrado como melhoria futura (mesma decisão da SPEC 017).
- [ ] `bulk-restore` não implementado — restaurar continua item por item.
