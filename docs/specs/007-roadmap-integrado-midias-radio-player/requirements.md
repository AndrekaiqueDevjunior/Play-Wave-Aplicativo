# SPEC 007 — Roadmap integrado de midias, playlists, radio indoor e player

Status: especificacao inicial
Data: 2026-05-23
Projeto: PlayWave

## Objetivo

Consolidar o estado atual do PlayWave e definir a evolucao tecnica para fechar as melhorias de midia, campanha/playlist, radio indoor, comandos remotos, pareamento, conflitos de audio e overlay de musica atual, preservando compatibilidade com o que ja foi implementado nas SPECs 001, 003, 004, 005 e 006.

## Contexto

O projeto ja recebeu varias partes das funcionalidades pedidas:

- `docs/specs/001-midias-inteligentes/`: duracao real, periodo de exibicao, substituicao segura e versionamento de midia.
- `docs/specs/003-player-comandos-nativos/`: ciclo de vida de comandos e bridge nativa para desligar/reiniciar.
- `docs/specs/004-pareamento-revocacao/`: token version, force-repair, invalidacao de pareamento e auditoria.
- `docs/specs/005-conflito-audio-midia/`: politica de audio entre radio e midia visual.
- `docs/specs/006-osd-musica-atual/`: overlay configuravel com nome da musica atual.

O maior buraco restante esta em **radio indoor v2** e na **UI de playlist real de campanha**. O backend de itens relacionais de campanha ja existe, mas a tela principal ainda usa selecao por checkbox em `CampaignFormModal.jsx`.

## Arquivos analisados

### Backend

- `backend/core/models.py`
- `backend/core/schemas_completos.py`
- `backend/api/v1/media.py`
- `backend/api/v1/campaigns.py`
- `backend/api/v1/audio/tracks.py`
- `backend/api/v1/audio/playlists.py`
- `backend/api/v1/audio/devices.py`
- `backend/api/v1/devices.py`
- `backend/api/v1/tenants.py`
- `backend/services/audio_policy_resolver.py`
- `backend/services/osd_config_resolver.py`
- `backend/tasks/media/backfill_has_audio.py`
- `backend/alembic/versions/20260520_1000_media_metadata_versions.py`
- `backend/alembic/versions/20260520_1400_campaign_playlist_items.py`
- `backend/alembic/versions/20260522_1000_command_defaults_and_index.py`
- `backend/alembic/versions/20260522_1500_device_pairing_events.py`
- `backend/alembic/versions/20260522_2000_audio_policy.py`
- `backend/alembic/versions/20260523_1000_osd_config.py`

### Frontend Admin

- `frontend/src/pages/BibliotecaMidias.jsx`
- `frontend/src/components/media/MediaFormModal.jsx`
- `frontend/src/pages/Campanhas.jsx`
- `frontend/src/components/campaigns/CampaignFormModal.jsx`
- `frontend/src/pages/FaixasAudio.jsx`
- `frontend/src/components/audio/AudioTrackFormModal.jsx`
- `frontend/src/pages/PlaylistsSonoras.jsx`
- `frontend/src/components/audio/AudioPlaylistsFormModal.jsx`
- `frontend/src/pages/DispositivoDetalhe.jsx`
- `frontend/src/pages/ConfigEmpresa.jsx`
- `frontend/src/api/midias.js`
- `frontend/src/api/campanhas.js`
- `frontend/src/api/audio.js`
- `frontend/src/api/dispositivos.js`
- `frontend/src/api/tenants.js`

### Player

- `frontend/src/pages/Player.jsx`
- `frontend/src/components/audio/AudioPlayer.jsx`
- `frontend/src/components/player/MediaRenderer.jsx`
- `frontend/src/components/player/PlayerOSD.jsx`
- `frontend/src/components/player/PairingScreen.jsx`
- `frontend/src/player-core/commands.js`
- `frontend/src/player-core/platform.js`
- `frontend/src/player-core/repair.js`
- `frontend/src/player-core/storage.js`
- `frontend/src/player-core/network.js`

### Testes existentes relevantes

- `backend/tests/test_media_rules.py`
- `backend/tests/test_audio_policy_005.py`
- `backend/tests/test_audio_backfill_005.py`
- `backend/tests/test_osd_config_006.py`
- `backend/tests/test_pairing_004.py`
- `frontend/src/__tests__/audio_conflict_resolver.test.jsx`
- `frontend/src/__tests__/osd_audio_player.test.jsx`
- `frontend/src/__tests__/repair.test.js`
- `frontend/src/__tests__/pairing_storage.test.js`

## Estado atual encontrado

### Ja existe

- Upload de midia em `POST /media/upload` com `ffprobe`, `duration_seconds`, `display_duration_seconds`, `file_hash`, `file_version`, `starts_at`, `ends_at` e `has_audio`.
- Fallback de duracao: imagem e URL usam duracao manual/default; video/audio podem tocar ate o fim.
- Periodo de midia no banco e filtro no payload do player via `_media_is_valid_for_player`.
- Substituicao de arquivo em `POST /media/{id}/replace-file`, mantendo `media_id`, incrementando `file_version`, criando `media_versions`, tocando campanhas afetadas e invalidando cache.
- Itens relacionais de campanha em `campaign_playlist_items` com `order_index`, duracao customizada, periodo por item, ativo/inativo e repeat count.
- Endpoints de item de campanha: listar, adicionar em bulk, editar, remover e reordenar.
- Politica de audio por hierarquia `media > campaign > device > tenant > auto`.
- Backfill manual/Celery de `has_audio`.
- Pareamento com `token_version`, `requires_repairing`, `forceRepair`, SSE `pairing:revoked` e auditoria em `device_pairing_events`.
- Comandos remotos com ciclo de vida recebido/iniciado/ack, status expandido e `platform_unsupported`.
- OSD de musica atual com config por tenant/device e heartbeat com `current_audio_track_*`.
- Radio indoor basica: `audio_tracks`, `audio_playlists`, upload individual de faixa, playlist com `track_ids`, volume, loop e shuffle.

