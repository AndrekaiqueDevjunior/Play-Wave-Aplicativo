# SPEC 002 — Radio, Audio e Player

Status: auditoria e plano inicial  
Data: 2026-05-21  
Projeto: PlayWave

## Objetivo

Mapear o estado atual do PlayWave para evoluir Radio/Audio e corrigir pontos do Player antes de implementar codigo funcional.

Esta auditoria cobre:

- upload multiplo de audios;
- selecao multipla;
- pastas/categorias;
- playlists de radio;
- agendamento por horario;
- spots recorrentes;
- conflito entre audio da midia visual e radio;
- comandos remotos;
- desligamento/restart;
- pareamento/token;
- overlay com nome da musica no player.

## 1. Telas Encontradas

### Radio / Audio

Rotas encontradas em `frontend/src/app.jsx`:

- `/audio/faixas` -> `frontend/src/pages/FaixasAudio.jsx`
- `/audio/playlists` -> `frontend/src/pages/PlaylistsSonoras.jsx`
- alias legado `/audio/tracks` -> `frontend/src/pages/FaixasAudio.jsx`

Componentes:

- `frontend/src/components/audio/AudioTrackFormModal.jsx`
- `frontend/src/components/audio/AudioPlaylistsFormModal.jsx`
- `frontend/src/components/audio/AudioPlayer.jsx`

Estado atual:

- Existe tela de faixas de audio.
- Existe tela de playlists sonoras.
- Existe upload de uma faixa por vez.
- Existe selecao de faixas dentro da playlist, mas baseada em clique individual.
- Existe drag and drop simples para ordenar faixas da playlist.
- Existe loop e shuffle no cadastro da playlist.

Faltando:

- Upload multiplo real.
- Progresso por arquivo.
- Selecao em massa de faixas.
- Pastas/agrupamentos reais.
- Agendamento por pasta/playlist por horario.
- Spots recorrentes.
- Tela de agenda de radio.
- Tela de spots.

### Player

Arquivos:

- `frontend/src/pages/Player.jsx`
- `frontend/src/components/player/MediaRenderer.jsx`
- `frontend/src/components/player/PlayerOSD.jsx`
- `frontend/src/player-core/storage.js`
- `frontend/src/player-core/commands.js`
- `frontend/src/components/audio/AudioPlayer.jsx`

Estado atual:

- Player busca playlist visual.
- Player carrega audio playlist junto da campanha/device.
- `AudioPlayer` e persistente e invisivel.
- Player recebe comandos por polling.
- Player escuta SSE para atualizacao de playlist/config.
- Player usa cache local via IndexedDB e pareamento via localStorage.

Faltando:

- Overlay do nome da musica.
- Estado atual da musica reportado ao backend.
- Regras claras para conflito radio vs audio do video.
- Comandos de desligamento/restart fisico por plataforma.
- Status de comando granular: received/executing/completed/expired.

### Dispositivos / Comandos

Telas:

- `frontend/src/pages/Dispositivos.jsx`
- `frontend/src/pages/DispositivoDetalhe.jsx`
- `frontend/src/pages/DispositivoNovo.jsx`
- `frontend/src/components/devices/DeviceFormModal.jsx`
- `frontend/src/components/devices/DeviceEditDrawer.jsx`
- `frontend/src/pages/Monitoramento.jsx`

Estado atual:

- `DispositivoDetalhe.jsx` possui botoes para comandos:
  - `sync`
  - `refresh_playlist`
  - `clear_cache`
  - `restart`
- Exibe historico/log de comandos por device.

Faltando:

- Central de comandos dedicada.
- Comando de desligar dispositivo.
- Diferenciar reiniciar app, reiniciar player, reiniciar dispositivo e desligar dispositivo.
- Resultado detalhado por plataforma.

## 2. Endpoints Encontrados

### Audio tracks

Arquivo: `backend/api/v1/audio/tracks.py`

