# SPEC 007 — Design tecnico

## Arquitetura alvo por fase

### Fase A — Consolidacao do que ja existe

Objetivo: estabilizar SPECs 001, 004, 005 e 006.

- Rodar testes focados no Docker.
- Garantir migrations aplicadas.
- Validar que o payload de `GET /devices/{id}/playlist` inclui:
  - campanha;
  - midias filtradas por periodo;
  - `duration_seconds`, `display_duration_seconds`, `file_hash`, `file_version`;
  - `audio_playlist`;
  - `audio_policy_effective`;
  - `osd_config`.

### Fase B — Playlist visual real

Backend ja existe:

- `campaign_playlist_items`;
- `GET /campaigns/{id}/items`;
- `POST /campaigns/{id}/items`;
- `PUT /campaigns/{id}/items/{item_id}`;
- `DELETE /campaigns/{id}/items/{item_id}`;
- `PATCH /campaigns/{id}/items/reorder`.

Frontend alvo:

- criar componente `CampaignPlaylistBuilder`;
- criar drawer `AddCampaignMediaDrawer`;
- usar `@hello-pangea/dnd` ja instalado para ordenar;
- manter botoes subir/descer como fallback acessivel;
- no submit de campanha, salvar dados gerais em `/campaigns/{id}` e itens nos endpoints relacionais.

### Fase C — Radio v2

Novas entidades:

- `audio_playlist_items`: substitui `AudioPlaylist.track_ids` como fonte principal.
- `audio_folders`: pastas/grupos com periodo/data/hora/status.
- `audio_folder_tracks`: N:N entre pasta e faixa.
- `audio_playlist_folder_schedules`: agenda de pastas numa playlist/radio.
- `audio_spots`: faixa ou arquivo de spot com tipo de insercao.
- `audio_spot_schedules`: intervalo, janela e prioridade.
- `audio_playback_events`: log de musica/spot tocado pelo player.

Servicos:

- `services/audio_schedule_resolver.py`: resolve pasta/faixas validas para `now`.
- `services/audio_spot_scheduler.py`: calcula proximo spot elegivel.
- `services/audio_shuffle.py`: cria fila embaralhada sem repeticao imediata.

### Fase D — Audio manager do player

Criar `frontend/src/player-core/audioManager.js` ou hook equivalente.

Estados:

- `radio`: musica ambiente normal;
- `media_audio`: audio de video/midia visual;
- `spot`: insercao prioritaria;
- `silent`: sem audio.

Prioridade inicial:

1. Spot ativo.
2. Midia visual com politica `media_audio_only` ou `auto` + `has_audio=true`.
3. Radio.
4. Silencio.

Transicoes:

- fade out/in configuravel;
- nunca dois players ativos com volume audivel ao mesmo tempo, exceto politica explicita `mix`.

## Fluxos de usuario

### Upload de video

1. Admin abre Biblioteca de Midias.
2. Seleciona arquivo de video.
3. Frontend envia multipart para `POST /media/upload`.
4. Backend valida arquivo, roda `ffprobe`, salva duracao e hash.
5. UI exibe duracao detectada.

### Periodo de midia

1. Admin informa inicio/fim no cadastro.
2. Backend valida `ends_at >= starts_at`.
3. Player recebe apenas midias vigentes.
4. UI lista status `ativa/agendada/expirada`.

### Substituir midia

1. Admin escolhe "Substituir arquivo".
2. Backend troca arquivo mantendo `media.id`.
3. Backend cria `media_versions`, incrementa `file_version`, atualiza hash.
4. Campanhas afetadas ganham novo `config_version`.
5. Player recarrega playlist e baixa/exibe novo arquivo.

### Playlist visual item a item

1. Admin cria/edita campanha.
2. Aba Midias mostra itens atuais, nao apenas checkboxes.
3. Admin adiciona midia via drawer.
4. Admin ordena e configura cada item.
5. Backend salva em `campaign_playlist_items`.
6. Player respeita `order_index`.

### Radio por pastas e spots

1. Admin faz upload multiplo de audio.
2. Admin cria pastas Manha/Tarde/Noite.
3. Admin vincula faixas nas pastas.
4. Admin programa pastas por horario.
5. Admin cria spot "Anuncio" a cada 30 min.
6. Player recebe grade atual e executa sem sobreposicao.

## Regras de compatibilidade

- `AudioPlaylist.track_ids` continua sendo aceito ate radio v2 estar em producao.
- Player antigo recebe payload atual sem quebrar.
- Player novo deve preferir `audio_playlist.items` quando existir, e cair para `tracks`.
- `campaign.media_ids/media_order` continuam write-through ate remocao futura.

## Riscos de regressao

- Mudanca em playlist pode quebrar campanhas antigas. Mitigacao: fallback legado e testes com campanha antiga.
- Agenda de audio pode causar silencio indevido. Mitigacao: fallback para playlist padrao ou radio off claro.
- Spot pode sobrepor musica. Mitigacao: audio manager central com estado unico.
- Upload multiplo pode gerar falha parcial confusa. Mitigacao: resultado por arquivo.
- Comando shutdown pode parecer sucesso em plataforma sem suporte. Mitigacao: `platform_unsupported=true` e mensagem no painel.
