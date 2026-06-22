# SPEC 017 — Player

Status: implementada

## Comportamento confirmado (caminho real, já correto antes desta SPEC)

O resolver principal de playlist do player (`backend/api/v1/devices.py`):

- `_build_audio_playlist(device, db)` — filtra explicitamente `status == "active"` antes de montar o payload (linha ~667-669).
- `_build_player_playlist_response(db, device=device)` — resolve a playlist via campanha (`campaign.audio_playlist_id`) ou via device (`device.audio_playlist_id`), checando `status == "active"` em ambos os ramos.
- `get_device_playlist()` — o endpoint real (`GET /devices/{device_id}/playlist`), consumido pelo `Player.jsx` em produção via `getDevicePlaylist`/SSE — delega para `_build_player_playlist_response()`.

Conclusão: **o player principal nunca tocou uma playlist arquivada**, mesmo antes desta SPEC. Não foi necessária nenhuma mudança nesse caminho.

## Bug corrigido (caminho secundário)

`GET /audio/devices/{device_id}/playlist` (`backend/api/v1/audio/devices.py`) é um segundo endpoint, registrado no FastAPI mas **não usado por nenhum componente do frontend atual** — a função `buscarPlaylistAudioDispositivo` existe em `frontend/src/api/audio.js` mas não é importada/chamada em lugar nenhum.

Esse endpoint não verificava `playlist.status` antes de servir o conteúdo. Foi corrigido para retornar `404` quando a playlist está arquivada/inativa, no mesmo padrão do resolver principal — por precaução e consistência, já que é uma rota viva e alcançável (ex.: chamada direta de API, integração futura), mesmo sem impacto visível no player real hoje.

## Checklist de auditoria

- [x] Conferir `_build_audio_playlist` em `backend/api/v1/devices.py` — já filtra `status == "active"`.
- [x] Conferir `_build_player_playlist_response` — já filtra em ambos os ramos (campanha e device).
- [x] Conferir `get_device_playlist` — delega para `_build_player_playlist_response`, sem necessidade de mudança.
- [x] Conferir `get_device_player_versions` — retorna apenas metadados de versão (sem conteúdo de áudio), sem filtro de status necessário (não expõe faixas/URLs).
- [x] Conferir `backend/api/v1/audio/devices.py` — endpoint secundário sem filtro, corrigido.
- [x] Confirmar que `buscarPlaylistAudioDispositivo` (frontend) não tem nenhum consumidor real — corrigido por precaução, sem mudança de comportamento visível.