- `GET /audio/tracks/`
- `GET /audio/tracks/statistics/overview`
- `GET /audio/tracks/active/list`
- `GET /audio/tracks/by-category/{category}`
- `GET /audio/tracks/by-duration`
- `GET /audio/tracks/{track_id}`
- `POST /audio/tracks/`
- `POST /audio/tracks/upload`
- `PUT /audio/tracks/{track_id}`
- `DELETE /audio/tracks/{track_id}`
- `PATCH /audio/tracks/{track_id}/status`

Existe:

- Upload simples de uma faixa.
- Validacao de MIME/extensao.
- CRUD basico.
- Filtro por categoria/status/duracao.

Falta:

- `POST /audio/tracks/bulk-upload`
- endpoint de operacoes em massa.
- extracao backend de duracao via ffprobe.
- hash/versionamento de audio.
- endpoint de uso da faixa em playlists/spots.

### Audio playlists

Arquivo: `backend/api/v1/audio/playlists.py`

- `GET /audio/playlists/`
- `GET /audio/playlists/{playlist_id}`
- `GET /audio/playlists/{playlist_id}/with-tracks`
- `POST /audio/playlists/`
- `PUT /audio/playlists/{playlist_id}`
- `DELETE /audio/playlists/{playlist_id}`
- `PATCH /audio/playlists/{playlist_id}/status`
- `POST /audio/playlists/{playlist_id}/tracks/{track_id}`
- `DELETE /audio/playlists/{playlist_id}/tracks/{track_id}`
- `PUT /audio/playlists/{playlist_id}/tracks/reorder`
- `GET /audio/playlists/statistics/overview`
- `GET /audio/playlists/active/list`
- `GET /audio/playlists/by-device/{device_id}`

Existe:

- Playlist com `track_ids` em JSON.
- Volume padrao.
- Loop.
- Shuffle.
- Agenda simples com `schedule_enabled`, `schedule_start_time`, `schedule_end_time`, `schedule_days`.
- Invalidacao de cache de devices afetados ao atualizar playlist.

Falta:

- Playlist por pasta.
- Playlist item relacional.
- Agendamento multiplo por horario.
- Prioridade.
- Spots.
- Regras de conflito entre agendas.

### Audio do player

Arquivo: `backend/api/v1/audio/devices.py`

- `GET /audio/devices/{device_id}/playlist`

Observacao:

- Existe endpoint separado de playlist de audio por device.
- O player principal tambem recebe `audio_playlist` dentro de `/devices/{device_id}/playlist`.

### Player / dispositivos / pareamento

Arquivo: `backend/api/v1/devices.py`

- `POST /devices/pair-request`
- `GET /devices/by-code/{code}/status`
- `GET /devices/{device_id}/playlist`
- `POST /devices/{device_id}/heartbeat`
- `POST /devices/{device_id}/playback-log`
- `POST /devices/{device_id}/pair-confirm`
- `GET /devices/{device_id}/metrics`
- `GET /devices/{device_id}/sessions`
- `POST /devices/{device_id}/command`
- `GET /devices/{device_id}/commands`
- `GET /devices/{device_id}/commands/pending`
- `GET /devices/{device_id}/playlist/updates`
- `POST /devices/{device_id}/commands/{command_id}/ack`
- `POST /devices/{device_id}/revoke-token`

Existe:

- Pareamento por codigo.
- Device token.
- Playlist sync por token.
- Heartbeat.
- Comandos remotos.
- ACK de comando.
- SSE para updates.
- Revogar token.

Falta:

- `pairing_version` ou `token_version`.
- Invalidar automaticamente token antigo quando pairing_code muda.
- Estado `requires_repairing`.
- Comandos de desligamento fisico/restart fisico.
- Estados received/executing/expired.

### Logs

Encontrados:

- `playback_logs`
- `view_reports`
- `device_events`
- `device_commands`

Falta:

- Log especifico de execucao de audio.
- Log de spot.
- Log de musica atual.
- Log de falha de radio/audio.

## 3. Models / Tabelas Encontradas

### AudioTrack

Arquivo: `backend/core/models.py`

Campos:

