# SPEC 016 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 015 concluída — gate liberado.

## Diagnóstico

- [x] Auditar model `AudioTrack` (`backend/core/models.py`) — confirmado: só enum `status` (active/inactive/archived), sem `archived_at`/`deleted_at`/`is_active`.
- [x] Auditar `DELETE /audio/tracks/{id}` — confirmado: já faz hard delete real (`crud_audio_track.remove()` → `db.delete()`), não é "exclusão fake".
- [x] Auditar `GET /audio/tracks` — confirmado: não filtra arquivadas por padrão, causa raiz do leak relatado.
- [x] Auditar `AudioTrackSelector.jsx` e os 6 call sites de `listarFaixas()` — confirmado: 4 já passam `status: "active"` explicitamente (preservados), 1 (`FaixasAudio.jsx`) precisa ver tudo (tela de gerenciamento), 1 (`PlaylistsSonoras.jsx`) usa para cálculo de duração (impacto secundário aceitável).
- [x] Auditar resolução de playlist do player (`backend/api/v1/devices.py`) — confirmado: já filtra por `status == "active"`, sem bug.
- [x] Auditar FKs que referenciam `AudioTrack` — confirmado: `AudioFolderTrack`, `AudioPlaylistItem`, `AudioSpot` usam `ondelete="RESTRICT"`, sem checagem amigável antes do delete.
- [x] Auditar UI (`FaixasAudio.jsx`) — confirmado: botão "Excluir" sempre arquivava (`status: archived`), sem caminho de UI para excluir definitivamente ou restaurar individualmente.

## Decisão de escopo (confirmada com o usuário)

- [x] Corrigir filtros de listagem + adicionar checagem de uso antes do delete (não apenas filtros).
- [x] Adicionar `archived_at` nesta SPEC (não esperar a SPEC 020).

## Backend

- [x] Adicionar coluna `archived_at` ao model `AudioTrack`.
- [x] Expor `archived_at` em `AudioTrackResponse`.
- [x] Adicionar parâmetro `include_archived` a `GET /audio/tracks`, com exclusão de `archived` por padrão quando `status` não é informado.
- [x] Criar `CRUDAudioTrack.get_in_use_references()` — conta uso em playlist/pasta/spot.
- [x] Atualizar `DELETE /audio/tracks/{id}` para bloquear com 409 quando em uso.
- [x] Sobrescrever `CRUDAudioTrack.update()` para sincronizar `archived_at` com qualquer mudança de `status` (cobre o fluxo real `PUT` usado pela UI, não só o `PATCH /status` dedicado).
- [x] `update_status()` passa a delegar para `update()`, eliminando duplicação de lógica.
- [x] Criar migration aditiva `20260618_1200_audio_track_archived_at.py` com backfill para faixas já arquivadas.

## Frontend

- [x] `FaixasAudio.jsx`: query da própria tela passa `include_archived: true` (precisa ver arquivadas para o filtro de status existente continuar funcionando).
- [x] Separar ação "Arquivar" (faixas ativas/inativas) de "Restaurar" + "Excluir definitivamente" (faixas arquivadas).
- [x] Dois `ConfirmDialog` distintos, com textos claros sobre o efeito de cada ação.
- [x] Importar `deletarFaixa` (já existia em `api/audio.js`, não estava sendo usado em nenhuma tela).
- [x] Renomear estado/mutation de `deleteTarget`/`deleteMutation` (que na verdade arquivava) para `archiveTarget`/`archiveMutation`, evitando o nome confuso que motivou parte do relato do cliente.

## Testes

- [x] Backend — `test_audio_track_archive_delete.py`: 9 testes novos (filtro padrão exclui arquivadas, include_archived inclui, status explícito tem precedência, archived_at setado/limpo via PUT, archived_at preservado quando status não muda, update_status mantém sincronia, delete bloqueado quando em uso, delete permitido quando livre, contagem de referências). Validados por análise de sintaxe (`ast.parse`) — `pytest` não executável neste ambiente (sem FastAPI instalado).
- [x] Lint (`eslint`) de `FaixasAudio.jsx` e `api/audio.js` — sem erros nem warnings novos.
- [x] Suite completa do frontend: 170/173 passando — as 3 falhas (`player_sse.test.js`, `playbackQueueManager.test.js`) são pré-existentes e não relacionadas, confirmadas em SPECs anteriores.

## Critérios de aceite

- [x] Faixas arquivadas não aparecem por padrão em nenhuma listagem/seletor.
- [x] UI distingue Arquivar, Restaurar e Excluir definitivamente.
- [x] Excluir faixa em uso retorna erro claro (409) em vez de erro genérico.
- [x] Excluir faixa sem uso remove de verdade (arquivo + registro).
- [x] `archived_at` sincronizado em ambos os caminhos de mudança de status.
- [ ] Migration aplicada em produção (VPS) — pendente de deploy.
- [ ] Validação manual end-to-end (criar → arquivar → confirmar ausência no seletor → restaurar → excluir) — não executada nesta sessão por falta de ambiente de teste com banco real.

## Riscos e pendências

- [ ] Deploy da migration `20260618_1200_audio_track_archived_at` na VPS.
- [ ] `PlaylistsSonoras.jsx` pode subestimar duração total de playlists com faixas arquivadas referenciadas (ver `design.md`) — comportamento aceito, não corrigido nesta SPEC.
- [ ] Validar com o cliente se a mensagem de erro 409 (contagem por tipo de referência) é suficientemente clara, ou se será necessário listar os nomes específicos das playlists/spots que usam a faixa.
