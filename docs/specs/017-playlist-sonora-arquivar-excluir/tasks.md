# SPEC 017 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 016 concluída — gate liberado.

## Diagnóstico

- [x] Auditar model `AudioPlaylist` — confirmado: só enum `status`, sem `archived_at`.
- [x] Auditar FKs que apontam para `AudioPlaylist` — confirmado: `Device.audio_playlist_id` e `Campaign.audio_playlist_id` são FK direta sem `ondelete` (diferente das faixas, referenciadas via tabela de junção).
- [x] Auditar `GET /audio/playlists` — confirmado: mesmo leak da SPEC 016, sem filtro de arquivadas por padrão.
- [x] Auditar os 5 call sites de `listarPlaylistsAudio()` — confirmado: 4 já passam `status: "active"` (preservados), 1 (`PlaylistsSonoras.jsx`) é a tela de gerenciamento, sem filtro de status na UI.
- [x] Auditar resolução de playlist do player (`backend/api/v1/devices.py`) — confirmado: `_build_audio_playlist`/`_build_player_playlist_response` já filtram por `status == "active"`, **sem bug no caminho real**.
- [x] Auditar endpoint secundário `backend/api/v1/audio/devices.py` — confirmado: não filtra por status, mas não é usado pelo frontend atual (`buscarPlaylistAudioDispositivo` sem consumidor).
- [x] Auditar `DELETE /audio/playlists/{id}` — confirmado: hard delete real, sem checagem de uso.
- [x] Auditar UI (`PlaylistsSonoras.jsx`) — confirmado: botão "excluir" sempre arquivava, sem distinção de Arquivar/Restaurar/Excluir nem filtro de status.

## Decisão de escopo (confirmada com o usuário)

- [x] Bloquear playlist arquivada no resolver do player (não apenas avisar na UI) — confirmado que o resolver principal já estava correto; o fix foi aplicado no endpoint secundário por precaução.
- [x] Checagem de uso + bloqueio com erro claro antes do delete (não desvincular automaticamente).

## Backend

- [x] Adicionar coluna `archived_at` ao model `AudioPlaylist`.
- [x] Expor `archived_at` em `AudioPlaylistResponse`.
- [x] Adicionar parâmetro `include_archived` a `GET /audio/playlists`.
- [x] Criar `CRUDAudioPlaylist.get_in_use_references()` — conta `Device`/`Campaign` vinculados via FK direta.
- [x] Atualizar `DELETE /audio/playlists/{id}` para bloquear com 409 quando vinculada.
- [x] Sobrescrever `CRUDAudioPlaylist.update()` para sincronizar `archived_at` (cobre `PUT` genérico, usado pela UI).
- [x] `update_status()` delega para `update()`.
- [x] Corrigir `GET /audio/devices/{device_id}/playlist` para filtrar `status == "active"`.
- [x] Criar migration aditiva `20260618_1300_audio_playlist_archived_at.py` com backfill.

## Frontend

- [x] `PlaylistsSonoras.jsx`: query passa `include_archived: true`.
- [x] Adicionar filtro de status (Select) — antes inexistente nesta tela.
- [x] Separar "Arquivar" de "Restaurar" + "Excluir definitivamente", com dois `ConfirmDialog` distintos.
- [x] Importar `deletarPlaylistAudio` (já existia em `api/audio.js`, sem uso em nenhuma tela).
- [x] Renomear `deleteTarget`/`deleteMutation` para `archiveTarget`/`archiveMutation`.

## Testes

- [x] Backend — `test_audio_playlist_archive_delete.py`: 9 testes novos (filtro padrão exclui arquivadas, include_archived inclui, status explícito tem precedência, archived_at via PUT setado/limpo, update_status mantém sincronia, delete bloqueado por device, delete bloqueado por campanha, delete permitido sem vínculo, contagem de referências). Validados por sintaxe (`pytest` indisponível no ambiente).
- [x] Lint (`eslint`) de `PlaylistsSonoras.jsx` e `api/audio.js` — sem erros nem warnings novos.
- [x] Suite completa do frontend: 170/173 — mesmas 3 falhas pré-existentes não relacionadas.

## Critérios de aceite

- [x] Playlists arquivadas não aparecem por padrão em nenhuma listagem/seletor.
- [x] UI distingue Arquivar, Restaurar e Excluir definitivamente.
- [x] Nenhum caminho do player serve conteúdo de playlist arquivada (confirmado: resolver principal já correto; endpoint secundário corrigido).
- [x] Excluir playlist vinculada retorna erro claro (409).
- [x] Excluir playlist sem vínculo remove de verdade.
- [x] `archived_at` sincronizado em ambos os caminhos.
- [ ] Migration aplicada em produção (VPS) — pendente de deploy.
- [ ] Validação manual end-to-end (criar → vincular a device → tentar excluir bloqueado → desvincular → excluir com sucesso) — não executada nesta sessão.

## Riscos e pendências

- [ ] Deploy da migration `20260618_1300_audio_playlist_archived_at` na VPS.
- [ ] Aviso de UX quando um device/campanha está vinculado a uma playlist já arquivada — não implementado, registrado como melhoria futura.
- [ ] Fix do endpoint secundário (`audio/devices.py`) sem cobertura de teste automatizado (sem suite pré-existente para esse arquivo).