- `id`
- `tenant_id`
- `name`
- `description`
- `file_url`
- `mime_type`
- `file_size`
- `duration_seconds`
- `category`
- `status`
- `notes`
- `created_at`
- `updated_at`

Existe categoria como enum:

- `music`
- `jingle`
- `announcement`
- `ambient`
- `other`

Limite:

- Categoria e apenas campo na faixa, nao uma entidade/pasta.

### AudioFolder

Nao existe.

Necessario criar:

- `audio_folders`
- `audio_folder_tracks`

### AudioPlaylist

Campos:

- `id`
- `tenant_id`
- `name`
- `description`
- `status`
- `volume_default`
- `loop_enabled`
- `shuffle_enabled`
- `schedule_enabled`
- `schedule_start_time`
- `schedule_end_time`
- `schedule_days`
- `track_ids`
- `track_volumes`
- `created_at`
- `updated_at`

Limite:

- Usa `track_ids` JSON.
- Nao existe item relacional.
- Nao mistura pasta + faixa como item.
- Agenda e unica por playlist.

### PlaylistItem

Nao existe para audio.

Necessario criar:

- `audio_playlist_items`

### AudioSchedule

Nao existe como tabela propria.

Existe parcialmente dentro de `audio_playlists`:

- `schedule_enabled`
- `schedule_start_time`
- `schedule_end_time`
- `schedule_days`

Necessario criar:

- `audio_playlist_schedules`

### SpotSchedule

Nao existe.

Necessario criar:

- `audio_spots`
- `audio_spot_schedules`

### Device

Existe com:

- `pairing_code`
- `device_token`
- `status`
- `is_blocked`
- `current_campaign_id`
- `audio_playlist_id`
- `audio_volume`
- `player_version`
- `os`
- `storage_used`
- `last_seen_at`

Falta:

- `pairing_version`
- `token_version`
- `requires_repairing`
- estado atual de audio/musica.

### DeviceCommand

Existe com:

- `command_type`
- `payload`
- `status`
- `requested_by`
- `requested_at`
- `sent_at`
- `executed_at`
- `error_message`

Estados atuais:

- pending
- sent
- executed
- failed
- cancelled

Faltam:

- received
- executing
- completed separado de executed, se desejado
- expired
- timeout/expiracao persistida

### DevicePairing / Sessions

Existem:

- `DevicePairingCode`
- `DeviceSession`

Observacao:

- Player atual parece operar principalmente com `device.device_token`.
- `DeviceSession` existe, mas o fluxo principal usa `device_token`.

Risco:

- Se `pairing_code` muda mas `device_token` continua igual, player antigo segue sincronizando.

### PlaybackLog / PlayerState

Existe:

- `PlaybackLog` para midia visual.

Nao existe:

- `PlayerState` persistido dedicado.
- `AudioPlaybackLog`.
- `CurrentAudioState`.

## 4. Schemas / Payloads

### AudioTrack schemas

Existem:

- `AudioTrackCreate`
- `AudioTrackUpdate`
- `AudioTrackResponse`

Falta:

- `AudioTrackBulkUploadResponse`
- `AudioTrackBulkAction`
- `AudioFolderCreate/Update/Response`
- campos de hash/versionamento se cache forte for aplicado ao audio.

### AudioPlaylist schemas

Existem:

- `AudioPlaylistCreate`
- `AudioPlaylistUpdate`
- `AudioPlaylistResponse`

Falta:

- `AudioPlaylistItemCreate/Update/Response`
- `AudioPlaylistScheduleCreate/Update/Response`
- `AudioSpotCreate/Update/Response`
- `AudioSpotScheduleCreate/Update/Response`

### Commands schemas

Existem:

- `DeviceCommandCreate`
- `DeviceCommandResponse`
- `DeviceCommandAck`

Falta:

- payload com status `received/executing`.
- endpoint/DTO para ACK em etapas.
- `expires_at`.
- `result`.

## 5. Mocks, Hardcoded, localStorage e Simulacoes

### localStorage real/esperado

