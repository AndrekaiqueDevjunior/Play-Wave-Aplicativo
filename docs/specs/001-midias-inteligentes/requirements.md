# SPEC 001 — Midias Inteligentes

Status: especificacao inicial  
Data: 2026-05-20  
Projeto: PlayWave

## Objetivo

Evoluir o modulo de midias para que cada midia tenha metadados confiaveis, validade propria, duracao real detectada automaticamente e substituicao segura de arquivo sem quebrar campanhas, playlists ou agendamentos existentes.

## Contexto

O PlayWave e um sistema de midia indoor/digital signage com:

- painel administrativo;
- campanhas/playlists;
- biblioteca de midias;
- dispositivos/players para TVs;
- sincronizacao de playlist pelo backend;
- cache Redis;
- player web com cache local.

Hoje midias ja existem e sao usadas por campanhas atraves de `campaigns.media_ids` e `campaigns.media_order`. O player busca a playlist em `/devices/{device_id}/playlist`.

## Escopo

Esta SPEC cobre:

- upload e cadastro de midias;
- edicao de metadados;
- duracao automatica para video/audio;
- duracao configurada para exibicao;
- periodo de exibicao da midia;
- status calculado de disponibilidade;
- substituicao de arquivo mantendo `media_id`;
- historico/versionamento de arquivo;
- contrato de sincronizacao com player;
- invalidacao de cache quando a midia muda.

Esta SPEC nao cobre:

- construtor relacional completo de playlist de campanha;
- regras avancadas de conflito de campanha;
- central completa de entrega por player;
- radio indoor/spots;
- processamento assincromo completo via Celery, exceto como recomendacao futura.

## Arquivos analisados

### Backend

- `backend/api/v1/media.py`
- `backend/api/v1/campaigns.py`
- `backend/api/v1/devices.py`
- `backend/api/v1/audio/tracks.py`
- `backend/api/v1/audio/playlists.py`
- `backend/api/v1/audio/devices.py`
- `backend/core/models.py`
- `backend/core/schemas_completos.py`
- `backend/crud/entidades/crud_media.py`
- `backend/crud/entidades/crud_campaign.py`
- `backend/crud/entidades/crud_device.py`
- `backend/main.py`
- `backend/alembic/versions/001_initial_migration.py`
- `backend/alembic/versions/20260520_1000_media_metadata_versions.py`

### Frontend

- `frontend/src/api/midias.js`
- `frontend/src/api/dispositivos.js`
- `frontend/src/api/campanhas.js`
- `frontend/src/pages/BibliotecaMidias.jsx`
- `frontend/src/pages/MidiaUpload.jsx`
- `frontend/src/components/media/MediaFormModal.jsx`
- `frontend/src/components/media/MediaThumb.jsx`
- `frontend/src/components/campaigns/CampaignFormModal.jsx`
- `frontend/src/pages/CampanhaPreview.jsx`
- `frontend/src/pages/Player.jsx`
- `frontend/src/components/player/MediaRenderer.jsx`
- `frontend/src/player-core/storage.js`
- `frontend/src/player-core/commands.js`
- `frontend/src/utils/mediaUtils.js`

## Estado atual encontrado

### Ja existe

- Model `Media`.
- Schemas `MediaCreate`, `MediaUpdate`, `MediaResponse`.
- Endpoints administrativos de midia.
- Upload de arquivo em `/media/upload`.
- Listagem, criacao, atualizacao e delecao de midia.
- Campanhas com `media_ids` e `media_order` em JSON.
- Player busca playlist visual por device.
- Player usa cache local de playlist.
- Redis cacheia playlist por dispositivo.
- Player trata video/audio sem duracao como reproducao ate `onEnded`.

### Existe parcialmente

- Campo legado `duration`.
- Status tecnico de midia: `available`, `processing`, `error`.
- Audio tracks tem duracao manual, mas nao esta no escopo principal desta SPEC.
- Campanha usa midias por JSON, ainda sem tabela relacional de itens.
- Player registra playback log.
- Cache local existe, mas ainda nao tem status por midia/dispositivo.

### Faltava ou precisa consolidar

- Duracao real separada de duracao de exibicao.
- Periodo de exibicao por midia.
- Status calculado: ativa, agendada, expirada, inativa.
- Versionamento formal da midia.
- Endpoint de substituicao de arquivo.
- Uso da midia em campanhas para alertas.
- Invalidacao direcionada do cache quando arquivo muda.
- Pipeline robusto de thumbnail/metadados em background.

## Requisitos funcionais

### RF001 — Detectar duracao real de video

Ao fazer upload de video, o sistema deve detectar automaticamente a duracao real do arquivo.

Critérios:

- Salvar a duracao em `duration_seconds`.
- Usuario nao deve ser obrigado a digitar duracao manual.
- Se a extracao falhar, a midia deve indicar erro ou metadata incompleta.
- O erro deve ser amigavel no painel.

