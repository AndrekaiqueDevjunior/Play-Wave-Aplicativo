# SPEC 017 — Tests

Status: implementada — testes de backend validados por sintaxe (pytest não executável neste ambiente); frontend sem testes unitários dedicados a esta tela, suite completa sem regressão; validação manual end-to-end pendente

## Testes automatizados — Backend (validados por sintaxe, não executados)

`backend/tests/test_audio_playlist_archive_delete.py` — testes novos:

| Teste | O que valida |
|---|---|
| `test_get_audio_playlists_excludes_archived_by_default` | listagem sem `status` exclui arquivadas |
| `test_get_audio_playlists_include_archived_keeps_archived` | `include_archived=true` mantém arquivadas |
| `test_get_audio_playlists_explicit_status_overrides_default_filter` | `status=archived` explícito tem precedência |
| `test_archiving_via_put_sets_archived_at` | `PUT` com `status=archived` seta `archived_at` |
| `test_restoring_via_put_clears_archived_at` | `PUT` com `status=active` limpa `archived_at` |
| `test_update_status_helper_keeps_archived_at_in_sync` | endpoint dedicado também sincroniza |
| `test_delete_blocked_when_linked_to_device` | 409 quando `Device.audio_playlist_id` aponta para a playlist |
| `test_delete_blocked_when_linked_to_campaign` | 409 quando `Campaign.audio_playlist_id` aponta para a playlist |
| `test_delete_allowed_when_not_linked` | exclusão real quando sem vínculo |
| `test_get_in_use_references_counts_devices_and_campaigns` | contagem correta por tipo de vínculo |
| `test_get_in_use_references_not_in_use_when_all_zero` | `in_use=False` quando ambas as contagens são zero |

Tentativa de execução real:

```bash
cd backend && python3 -m pytest tests/test_audio_playlist_archive_delete.py -q
```

Resultado: `ModuleNotFoundError: No module named 'fastapi'` — mesma limitação de ambiente das SPECs 011-016.

Mitigação: validação de sintaxe de todos os arquivos Python alterados via `ast.parse` (modelos, schemas, endpoints, CRUD, migration, teste) — todos `OK`. Complementado por revisão manual.

## Testes automatizados — Frontend

`PlaylistsSonoras.jsx` não possui suite de testes unitários dedicada (mesma situação de `FaixasAudio.jsx` na SPEC 016).

```bash
cd frontend && npx eslint src/pages/PlaylistsSonoras.jsx src/api/audio.js
```

Resultado: 0 erros, 0 warnings novos.

```bash
cd frontend && npx vitest run
```

Resultado: `170 passed`, `3 failed` — mesmas 3 falhas pré-existentes e não relacionadas (`player_sse.test.js`, `playbackQueueManager.test.js`).

## Testes manuais sugeridos (não executados nesta SPEC)

### TM017-01 — Arquivar esconde a playlist dos seletores

Passos: criar playlist, vincular a um device, arquivar a playlist na tela de gerenciamento, abrir o seletor de playlist em `DeviceEditDrawer`/`CampaignFormModal` — a playlist arquivada não deve aparecer.

### TM017-02 — Device vinculado a playlist arquivada não recebe áudio

Pré-condição: device com `audio_playlist_id` apontando para uma playlist que foi arquivada depois do vínculo (vínculo não removido).

Passos: o player do device consulta `GET /devices/{id}/playlist`.

Resultado esperado: `audio_playlist` retorna `null`/vazio (a playlist arquivada não é resolvida), mesmo com o vínculo ainda existindo no banco.

### TM017-03 — Excluir definitivamente bloqueado quando vinculada

Pré-condição: playlist arquivada ainda vinculada a um device ou campanha.

Passos: clicar em "Excluir definitivamente", confirmar.

Resultado esperado: erro 409 exibido via toast, playlist não removida.

### TM017-04 — Excluir definitivamente funciona quando livre

Pré-condição: playlist arquivada, desvinculada de todos os devices/campanhas.

Passos: clicar em "Excluir definitivamente", confirmar.

Resultado esperado: playlist removida da listagem e do banco.

## Evidências de teste

- Ambiente: desenvolvimento local (sem backend rodando; validação por análise de código e sintaxe).
- Build/commit: branch `fix/dev-env`.
- Data: 2026-06-18.
- Resultado: 170/173 testes de frontend (suite completa, sem regressão); 11 testes novos de backend validados por sintaxe e revisão manual.
- Observações: validação manual end-to-end (TM017-01 a TM017-04) e deploy da migration na VPS ficam pendentes.
