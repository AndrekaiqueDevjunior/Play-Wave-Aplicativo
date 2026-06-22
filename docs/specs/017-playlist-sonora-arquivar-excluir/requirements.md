# SPEC 017 — Requirements

Status: implementada
Data: 2026-06-18

## Contexto

Cliente reportou que a playlist sonora "não exclui corretamente, apenas arquiva e continua aparecendo no sistema" — mesmo relato da SPEC 016, agora para `AudioPlaylist`. A auditoria confirmou o mesmo padrão de leak de filtro, mais um bug adicional: um endpoint secundário de resolução do player não filtrava playlists arquivadas (o endpoint principal, usado pelo player real, já filtrava corretamente).

## Objetivo

Diferenciar Arquivar / Restaurar / Excluir definitivamente para playlists sonoras, escondê-las por padrão em todos os seletores, garantir que nenhum caminho do player sirva conteúdo de uma playlist arquivada, e tornar a exclusão definitiva segura.

## Requisitos funcionais

### RF017-01 — Playlists arquivadas escondidas por padrão

`GET /audio/playlists` não deve retornar playlists com `status=archived` a menos que explicitamente solicitado.

Critérios:

- Novo parâmetro `include_archived` (bool, default `false`).
- `status` explícito (ex.: `status=archived`) tem precedência sobre o default.
- Os 4 seletores existentes que já filtravam por `status=active` continuam funcionando sem alteração.
- A tela de gerenciamento (`PlaylistsSonoras.jsx`) passa `include_archived=true` e ganha um filtro de status (igual à tela de Faixas de Áudio).

### RF017-02 — Distinção visual entre Arquivar e Excluir definitivamente

Mesmo padrão de UI da SPEC 016, aplicado a `PlaylistsSonoras.jsx`:

- Botão "Arquivar" para playlists ativas/inativas.
- Para playlists arquivadas: "Restaurar" e "Excluir definitivamente", com confirmação distinta para cada ação.

### RF017-03 — Playlist arquivada nunca é servida ao player

Nenhum caminho de resolução de playlist do player deve entregar conteúdo de uma playlist arquivada, mesmo que `Device.audio_playlist_id` ou `Campaign.audio_playlist_id` ainda apontem para ela.

Critérios:

- Confirmado: o resolver principal (`_build_audio_playlist`/`_build_player_playlist_response` em `backend/api/v1/devices.py`) já filtra por `status == "active"` — sem alteração necessária.
- Corrigido: o endpoint secundário (`GET /audio/devices/{device_id}/playlist`) agora também filtra por `status == "active"`, retornando 404 quando a playlist está arquivada/inativa.

### RF017-04 — Exclusão definitiva segura

Excluir uma playlist vinculada a um device ou campanha deve falhar com mensagem clara, não com erro genérico de banco.

Critérios:

- Endpoint verifica `Device.audio_playlist_id` e `Campaign.audio_playlist_id` antes de excluir (FK direta, diferente das faixas que usam tabela de junção).
- Se vinculada, retorna `409 Conflict` com contagem por tipo de vínculo.
- Se não vinculada, executa a exclusão real.

### RF017-05 — Timestamp de arquivamento

Mesmo padrão da SPEC 016: campo `archived_at` (nullable) no model `AudioPlaylist`, sincronizado automaticamente com o enum `status` em qualquer caminho de update (`PUT` genérico ou `PATCH /status`).

## Compatibilidade

- Não altera o comportamento de `status=active`/`status=inactive` explícitos.
- Não altera o resolver principal do player — já estava correto.
- Não remove o hard delete real — apenas adiciona a checagem de uso antes dele.
- Migration aditiva, com backfill para playlists já arquivadas.

## Critérios de aceite

- [x] Playlists arquivadas não aparecem por padrão em `GET /audio/playlists` nem em nenhum seletor.
- [x] UI distingue Arquivar, Restaurar e Excluir definitivamente.
- [x] Nenhum caminho do player serve conteúdo de playlist arquivada.
- [x] Excluir playlist vinculada a device/campanha retorna erro claro (409).
- [x] Excluir playlist sem vínculo remove de verdade.
- [x] `archived_at` sincronizado em ambos os caminhos de mudança de status.
- [ ] Migration aplicada em produção (VPS) — pendente de deploy.
