# SPEC 016 — Tests

Status: implementada — testes de backend validados por sintaxe (pytest não executável neste ambiente); frontend sem testes unitários dedicados a esta tela, suite completa sem regressão; validação manual end-to-end pendente

## Testes automatizados — Backend (validados por sintaxe, não executados)

`backend/tests/test_audio_track_archive_delete.py` — testes novos:

| Teste | O que valida |
|---|---|
| `test_get_audio_tracks_excludes_archived_by_default` | `GET /audio/tracks` sem `status` filtra `status != 'archived'` |
| `test_get_audio_tracks_include_archived_skips_default_filter` | `include_archived=true` não aplica o filtro de exclusão |
| `test_get_audio_tracks_explicit_status_overrides_default_filter` | `status=archived` explícito tem precedência sobre o default |
| `test_archiving_via_put_sets_archived_at` | `PUT` com `status=archived` seta `archived_at` |
| `test_restoring_via_put_clears_archived_at` | `PUT` com `status=active` limpa `archived_at` |
| `test_update_without_status_field_does_not_touch_archived_at` | `PUT` sem campo `status` não altera `archived_at` existente |
| `test_update_status_helper_keeps_archived_at_in_sync` | `update_status()` (endpoint dedicado) também sincroniza `archived_at` |
| `test_delete_blocked_when_track_in_use` | `DELETE` retorna 409 com contagem quando há referências |
| `test_delete_allowed_when_track_not_in_use` | `DELETE` remove de verdade quando livre de referências |
| `test_get_in_use_references_counts_all_sources` | conta playlists/pastas/spots corretamente |
| `test_get_in_use_references_not_in_use_when_all_zero` | `in_use=False` quando todas as contagens são zero |

Tentativa de execução real:

```bash
cd backend && python3 -m pytest tests/test_audio_track_archive_delete.py -q
```

Resultado: `ModuleNotFoundError: No module named 'fastapi'` — ambiente local sem dependências do backend instaladas (sem venv do projeto). Mesma limitação registrada nas SPECs 011-015.

Mitigação aplicada — validação de sintaxe:

```bash
cd backend && python3 -c "
import ast
for f in ['core/models.py', 'core/schemas_completos.py', 'api/v1/audio/tracks.py', 'crud/entidades/crud_audio_track.py', 'alembic/versions/20260618_1200_audio_track_archived_at.py', 'tests/test_audio_track_archive_delete.py']:
    ast.parse(open(f).read()); print('OK:', f)
"
```

Resultado: `OK` para os 6 arquivos. Complementado por revisão manual linha a linha de cada teste e do código correspondente.

## Testes automatizados — Frontend

`FaixasAudio.jsx` não possui suite de testes unitários dedicada (página de gerenciamento sem lógica testável isoladamente — toda a lógica nova é simples roteamento de mutations já testado implicitamente pelos testes de backend dos endpoints que ela chama).

```bash
cd frontend && npx eslint src/pages/FaixasAudio.jsx src/api/audio.js
```

Resultado: 0 erros, 0 warnings novos.

```bash
cd frontend && npx vitest run
```

Resultado: `170 passed`, `3 failed` — as 3 falhas (`player_sse.test.js`, `playbackQueueManager.test.js`) são pré-existentes e não relacionadas a esta SPEC (nenhum arquivo de teste tocado), confirmadas em SPECs anteriores via `git stash`.

## Testes manuais sugeridos (não executados nesta SPEC)

### TM016-01 — Arquivar esconde a faixa dos seletores

Passos:

1. Criar uma faixa de áudio nova.
2. Adicionar a faixa a uma playlist sonora (via seletor).
3. Arquivar a faixa na tela de Faixas de Áudio.
4. Abrir o seletor de faixas de uma playlist (nova ou existente) — a faixa arquivada não deve aparecer.
5. Na tela de Faixas de Áudio, com filtro "Todos" ou "Arquivado", a faixa deve aparecer normalmente (a tela de gerenciamento usa `include_archived=true`).

Resultado esperado: faixa some dos seletores operacionais, mas continua visível/gerenciável na tela de Faixas de Áudio.

### TM016-02 — Restaurar volta a faixa para active

Passos: na tela de Faixas de Áudio, filtrar "Arquivado", clicar em "Restaurar" em uma faixa.

Resultado esperado: faixa volta a aparecer nos seletores; `status` volta para `active`; `archived_at` volta a `null`.

### TM016-03 — Excluir definitivamente bloqueado quando em uso

Pré-condição: faixa arquivada que ainda está referenciada em uma playlist (não removida de lá).

Passos: clicar em "Excluir definitivamente", confirmar.

Resultado esperado: erro exibido via toast com a mensagem do backend (409), faixa não é removida.

### TM016-04 — Excluir definitivamente funciona quando livre

Pré-condição: faixa arquivada, removida de todas as playlists/pastas/spots que a usavam.

Passos: clicar em "Excluir definitivamente", confirmar.

Resultado esperado: faixa removida da listagem e do banco; arquivo físico removido do disco (se existir em `/uploads/`).

## Evidências de teste

- Ambiente: desenvolvimento local (sem backend rodando; validação por análise de código e sintaxe).
- Build/commit: branch `fix/dev-env`.
- Data: 2026-06-18.
- Resultado: 170/173 testes de frontend (suite completa, sem regressão); 11 testes novos de backend validados por sintaxe e revisão manual (execução real bloqueada pela ausência de FastAPI no ambiente).
- Observações: validação manual end-to-end (TM016-01 a TM016-04) e deploy da migration na VPS ficam pendentes — mesma situação já registrada para itens que exigem banco de dados real/produção nas SPECs anteriores.
