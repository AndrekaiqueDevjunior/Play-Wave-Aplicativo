# SPEC 001 — Design Tecnico

## Resumo

A funcionalidade sera implementada sobre a arquitetura atual do PlayWave, usando FastAPI, SQLAlchemy, Alembic, Redis e React/Vite.

O design preserva compatibilidade com campanhas existentes, pois atualmente campanhas referenciam midias por JSON em `campaigns.media_ids` e `campaigns.media_order`.

## Arquitetura atual relacionada

### Backend

- `backend/api/v1/media.py`: endpoints e regras de midia.
- `backend/core/models.py`: models `Media`, `Campaign`, `Device`.
- `backend/core/schemas_completos.py`: DTOs/schemas.
- `backend/crud/entidades/crud_media.py`: CRUD base de midia.
- `backend/api/v1/devices.py`: builder de playlist do player.
- `backend/api/v1/campaigns.py`: vinculo campanha/midias e invalidacao.
- `backend/main.py`: servico de arquivos `/uploads`.

### Frontend

- `frontend/src/pages/BibliotecaMidias.jsx`: listagem.
- `frontend/src/components/media/MediaFormModal.jsx`: criacao/edicao.
- `frontend/src/api/midias.js`: cliente da API.
- `frontend/src/components/campaigns/CampaignFormModal.jsx`: selecao de midias na campanha.
- `frontend/src/pages/CampanhaPreview.jsx`: preview.

### Player

- `frontend/src/pages/Player.jsx`: ciclo de sincronizacao, playlist, heartbeat e execucao.
- `frontend/src/components/player/MediaRenderer.jsx`: renderizacao de video/audio/imagem/url.
- `frontend/src/player-core/storage.js`: cache local/pairing.
- `frontend/src/api/dispositivos.js`: chamadas de playlist, heartbeat e playback.

## Fluxo de upload

1. Frontend envia `multipart/form-data` para `/media/upload`.
2. Backend valida arquivo por MIME/extensao.
3. Backend salva arquivo em `uploads/media`.
4. Backend calcula `file_hash`.
5. Backend usa `ffprobe` para video/audio.
6. Backend salva:
   - `duration_seconds`;
   - `display_duration_seconds`;
   - `file_size`;
   - `mime_type`;
   - `file_hash`;
   - `file_version`.
7. Backend cria registro inicial em `media_versions`.
8. Frontend invalida query/listagem.

## Fluxo de edicao

1. Frontend envia `PUT /media/{id}`.
2. Backend valida datas.
3. Backend atualiza metadados.
4. Se alteracao impactar player, backend atualiza campanhas afetadas.
5. Backend invalida cache das playlists dos devices afetados.

## Fluxo de substituicao de arquivo

1. Frontend envia novo arquivo para `POST /media/{id}/replace-file`.
2. Backend busca a midia existente.
3. Backend valida permissao e compatibilidade de tipo.
4. Backend salva novo arquivo.
5. Backend recalcula metadados.
6. Backend incrementa `file_version`.
7. Backend atualiza a mesma linha em `media`.
8. Backend marca versoes antigas como `is_current = false`.
9. Backend cria nova linha em `media_versions`.
10. Backend identifica campanhas que usam a midia.
11. Backend atualiza `config_version` dessas campanhas.
12. Backend invalida cache Redis dos devices afetados.
13. Backend publica evento de playlist invalidada.

## Fluxo de sync do player

1. Player chama `GET /devices/{device_id}/playlist`.
2. Backend resolve campanha ativa.
3. Backend ordena midias por `media_order` ou `media_ids`.
4. Backend filtra midias invalidas.
5. Backend retorna payload com versao/hash/duracoes.
6. Player executa:
   - video/audio ate o fim se `duration` vier nulo;
   - imagem/link pelo tempo de `duration`.
7. Player registra playback.

## Status de midia

### Status persistido

Atualmente existe enum:

- `available`;
- `processing`;
- `error`.

### Status calculado

Deve ser calculado com base em:

- `status`;
- `is_active`;
- `starts_at`;
- `ends_at`;
- data atual.

Valores:

- `active`;
- `scheduled`;
- `expired`;
- `inactive`;
- `processing`;
- `error`.

## Decisoes tecnicas

- Usar `ffprobe` para detectar duracao real.
- Usar SHA-256 para `file_hash`.
- Usar inteiro incremental em `file_version`.
- Manter `duration` como legado.
- Preferir `display_duration_seconds` para tempo operacional.
- Nao criar novo `media_id` na substituicao.
- Invalidar cache apenas de devices impactados quando houver campanhas identificadas.
- Bloquear delete de midia em uso por padrao.

## Pontos parcialmente existentes

- `MediaVersion` ja esta modelado.
- Endpoint `replace-file` existe no estado atual do projeto.
- `duration_seconds`, `display_duration_seconds`, `starts_at`, `ends_at`, `file_hash`, `file_version` ja aparecem nos models/schemas atuais.
- Player ja trata video/audio sem `duration` como playback natural.

## Lacunas de design

- Processamento ainda pode ocorrer na request, o ideal futuro e Celery.
- Thumbnail de video ainda precisa geracao real.
- `campaigns.media_ids` e `campaigns.media_order` ainda sao JSON.
- Nao existe tabela `device_cache_status`.
- Nao existe tabela `media_processing_jobs`.
- Frontend de campanha ainda usa selecao por checkbox/lista simples.

## Riscos e mitigacoes

### Risco: ffprobe ausente

Mitigacao:

- Adicionar `ffmpeg` no Dockerfile.
- Registrar metadata `ffprobe_available=false` quando ausente.

### Risco: upload pesado bloqueando request

Mitigacao:

- Fase 1: processamento sincrono.
- Fase 2: migrar para Celery com status `processing`.

### Risco: cache antigo no player

Mitigacao:

- Enviar `file_hash` e `file_version`.
- Player compara antes de reutilizar cache.

### Risco: campanha quebrada apos substituicao

Mitigacao:

- Manter `media_id`.
- Nao alterar `campaign.media_ids`.
- Nao alterar `campaign.media_order`.

## Criterio de pronto tecnico

- Banco migrado.
- Upload detecta duracao real.
- Edicao valida datas.
- Substituicao preserva `media_id`.
- Historico registra versao.
- Player recebe hash/versao/duracoes.
- Midia expirada/agendada nao toca.
- Frontend mostra duracao, periodo e status.
