# SPEC 007 — Plano de testes

## Backend

- `test_video_upload_detects_duration`: upload de MP4 salva `duration_seconds`.
- `test_video_upload_without_ffprobe_returns_clear_error_or_manual_fallback`.
- `test_media_period_future_not_in_player_payload`.
- `test_media_period_expired_not_in_player_payload`.
- `test_replace_media_keeps_media_id_and_campaign_items`.
- `test_replace_media_increments_file_version_and_hash`.
- `test_campaign_items_reorder_persists_order`.
- `test_audio_upload_multiple_partial_success`.
- `test_audio_playlist_items_backfill_from_track_ids`.
- `test_audio_folder_schedule_resolves_current_folder`.
- `test_audio_folder_schedule_detects_conflict`.
- `test_audio_spot_interval_due`.
- `test_audio_spot_interval_not_due`.
- `test_pairing_regenerate_rejects_old_token`.
- `test_shutdown_command_web_ack_failed_with_platform_unsupported`.

## Frontend Admin

- `CampaignPlaylistBuilder` adiciona item.
- `CampaignPlaylistBuilder` reordena item.
- `CampaignPlaylistBuilder` edita duracao/periodo/status.
- `MediaFormModal` nao exige duracao manual para video.
- `MediaFormModal` exige duracao para imagem/URL ou usa default.
- `MultiAudioUploadDialog` mostra progresso por arquivo.
- `AudioFolderFormModal` salva periodo/horario/status.
- `RadioScheduleEditor` alerta conflito.
- `AudioSpotFormModal` valida intervalo.
- `CommandStatusPanel` mostra `Nao suportado`.

## Player

- Video com audio + policy `auto`: radio pausa.
- Imagem + radio: radio toca.
- Policy `mix`: radio e midia tocam juntas apenas quando configurado.
- Spot devido: radio pausa, spot toca, radio retoma.
- Shuffle nao repete a mesma faixa imediatamente quando ha alternativas.
- Sequential respeita ordem.
- Playlist por pasta troca ao mudar horario.
- OSD mostra nome da musica e oculta conforme config.
- Pairing revoked via SSE volta para tela de pareamento.
- Shutdown em web puro falha com mensagem clara.

## E2E manual obrigatorio

- Upload de video com duracao automatica.
- Periodo de midia futuro/expirado.
- Substituicao de midia em campanha ativa.
- Playlist visual item a item com ordem customizada.
- Upload multiplo de audio com arquivo invalido no meio.
- Radio Manha/Tarde/Noite por horario.
- Spot a cada 10 minutos.
- Player sem mistura indevida de audio.
- Comando desligar/reiniciar por plataforma.
- Alterar codigo de pareamento invalida player antigo.
- Nome da musica aparece no player fullscreen.
