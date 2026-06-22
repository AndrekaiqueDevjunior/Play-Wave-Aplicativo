# SPEC 018 — Tests

Status: implementada — testes de backend validados por sintaxe (pytest não executável neste ambiente); frontend sem testes unitários dedicados a esta tela, suite completa sem regressão; validação manual end-to-end pendente

## Testes automatizados — Backend (validados por sintaxe, não executados)

`backend/tests/test_media_bulk_archive_delete.py` — 12 testes novos:

| Teste | O que valida |
|---|---|
| `test_get_media_excludes_archived_by_default` | listagem sem `status` exclui arquivadas |
| `test_get_media_include_archived_keeps_archived` | `include_archived=true` mantém arquivadas |
| `test_update_status_helper_sets_archived_at` | `update_status("archived")` seta `archived_at` |
| `test_update_status_helper_clears_archived_at_on_restore` | `update_status("available")` limpa `archived_at` |
| `test_delete_blocked_when_in_campaign_playlist_item` | 409 quando há `CampaignPlaylistItem` vinculado |
| `test_delete_blocked_when_in_campaign_playlist_item_even_with_force` | `force=true` não contorna o bloqueio relacional |
| `test_delete_allowed_when_not_in_use` | exclusão real quando sem nenhum vínculo |
| `test_bulk_archive_processes_each_item_independently` | arquiva todos os itens válidos do lote |
| `test_bulk_archive_reports_failure_for_missing_media_without_failing_others` | item inexistente falha sem afetar os demais |
| `test_bulk_delete_skips_media_in_use_reports_reason` | item em uso (relacional) é pulado com motivo, outro item é excluído |
| `test_bulk_delete_reports_legacy_campaign_usage` | item em uso (legado JSON) é reportado corretamente |
| `test_bulk_delete_all_succeed_when_none_in_use` | sucesso total quando nenhum item está em uso |
| `test_get_in_use_references_counts_playlist_items_and_legacy` | contagem correta com uso |
| `test_get_in_use_references_not_in_use_when_no_references` | `in_use=False` quando não há referências |

Tentativa de execução real:

```bash
cd backend && python3 -m pytest tests/test_media_bulk_archive_delete.py -q
```

Resultado: `ModuleNotFoundError: No module named 'fastapi'` — mesma limitação de ambiente das SPECs 011-017.

Mitigação: validação de sintaxe (`ast.parse`) de todos os arquivos Python alterados (model, schemas, endpoint, CRUD, migration, teste) — todos `OK`. Complementado por revisão manual de cada teste contra o código correspondente.

## Testes automatizados — Frontend

`BibliotecaMidias.jsx` não possui suite de testes unitários dedicada (mesma situação de `FaixasAudio.jsx`/`PlaylistsSonoras.jsx` após as SPECs 016/017).

```bash
cd frontend && npx eslint src/pages/BibliotecaMidias.jsx src/api/midias.js
```

Resultado: 0 erros, 0 warnings (1 erro pré-existente de import não utilizado corrigido durante a implementação, reaproveitando o ícone `Loader2` no estado de carregamento das ações em massa).

```bash
cd frontend && npx vitest run
```

Resultado: `170 passed`, `3 failed` — mesmas 3 falhas pré-existentes e não relacionadas (`player_sse.test.js`, `playbackQueueManager.test.js`).

## Testes manuais sugeridos (não executados nesta SPEC)

### TM018-01 — Arquivar em massa esconde mídias dos seletores

Passos: selecionar 3 mídias na Biblioteca, arquivar em massa, abrir o seletor de mídia em uma campanha — as 3 não devem aparecer.

Resultado esperado: arquivamento sempre bem-sucedido (nunca falha por uso); mídias desaparecem dos seletores; continuam visíveis na Biblioteca com filtro de status "Arquivada".

### TM018-02 — Excluir em massa com mídia em uso

Pré-condição: 3 mídias selecionadas, uma delas referenciada em `CampaignPlaylistItem` de uma campanha ativa.

Passos: clicar em "Excluir (3)", confirmar.

Resultado esperado: toast mostra "2/3 excluídas, 1 falharam" com o motivo (uso em playlist de campanha); a mídia em uso permanece na listagem; as outras 2 são removidas.

### TM018-03 — Restaurar individual

Passos: filtrar por "Arquivada", usar o menu de uma mídia → "Restaurar".

Resultado esperado: mídia volta a aparecer nos seletores; `status` volta para `available`; `archived_at` volta a `null`.

### TM018-04 — Selecionar todas respeita o filtro atual

Passos: aplicar um filtro (ex.: tipo = vídeo), clicar em "Selecionar Todas".

Resultado esperado: apenas os itens visíveis no filtro atual são selecionados, não todas as mídias do sistema.

## Evidências de teste

- Ambiente: desenvolvimento local (sem backend rodando; validação por análise de código e sintaxe).
- Build/commit: branch `fix/dev-env`.
- Data: 2026-06-18.
- Resultado: 170/173 testes de frontend (suite completa, sem regressão); 12 testes novos de backend validados por sintaxe e revisão manual.
- Observações: validação manual end-to-end (TM018-01 a TM018-04) e deploy da migration na VPS ficam pendentes.