### RF002 — Detectar duracao real de audio

Ao fazer upload de audio, o sistema deve detectar automaticamente a duracao real do arquivo.

Critérios:

- Salvar a duracao em `duration_seconds`.
- Usuario nao deve digitar duracao manual para audio.
- Player deve receber a duracao real.

### RF003 — Separar duracao real e duracao de exibicao

O sistema deve separar:

- `duration_seconds`: duracao real do arquivo.
- `display_duration_seconds`: duracao operacional que o player deve respeitar quando configurada.

Regras:

- Video/audio sem `display_duration_seconds` devem tocar ate o fim.
- Video/audio com `display_duration_seconds` devem respeitar o tempo configurado.
- Imagem deve usar `display_duration_seconds` obrigatorio ou padrao.
- Link/webview/html deve usar `display_duration_seconds`.

### RF004 — Periodo de exibicao da midia

A midia deve permitir periodo proprio de exibicao.

Campos:

- `starts_at`
- `ends_at`

Regras:

- `starts_at` pode ser vazio.
- `ends_at` pode ser vazio.
- `ends_at` nao pode ser menor que `starts_at`.
- Midia antes de `starts_at` fica agendada.
- Midia depois de `ends_at` fica expirada.
- Midia expirada nao deve tocar.
- Midia agendada para o futuro nao deve tocar ainda.

### RF005 — Status de disponibilidade

O painel deve mostrar status operacional calculado:

- ativa;
- agendada;
- expirada;
- inativa;
- processando;
- com erro.

Observacao: status persistido tecnico pode continuar com `available`, `processing`, `error`, mas o painel precisa exibir disponibilidade calculada.

### RF006 — Substituir arquivo mantendo media_id

O sistema deve permitir substituir o arquivo fisico de uma midia existente.

Regras:

- Manter o mesmo `media_id`.
- Nao remover a midia das campanhas.
- Nao remover a midia de playlists.
- Nao remover a midia de agendamentos.
- Recalcular hash, tamanho, mime type, duracao, thumbnail e metadados.
- Incrementar `file_version`.
- Criar historico em `media_versions`.
- Notificar/invalidadar players afetados.

### RF007 — Historico de versoes

Toda substituicao de arquivo deve criar uma versao historica.

O historico deve registrar:

- arquivo antigo/novo;
- hash;
- tamanho;
- mime type;
- duracao;
- versao;
- data;
- usuario responsavel.

### RF008 — Uso da midia em campanhas

O sistema deve permitir consultar onde uma midia esta sendo usada.

Critérios:

- Informar quantidade de campanhas.
- Listar campanhas associadas.
- Mostrar aviso antes de substituicao.
- Bloquear exclusao direta de midia em uso, salvo confirmacao forte.

### RF009 — Player deve receber contrato atualizado

O player deve receber:

- `media_id`;
- `file_url`;
- `file_hash`;
- `file_version`;
- `duration_seconds`;
- `display_duration_seconds`;
- `starts_at`;
- `ends_at`;
- `status`;
- `type`;
- `thumbnail_url`;
- `play_until_end`.

### RF010 — Player nao deve tocar midia invalida

O player/backend deve garantir que midias invalidas nao sejam executadas.

Invalidas:

- expirada;
- agendada para o futuro;
- inativa;
- com erro;
- sem arquivo valido.

## Requisitos nao funcionais

- Nao quebrar campanhas existentes.
- Nao quebrar agendamentos existentes.
- Nao alterar `media_id` ao substituir arquivo.
- Nao usar mock/localStorage como solucao administrativa final.
- Manter compatibilidade com `duration` ate migração completa.
- Upload deve validar MIME e extensao.
- Processamento pesado deve poder migrar para Celery.
- Player deve continuar funcionando offline com cache local quando possivel.
- Alteracoes em midia devem invalidar cache somente de players afetados quando possivel.

## Decisoes de compatibilidade

- `campaigns.media_ids` e `campaigns.media_order` continuam funcionando nesta SPEC.
- `duration` permanece como campo legado para compatibilidade.
- `display_duration_seconds` passa a ser a fonte preferencial para tempo operacional.
- `duration_seconds` passa a ser a fonte de metadado real.
- `file_hash` e `file_version` serao usados para cache busting.

## Riscos

- `ffprobe` precisa estar disponivel no ambiente do backend.
- Processamento de video grande pode pesar se executado dentro da request.
- Campanhas ainda usam JSON, dificultando integridade referencial.
- Thumbnail real de video exige pipeline adicional.
- Cache local do player precisa comparar hash/versao para evitar arquivo antigo.

## Fora de escopo imediato

- Migrar campanhas para `campaign_playlist_items`.
- Criar status de cache por midia/dispositivo.
- Criar relatorios avancados de playback.
- Criar pipeline completo de processamento assincromo.
