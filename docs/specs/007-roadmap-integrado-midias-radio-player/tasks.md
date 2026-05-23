# SPEC 007 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Auditoria e SPEC

- [x] Mapear telas frontend envolvidas.
- [x] Mapear endpoints backend existentes.
- [x] Mapear models/migrations existentes.
- [x] Identificar mocks/localStorage/hardcoded.
- [x] Criar SPEC tecnica consolidada.

## Fase A — Consolidacao do existente

- [x] Confirmar Docker build backend/frontend.
- [x] Confirmar backend sobe com migrations atuais.
- [x] Confirmar task Celery `tasks.media.backfill_has_audio`.
- [ ] Rodar E2E manual de upload de video com duracao automatica.
- [ ] Rodar E2E manual de periodo de midia.
- [ ] Rodar E2E manual de substituicao de midia mantendo campanha.
- [ ] Rodar E2E manual de regenerar codigo invalidando player antigo.
- [ ] Rodar E2E manual de OSD musica atual.

## Fase B — Playlist visual real

- [x] Criar API client para `/campaigns/{id}/items`.
- [x] Criar `CampaignPlaylistBuilder`.
- [~] Criar drawer de adicionar midias — implementado como biblioteca inline no builder; drawer dedicado pode ficar para refinamento.
- [x] Permitir edicao de duracao/periodo/status/repeat por item.
- [x] Implementar drag and drop e botoes mover.
- [x] Substituir fluxo principal de checkbox em `CampaignFormModal`.
- [x] Testar ordem persistida e player respeitando ordem.

## Fase C — Radio v2 banco/backend

- [x] Migration `audio_playlist_items`.
- [x] Backfill de `audio_playlists.track_ids`.
- [x] CRUD/API de itens de playlist de audio.
- [x] Migration `audio_folders` e `audio_folder_tracks`.
- [x] CRUD/API de pastas.
- [x] Migration `audio_playlist_folder_schedules`.
- [x] Resolver de agenda de pastas.
- [ ] Migration `audio_spots`, `audio_spot_schedules`, `audio_playback_events`.
- [ ] Resolver de spots por intervalo.
- [ ] Endpoint `POST /audio/tracks/upload-multiple`.
- [ ] Backend `ffprobe` como fonte oficial de duracao de audio.

## Fase D — Radio v2 frontend

- [ ] `MultiAudioUploadDialog`.
- [ ] Selecao multipla de faixas.
- [ ] UI de pastas de audio.
- [ ] UI de programacao por horario.
- [ ] UI de spots por intervalo.
- [ ] UI de modo sequencial/shuffle por playlist/pasta.

## Fase E — Player audio manager

- [ ] Criar audio manager central.
- [ ] Implementar fila sequencial.
- [ ] Implementar shuffle sem repeticao imediata.
- [ ] Implementar spots sem sobreposicao.
- [ ] Registrar eventos de musica/spot.
- [ ] Validar comportamento com video + radio + spot.

## Fase F — Comandos nativos

- [ ] Validar Electron bridge real em Windows/Linux.
- [ ] Validar Capacitor plugin real no APK.
- [ ] Mostrar `platform_unsupported` no painel.
- [ ] Testar shutdown/restart em plataforma suportada.
- [ ] Testar mensagem clara em web puro.

## Testes

- [ ] Backend: upload multiplo com sucesso parcial.
- [x] Backend/player: playlist de audio relacional com fallback legado.
- [x] Backend: pastas de audio e vinculo ordenado com faixas.
- [ ] Backend: resolver de agenda por pasta.
- [ ] Backend: conflito de horario.
- [ ] Backend: spots por intervalo.
- [x] Frontend: playlist builder de campanha.
- [x] Backend/player: ordem persistida da playlist visual chega ao payload do player.
- [ ] Frontend: upload multiplo de audio.
- [ ] Player: sequencial.
- [ ] Player: shuffle.
- [ ] Player: spot interrompe/retoma sem overlap.
- [ ] E2E: radio troca pasta ao mudar horario.

## Rollout

- [ ] Deploy backend com migrations.
- [ ] Backfill audio playlist items.
- [ ] Deploy frontend admin com fluxo novo.
- [ ] Deploy player com fallback para payload legado.
- [ ] Validar com cliente em um device real.

## Pos-rollout

- [ ] Monitorar erros de upload.
- [ ] Monitorar eventos de spot.
- [ ] Monitorar comandos `platform_unsupported`.
- [ ] Planejar remocao de JSON legado.