### Existe parcialmente

- Frontend de campanha ainda usa checkbox simples em `CampaignFormModal.jsx`, mesmo o backend ja tendo itens relacionais.
- Playlist sonora permite adicionar faixas e reordenar por drag simples, mas persiste em JSON `track_ids`, nao em tabela de itens.
- `shuffle_enabled` existe em `AudioPlaylist`, mas o player ainda precisa de estrategia anti-repeticao clara.
- Upload de audio detecta duracao no browser antes de enviar; backend tambem precisa ser fonte oficial usando `ffprobe`.
- Comando de desligar funciona apenas onde existe bridge nativa real (`window.__ELECTRON__`, `PlayWaveNative`, `AndroidPlayer`). Web puro deve falhar com motivo claro.
- Cache do player tem base em `file_hash/file_version`, mas status de cache por midia/dispositivo ainda nao existe.
- Documentacao de provisionamento nativo existe em parte, mas validacao real em Windows/Linux/APK ainda depende de ambiente.

### Falta

- Upload multiplo de audio com feedback por arquivo e erro parcial.
- Tabela relacional de itens de playlist de audio.
- Pastas/grupos de audio com periodo, horario, status e membership N:N.
- Programacao de radio por pasta/horario com conflito/prioridade.
- Spots/insercoes com intervalo recorrente e log de execucao.
- Radio/ponto como entidade explicita, caso o produto diferencie device, grupo, ambiente/local e playlist.
- Gerenciador central de audio do player para priorizar radio, video com audio, spot e audio de midia.
- UI completa para playlist de campanha item a item.
- UI de status/log de comandos mais rica e validacao E2E de desligar/reiniciar por plataforma.
- Testes E2E para as jornadas completas pedidas.

## Requisitos funcionais

### RF007-01 — Fechar midia inteligente

Consolidar SPEC 001 como comportamento padrao:

- video tem duracao real detectada no backend;
- video nao exige tempo manual;
- imagem e URL usam duracao manual ou default configuravel;
- periodo da midia filtra o payload do player;
- substituicao mantem `media_id`, vinculos e ordem.

### RF007-02 — Playlist real de campanha no frontend

Substituir o fluxo principal de checkbox por construtor de itens:

- adicionar midias individualmente ou em lote controlado;
- cada inclusao vira um `campaign_playlist_item`;
- permitir ordenar, ativar/desativar, repetir, definir periodo e duracao por item;
- manter compat com `media_ids/media_order` ate uma futura remocao.

### RF007-03 — Radio indoor v2

Evoluir radio de `AudioPlaylist.track_ids` para modelo relacional:

- upload multiplo de faixas;
- itens de playlist de audio com ordem, volume e ativo/inativo;
- pastas/grupos de audio;
- programacao por horario/data;
- spots recorrentes por intervalo;
- modo sequencial ou embaralhado com anti-repeticao.

### RF007-04 — Audio manager do player

Centralizar decisoes de audio:

- radio normal;
- video com audio;
- spot/insercao;
- audio de midia;
- prioridade e transicoes sem sobreposicao indevida.

### RF007-05 — Comandos remotos nativos

Concluir desligar/reiniciar:

- gerenciador mostra ciclo de vida real;
- plataforma sem suporte retorna falha clara;
- Electron/Linux/Windows/APK usam bridge nativa;
- comandos destrutivos recebem pre-ACK e log final quando possivel.

### RF007-06 — Pareamento revogavel

Manter regra da SPEC 004:

- regenerar codigo invalida token antigo;
- player volta para pareamento via 401/403 ou SSE;
- backend rejeita token antigo por `token_version`.

### RF007-07 — OSD de musica atual

Manter regra da SPEC 006 e ampliar metadados quando existirem:

- exibir nome da faixa;
- atualizar ao trocar;
- permitir desligar/configurar posicao/duracao;
- futuramente exibir artista/pasta/playlist quando o schema tiver esses campos.

## Requisitos nao funcionais

- Payload do player deve continuar compativel durante uma release de transicao.
- Migrations devem preservar dados atuais e criar backfills claros.
- Processamento pesado (`ffprobe`, uploads multiplos, backfills) nao deve travar API em producao.
- Regras de agenda devem ser deterministicamente testaveis com `now` injetavel.
- Player deve preferir fail-safe: se nao sabe se video tem audio, evita misturar indevidamente.

## Decisoes tecnicas

- Substituir midia deve manter o mesmo `media_id`; criar nova midia e atualizar vinculos fica fora do padrao.
- Campanha deve migrar progressivamente para `campaign_playlist_items`, mantendo write-through em `media_ids/media_order`.
- Radio v2 deve usar tabelas relacionais novas, mantendo leitura de `AudioPlaylist.track_ids` como fallback.
- Spots nao devem mixar com musica; comportamento inicial recomendado: tocar no proximo intervalo seguro, pausando radio e retomando depois.
- Shuffle recomendado: embaralhar uma fila completa e tocar ate esgotar antes de reembaralhar, evitando repeticao imediata.

## Fora de escopo imediato

- Remover colunas legadas `campaign.media_ids`, `campaign.media_order`, `campaign.video_muted` sem compat-period.
- Implementar MDM Android completo.
- Criar dashboards avancados de analytics de execucao.