- `frontend/src/player-core/storage.js` usa localStorage para pareamento:
  - `pw_player_code`
  - `pw_player_device_id`
  - `pw_player_device_token`
- Isso e aceitavel para o player guardar credenciais, mas precisa invalidar token antigo no backend.

### IndexedDB

- `PlaylistCache` usa IndexedDB para cache da playlist.
- Isso e comportamento real do player, nao mock.

### Hardcoded

- `PLAYER_VERSION = "3.1.0"` em `Player.jsx`.
- `VALID_COMMANDS = {"restart", "sync", "clear_cache", "screenshot", "refresh_playlist"}` no backend.
- `COMMAND_HANDLERS` suporta mais comandos no frontend que o backend nao aceita (`set_volume`, `mute`, `unmute`).
- `AudioTrackFormModal` calcula duracao no browser com `new Audio()`, mas isso nao deve ser a fonte final confiavel.

### Simulacao / incompleto

- Comando `restart` e apenas soft reset do app, nao restart real.
- Nao ha comando real de desligar dispositivo.
- Nao ha suporte nativo por plataforma no comando de energia.
- Botao screenshot existe no backend como comando valido, mas handler do player nao implementa `screenshot`.

## 6. Como o Player Decide Hoje

### Qual midia visual tocar

1. `Player.jsx` chama `getDevicePlaylist(deviceId, token)`.
2. Backend `GET /devices/{device_id}/playlist` resolve campanha ativa.
3. Backend usa `campaign.media_order` ou `campaign.media_ids`.
4. Backend monta lista de midias.
5. Player guarda em `playlist`.
6. Player toca `playlist[currentIndex]`.
7. Ao terminar/timer, chama `advanceMedia`.

### Qual audio tocar

1. Backend inclui `audio_playlist` no payload de `/devices/{device_id}/playlist`.
2. Prioridade atual:
   - playlist de audio da campanha, se existir;
   - senao playlist de audio do device.
3. `AudioPlayer` recebe `audioPlaylist`.
4. `AudioPlayer` toca tracks em ordem.
5. Usa `audioPlaylist.loop`.
6. Nao foi encontrado uso real de shuffle dentro de `AudioPlayer`.

### Se radio fica ativa ou nao

Hoje:

- `AudioPlayer` fica habilitado quando `phase === "playing"`.
- Nao ha regra clara considerando audio do video.
- Nao ha pausa automatica da radio quando video com audio toca.
- `videoMuted` controla se video fica mudo, mas nao resolve todos os modos.

### Como recebe comandos

1. Player faz polling em `/devices/{device_id}/commands/pending`.
2. Backend retorna comandos pending e marca como sent.
3. Player executa handler local.
4. Player envia ACK em `/devices/{device_id}/commands/{command_id}/ack`.
5. Backend marca executed ou failed.

### Como valida o dispositivo pareado

1. Player guarda `device_id` e `device_token`.
2. Backend valida header `X-Device-Token`.
3. Se token existe e device nao esta bloqueado, libera.
4. Nao ha validacao de versao de pareamento.

### Como atualiza configuracoes

- Polling de playlist.
- Heartbeat compara `config_version`.
- SSE `playlist_invalidated` forca reload.
- Redis cacheia playlist por device.

## 7. Incompletos Principais

### Radio / Audio

- Upload multiplo nao existe.
- Pastas nao existem.
- Playlist item relacional nao existe.
- Agendamento avancado nao existe.
- Spots recorrentes nao existem.
- Selecao em massa nao existe.
- Shuffle no player de audio parece nao implementado.
- Logs de audio nao existem.

### Player

- Desligamento real nao existe.
- Restart real de app/dispositivo nao existe.
- Screenshot valido no backend, mas handler nao existe.
- Pairing code pode mudar sem invalidar token antigo.
- Radio e audio visual nao tem politica de conflito.
- Overlay de musica atual nao existe.

## 8. Riscos Tecnicos

