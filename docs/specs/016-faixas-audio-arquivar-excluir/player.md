# SPEC 016 — Player

Status: implementada — nenhuma mudança necessária no player

## Comportamento confirmado (já correto antes desta SPEC)

A auditoria confirmou que o player **já não recebia faixas arquivadas**. A resolução de playlist de áudio para o device (`backend/api/v1/devices.py`, funções `_audio_playlist_track_payload` e `_build_folder_schedules_payload`) filtra explicitamente por `AudioTrack.status == "active"` ao montar o payload entregue ao player.

Isso significa que o bug relatado pelo cliente ("faixas arquivadas continuam aparecendo") nunca afetou a reprodução real no player — afetava apenas as **telas de seleção no gerenciador** (escolher faixas para adicionar a uma playlist, pasta de rádio, ou spot), onde o usuário via e podia selecionar faixas arquivadas porque a listagem (`GET /audio/tracks`) não filtrava.

## Por que não foi necessária mudança aqui

- O endpoint do player já usa um filtro próprio e específico (`status == "active"`), independente do endpoint genérico `GET /audio/tracks` que foi corrigido nesta SPEC.
- Mesmo que uma faixa arquivada estivesse, por engano, referenciada em uma `AudioPlaylistItem` (porque foi adicionada antes de ser arquivada), o player não a reproduziria — o filtro é aplicado na query de resolução, não apenas na listagem do CRUD.

## Checklist de auditoria

- [x] Conferir `backend/api/v1/devices.py` — `_audio_playlist_track_payload` filtra por `status == "active"`.
- [x] Conferir `_build_folder_schedules_payload` — mesmo filtro aplicado a pastas de rádio.
- [x] Confirmar que nenhuma alteração nesta SPEC (filtro de `GET /audio/tracks`, `archived_at`, checagem de uso no delete) afeta o caminho de resolução do player — são endpoints e funções completamente separados.