1. `track_ids` em JSON limita integridade e agendamento.
2. Player web puro nao consegue desligar dispositivo fisico.
3. Android/Capacitor, Electron, Linux e Windows exigem implementacoes nativas diferentes para energia.
4. Se token antigo nao for revogado, trocar `pairing_code` nao protege o dispositivo.
5. Misturar radio e audio de video sem regra gera experiencia ruim.
6. Calcular duracao no browser pode ser inconsistente; backend deve ser fonte final.
7. Upload multiplo precisa tolerar falha parcial.
8. Spots podem criar conflitos se interromperem musicas sem regra clara.

## 9. Plano de Implementacao por Prioridade

### P0 — Segurança e controle do Player

- Criar regra de invalidacao de token ao regenerar pairing code.
- Adicionar `pairing_version` ou `token_version`.
- Recusar sync com token antigo.
- Expandir estados de comando.
- Separar comandos:
  - `restart_app`
  - `reload_player`
  - `restart_device`
  - `shutdown_device`
- Implementar fallback por plataforma:
  - web: nao suportado, retornar failed claro;
  - Capacitor/APK: plugin nativo;
  - Electron/desktop: API nativa;
  - Linux/Windows: comando controlado no shell/servico.

### P1 — Regras de conflito audio visual vs radio

- Criar campo de politica de audio em campanha/device:
  - `radio_only`
  - `media_audio_only`
  - `mix`
  - `auto`
  - `muted_video_with_radio`
- Player deve decidir `videoMuted` e `audioEnabled` por politica.
- Adicionar metadata `has_audio` em video futuramente.

### P2 — Upload multiplo e selecao multipla

- Criar `POST /audio/tracks/bulk-upload`.
- Frontend permitir input `multiple`.
- Mostrar progresso por arquivo.
- Retornar sucesso/falha por item.
- Criar acoes em massa: mover pasta, arquivar, ativar, adicionar a playlist.

### P3 — Pastas e playlists relacionais

- Criar `audio_folders`.
- Criar `audio_folder_tracks`.
- Criar `audio_playlist_items`.
- Permitir item tipo `track` ou `folder`.
- Preservar compatibilidade com `track_ids` durante migracao.

### P4 — Agendamento e spots

- Criar `audio_playlist_schedules`.
- Criar `audio_spots`.
- Criar `audio_spot_schedules`.
- Definir prioridade e interrupcao.
- Player receber agenda resolvida.

### P5 — Player UI e logs

- Overlay da musica atual.
- Configuracoes de overlay por device/campanha.
- Reportar musica atual no heartbeat.
- Criar logs de audio e spot.

## 10. Migrations Necessarias

### Player / dispositivos

- Adicionar em `devices`:
  - `pairing_version`
  - `token_version`
  - `requires_repairing`
  - `audio_policy`
  - `show_current_audio_title`
  - `audio_overlay_position`
  - `audio_overlay_duration_seconds`
  - `audio_overlay_opacity`
  - `audio_overlay_font_size`

### Comandos

- Alterar `device_commands`:
  - adicionar `received_at`
  - adicionar `started_at`
  - adicionar `finished_at`
  - adicionar `expires_at`
  - adicionar `result`
  - expandir enum/status.

### Audio

- Criar `audio_folders`.
- Criar `audio_folder_tracks`.
- Criar `audio_playlist_items`.
- Criar `audio_playlist_schedules`.
- Criar `audio_spots`.
- Criar `audio_spot_schedules`.
- Criar `audio_playback_logs`.

## 11. Endpoints Necessarios

### Upload e massa

- `POST /audio/tracks/bulk-upload`
- `POST /audio/tracks/bulk-action`
- `GET /audio/tracks/{id}/usage`

### Pastas

- `GET /audio/folders`
- `POST /audio/folders`
- `PUT /audio/folders/{id}`
- `DELETE /audio/folders/{id}`
- `POST /audio/folders/{id}/tracks`
- `DELETE /audio/folders/{id}/tracks/{track_id}`

### Playlist relacional

- `POST /audio/playlists/{id}/items`
- `PUT /audio/playlists/{id}/items/{item_id}`
- `DELETE /audio/playlists/{id}/items/{item_id}`
- `PATCH /audio/playlists/{id}/items/reorder`

### Agenda

- `GET /audio/playlists/{id}/schedules`
- `POST /audio/playlists/{id}/schedules`
- `PUT /audio/schedules/{id}`
- `DELETE /audio/schedules/{id}`

### Spots

- `GET /audio/spots`
- `POST /audio/spots`
- `PUT /audio/spots/{id}`
- `DELETE /audio/spots/{id}`
- `POST /audio/spots/{id}/schedules`

### Player/comandos

- `POST /devices/{id}/commands/{command_id}/received`
- `POST /devices/{id}/commands/{command_id}/started`
- `POST /devices/{id}/commands/{command_id}/result`
- `POST /devices/{id}/repairing/reset`
- `POST /devices/{id}/pairing-code/regenerate`

## 12. Componentes Frontend Necessarios

- `AudioBulkUploadModal`
- `AudioBulkActionsToolbar`
- `AudioFolderList`
- `AudioFolderFormModal`
- `AudioPlaylistItemsBuilder`
- `AudioScheduleFormModal`
- `AudioSpotList`
- `AudioSpotFormModal`
- `AudioSpotScheduleForm`
- `AudioNowPlayingOverlay`
- `DeviceCommandTimeline`
- `DevicePairingResetDialog`
- `AudioPolicySelector`

## 13. Criterios de Aceite

### Upload multiplo

- Selecionar varios arquivos.
- Cada arquivo mostra progresso/status.
- Falha de um arquivo nao cancela os outros.
- Audios validos aparecem na listagem.

### Selecao multipla

- Selecionar varias faixas.
- Mover para pasta.
- Adicionar a playlist.
- Arquivar/ativar em lote.

### Pastas

- Criar pasta.
- Adicionar/remover faixas.
- Usar pasta como fonte de playlist.

### Agenda

- Playlist Manha toca apenas no horario configurado.
- Playlist sem data final continua ativa.
- Dias da semana sao respeitados.

### Spots

- Spot toca a cada X minutos.
- Spot respeita horario/data/dia.
- Spot entre musicas nao interrompe faixa quando configurado assim.
- Spot com prioridade pode interromper quando permitido.

### Player comandos

- Comando enviado vira pending.
- Player busca e marca received/executing.
- Ao executar, marca completed ou failed.
- Web player retorna failed claro para desligamento fisico.
- APK/desktop executa conforme suporte nativo.

### Pareamento

- Regenerar pairing code invalida token antigo.
- Player antigo recebe unauthorized/requires_repairing.
- Player precisa parear novamente.

### Audio visual vs radio

- `radio_only`: video mudo, radio toca.
- `media_audio_only`: radio pausa, video com audio toca.
- `mix`: ambos tocam.
- `auto`: video com audio pausa radio; sem audio mantem radio.
- `muted_video_with_radio`: video sempre mudo e radio ativa.

### Overlay musica atual

- Mostra nome da musica atual.
- Posicao configuravel.
- Duração configuravel.
- Nao cobre area principal de forma agressiva.

## 14. Checklist Tecnico

- [ ] Confirmar estrategia de comando nativo por plataforma.
- [ ] Definir politica padrao de conflito audio visual vs radio.
- [ ] Criar migrations de device/comandos.
- [ ] Corrigir invalidacao de token ao mudar pairing code.
- [ ] Expandir estados de comando.
- [ ] Criar upload multiplo no backend.
- [ ] Criar upload multiplo no frontend.
- [ ] Criar pastas de audio.
- [ ] Criar playlist items relacionais.
- [ ] Criar agenda de radio.
- [ ] Criar spots recorrentes.
- [ ] Atualizar player para agenda/spots.
- [ ] Criar overlay de musica atual.
- [ ] Criar logs de audio.
- [ ] Criar testes backend.
- [ ] Criar testes frontend.
- [ ] Criar teste manual em web player e APK/desktop quando disponivel.
