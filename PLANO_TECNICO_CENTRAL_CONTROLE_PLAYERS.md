# Plano Tecnico: Central de Controle dos Players PlayWave

Data: 2026-05-20

## 1. Visao Geral

O PlayWave ja possui a base principal de uma plataforma de digital signage: campanhas, midias, dispositivos, player, Redis, Celery, heartbeat, comandos remotos e cache de playlist. O proximo salto de maturidade e transformar o painel administrativo em uma central operacional.

O objetivo da expansao e permitir que o administrador controle e audite, com precisao:

- o que toca;
- onde toca;
- quando toca;
- com qual prioridade;
- com qual audio;
- em qual modo de reproducao;
- com qual fila;
- com qual politica de cache;
- com qual fallback;
- se chegou no player;
- se sincronizou;
- se foi executado;
- se falhou e por que falhou.

O sistema deve deixar de ser apenas um CRUD de campanhas e virar uma plataforma de orquestracao, entrega e monitoramento de players.

## 2. Principios de Arquitetura

1. Campanha nao e apenas conteudo
   - Campanha deve ser tratada como uma regra de execucao versionada.

2. Player nao e apenas consumidor
   - Player deve reportar estado, fila atual, cache, erros, comandos e execucao.

3. Entrega deve ser observavel
   - Publicar campanha deve gerar evidencia: entregue, sincronizada, em execucao ou falhou.

4. Cache deve ter estado proprio
   - Cada midia em cada dispositivo precisa ter status de cache.

5. Prioridade e agenda devem ser resolvidas no backend
   - O player deve receber uma fila ja resolvida, com fallback e versao.

6. Toda acao operacional deve ser auditavel
   - Publicar, pausar, reiniciar, apagar midia e enviar comando precisam ter trilha de auditoria.

## 3. Regras de Negocio

## 3.1 Campanhas

### Ciclo de vida da campanha

Status recomendados:

- `draft`: campanha em criacao, nao chega ao player.
- `validating`: campanha em validacao automatica antes da publicacao.
- `ready`: campanha valida e pronta para publicar.
- `published`: campanha publicada, mas nao necessariamente ativa no horario atual.
- `active`: campanha elegivel para execucao agora.
- `paused`: campanha pausada manualmente.
- `expired`: campanha passou da data final.
- `archived`: campanha encerrada e retirada das operacoes.
- `rejected`: campanha falhou na validacao.

Regras:

- Campanha `draft` pode ser editada livremente.
- Campanha `published` deve gerar nova versao ao ser alterada.
- Campanha `active` so pode tocar se agenda, segmentacao, prioridade e midias forem validas.
- Campanha `paused` nao entra em fila.
- Campanha `expired` nao entra em fila.
- Campanha `archived` nao pode ser publicada sem duplicacao ou reabertura controlada.

### Validacao antes de publicar

Antes de publicar, o backend deve validar:

- nome preenchido;
- pelo menos uma midia valida, exceto campanhas `audio_only` ou templates especificos;
- pelo menos um alvo: dispositivo, grupo, unidade, cidade, tag, SO ou regra;
- midias com status `available`;
- midias com URL/arquivo acessivel;
- duracao valida por item;
- agenda coerente: inicio menor que fim;
- prioridade dentro do intervalo permitido;
- conflitos de agenda;
- politica de cache compativel com tipo de midia;
- playlist de audio existente quando o modo exige audio de fundo;
- permissoes do usuario publicador.

Resultado da validacao:

- `valid`: boolean;
- `errors`: bloqueiam publicacao;
- `warnings`: permitem publicar com confirmacao;
- `affected_devices_count`;
- `estimated_storage_required`;
- `conflicts`.

### Prioridade entre campanhas

Campos recomendados:

- `priority`: inteiro de 1 a 100.
- `priority_type`: `normal`, `high`, `emergency`.
- `exclusive`: boolean.
- `interrupt_current_playback`: boolean.

Regras:

- Campanha emergencial sempre vence campanhas normais.
- Campanha com `exclusive=true` bloqueia outras campanhas no mesmo periodo e alvo.
- Quando duas campanhas tem mesmo alvo e horario:
  - maior prioridade vence;
  - se prioridade empatar, campanha emergencial vence;
  - se continuar empatado, campanha mais recente publicada vence;
  - se ambas permitirem composicao, o backend pode mesclar filas conforme politica.

### Campanha emergencial

Campanha emergencial deve:

- publicar imediatamente;
- invalidar cache dos dispositivos alvo;
- enviar evento SSE/comando `refresh_playlist`;
- poder interromper a midia atual;
- ter TTL ou data final obrigatoria;
- aparecer destacada na Central de Entrega.

Campos:

- `is_emergency`;
- `emergency_level`: `info`, `warning`, `critical`;
- `interrupt_current_playback`;
- `expires_at`;
- `requires_ack`.

### Conflito de agenda

Um conflito acontece quando duas campanhas:

- miram o mesmo dispositivo ou grupo resolvido;
- estao ativas no mesmo dia/horario;
- possuem modos incompativeis;
- uma delas e exclusiva;
- possuem politicas de audio conflitantes.

Tipos de conflito:

- `blocking`: impede publicacao.
- `warning`: permite publicacao com confirmacao.
- `resolved_by_priority`: resolvido automaticamente pela prioridade.

Exemplos:

- Duas campanhas exclusivas no mesmo horario: bloqueia.
- Campanha emergencial sobre campanha normal: permitido, emergencial vence.
- Duas campanhas normais com prioridade diferente: maior prioridade vence.
- Campanha `audio_only` simultanea com `video_with_background_audio`: conflito de audio, precisa regra.

### Segmentacao

Campanha deve poder mirar:

- dispositivo especifico;
- grupo de dispositivos;
- unidade/localizacao;
- cidade;
- tags;
- sistema operacional;
- tipo de dispositivo;
- resolucao de tela;
- orientacao da tela;
- versao minima do player.

Regra:

- O backend deve resolver segmentacao para uma lista efetiva de dispositivos.
- Essa resolucao deve gerar snapshot versionado.
- O admin deve ver "alvos estimados" antes de publicar.

### Campanha e midias

Cada item da campanha deve permitir:

- ordem;
- duracao customizada;
- modo de ajuste visual: `contain`, `cover`, `fill`;
- volume da midia;
- permitir audio original;
- fallback por item;
- condicoes especificas;
- data/horario individual opcional;
- quantidade maxima de repeticoes;
- politica de cache por item.

## 3.2 Player

### Estado atual do player

O player deve reportar periodicamente:

- `device_id`;
- `current_campaign_id`;
- `current_config_version`;
- `current_media_id`;
- `current_media_name`;
- `queue_version`;
- `storage_used`;
- `storage_free`;
- `app_version`;
- `os`;
- `screen_resolution`;
- `orientation`;
- `last_error`;
- `playback_status`;
- `network_status`;
- `cache_status_summary`;
- `last_sync_at`;
- `last_playback_at`.

Status de playback:

- `idle`;
- `loading`;
- `playing`;
- `paused`;
- `buffering`;
- `stopped`;
- `error`;
- `offline_mode`;

### Fila real de reproducao por dispositivo

O backend deve gerar uma fila resolvida por dispositivo.

Fila deve incluir:

- `queue_id`;
- `queue_version`;
- `device_id`;
- campanhas aplicadas;
- itens ordenados;
- midias;
- audio;
- overlays;
- politicas de cache;
- fallback;
- validade;
- hash do conteudo.

O player deve:

- baixar ou receber a fila;
- confirmar recebimento;
- confirmar cache das midias obrigatorias;
- iniciar execucao;
- reportar item atual;
- reportar divergencia de fila.

### Confirmacoes

Eventos importantes:

- `queue_received`;
- `queue_synced`;
- `media_cache_started`;
- `media_cached`;
- `playback_started`;
- `playback_completed`;
- `playback_failed`;
- `fallback_started`;
- `command_received`;
- `command_running`;
- `command_success`;
- `command_failed`.

## 3.3 Modos de Reproducao

Modos suportados:

- `video_only`: video com audio original opcional.
- `video_muted`: video sempre mudo.
- `video_with_background_audio`: video mudo ou baixo com radio indoor.
- `image_only`: imagem sem audio.
- `image_with_background_audio`: imagem com playlist de audio.
- `audio_only`: campanha sonora, sem imagem obrigatoria.
- `web_url`: URL externa em iframe/webview.
- `html_template`: template HTML interno.
- `split_screen`: multiplas zonas na tela.
- `ticker_overlay`: faixa de texto sobre a reproducao.

Regras:

- `video_only` pode usar audio original do arquivo.
- `video_with_background_audio` deve definir se o audio original sera mutado.
- `image_with_background_audio` exige playlist de audio.
- `audio_only` nao deve bloquear campanhas visuais se a politica permitir composicao.
- `web_url` precisa timeout e fallback.
- `html_template` precisa assets empacotados/cacheados.
- `split_screen` precisa layout versionado.
- `ticker_overlay` pode coexistir com campanhas visuais.

## 3.4 Audio

Hierarquia de volume:

1. volume global do dispositivo;
2. volume padrao do grupo;
3. volume da campanha;
4. volume da playlist de audio;
5. volume por faixa;
6. volume por midia.

Regras:

- O player deve receber volume final calculado e tambem os componentes.
- Campanha pode escolher audio original do video ou radio indoor.
- Video pode ser mutado automaticamente quando houver audio de fundo.
- Imagem pode tocar com audio de fundo.
- Playlist de audio pode ser associada a campanha, grupo ou dispositivo.
- Campanha deve avisar conflito quando duas fontes de audio competem.

## 3.5 Cache

Politicas:

- `streaming`: toca direto da URL, cache opcional.
- `download_before_play`: baixa antes de tocar.
- `hybrid`: tenta cache, se falhar faz streaming.
- `cache_required`: so toca se estiver em cache.

Status por midia/dispositivo:

- `not_downloaded`;
- `downloading`;
- `cached`;
- `failed`;
- `expired`;
- `deleted`.

Regras:

- Campanha com `cache_required` so deve ser marcada como sincronizada se todas as midias obrigatorias estiverem cached.
- Player deve reportar progresso de download.
- Backend deve calcular armazenamento necessario.
- Se storage insuficiente, campanha deve ficar pendente ou falhar com motivo claro.

## 4. Requisitos Funcionais

## 4.1 Campanhas

- Criar campanha em rascunho.
- Validar campanha antes de publicar.
- Publicar campanha.
- Pausar campanha.
- Retomar campanha.
- Arquivar campanha.
- Expirar campanha automaticamente.
- Criar campanha emergencial.
- Definir prioridade e exclusividade.
- Definir agenda por data, dia da semana e horario.
- Definir segmentacao por dispositivo, grupo, unidade, cidade, tags, SO e tipo.
- Definir modo de reproducao.
- Definir midias com ordem e duracao customizada.
- Definir audio por campanha.
- Ver conflitos antes da publicacao.
- Ver entrega por dispositivo.

## 4.2 Player

- Buscar fila resolvida.
- Receber comandos remotos.
- Reportar heartbeat enriquecido.
- Reportar estado de cache.
- Reportar erro por midia.
- Reportar eventos de execucao.
- Executar fallback.
- Operar em modo offline.
- Confirmar recebimento, sincronizacao e execucao.

## 4.3 Comandos Remotos

Comandos:

- `sync`;
- `refresh_playlist`;
- `clear_cache`;
- `restart_app`;
- `restart_device`;
- `reload_player`;
- `take_screenshot`;
- `get_logs`;
- `download_media`;
- `stop_campaign`;
- `pause_campaign`;
- `resume_campaign`;
- `set_volume`;
- `mute`;
- `unmute`;
- `identify_screen`;
- `update_player`;
- `factory_reset`.

Status:

- `pending`;
- `sent`;
- `received`;
- `running`;
- `success`;
- `failed`;
- `expired`;
- `cancelled`.

Regras:

- Todo comando deve ter `expires_at`.
- Todo comando deve ter `requested_by`.
- Player deve confirmar recebimento.
- Player deve confirmar inicio da execucao.
- Player deve confirmar sucesso ou falha.
- Comandos sensiveis exigem permissao elevada.
- `factory_reset` deve exigir confirmacao forte.

## 4.4 Midias

- Upload de arquivo.
- Cadastro de URL externa.
- Validacao de MIME, extensao, tamanho, duracao, resolucao, codec e integridade.
- Extracao de metadata real.
- Geracao de thumbnail.
- Processamento assincromo.
- Status de processamento.
- Listar campanhas que usam a midia.
- Bloquear exclusao perigosa ou exigir confirmacao.
- Registrar erros de reproducao.
- Definir fallback por midia.

## 4.5 Auditoria

Registrar:

- quem criou campanha;
- quem editou campanha;
- antes/depois da edicao;
- quem publicou;
- quem pausou;
- quem retomou;
- quem arquivou;
- quem enviou comando;
- quem reiniciou player;
- quem apagou midia;
- quem alterou audio;
- quem alterou segmentacao;
- origem da acao: painel, API, automacao.

## 5. Requisitos Nao Funcionais

Performance:

- Endpoint de fila do player deve responder rapidamente usando cache.
- Heartbeat deve ser leve e tolerar muitos players.
- Comandos devem ser entregues quase em tempo real via SSE quando possivel.

Disponibilidade:

- Player deve continuar com fila local se backend cair.
- Campanhas cacheadas devem tocar offline se a politica permitir.
- Redis indisponivel nao deve derrubar o backend, apenas degradar cache/SSE.

Escalabilidade:

- Cache por dispositivo.
- Fila materializada por dispositivo.
- Celery separado por filas.
- Evitar invalidacao global.

Seguranca:

- Token de dispositivo obrigatorio.
- Comandos sensiveis por permissao.
- Auditoria imutavel.
- Logs sem expor tokens.

Observabilidade:

- Latencia por endpoint do player.
- Taxa de cache hit/miss.
- Erros de midia por tipo.
- Comandos falhos.
- Players offline.
- Filas divergentes.

## 6. Entidades e Tabelas Propostas

## 6.1 `campaign_devices`

Relacionamento efetivo entre campanha e dispositivo.

Campos:

- `id`;
- `campaign_id`;
- `device_id`;
- `target_source`: `manual`, `group`, `unit`, `city`, `tag`, `os`, `rule`;
- `priority_override`;
- `created_at`;
- `updated_at`.

## 6.2 `campaign_media`

Itens da campanha.

Campos:

- `id`;
- `campaign_id`;
- `media_id`;
- `position`;
- `duration_seconds`;
- `playback_mode`;
- `fit_mode`;
- `volume`;
- `use_original_audio`;
- `cache_policy`;
- `fallback_media_id`;
- `starts_at`;
- `ends_at`;
- `days_of_week`;
- `created_at`;
- `updated_at`.

## 6.3 `campaign_delivery_status`

Entrega por campanha/dispositivo.

Campos:

- `id`;
- `campaign_id`;
- `device_id`;
- `expected_config_version`;
- `current_config_version`;
- `expected_queue_version`;
- `current_queue_version`;
- `delivery_status`;
- `cache_status`;
- `current_media_id`;
- `last_error`;
- `last_seen_at`;
- `synced_at`;
- `started_at`;
- `updated_at`.

Status:

- `synced`;
- `pending`;
- `offline`;
- `error`;
- `executing`.

## 6.4 `device_queue_snapshots`

Fila resolvida por dispositivo.

Campos:

- `id`;
- `device_id`;
- `queue_version`;
- `queue_hash`;
- `payload`;
- `valid_from`;
- `valid_until`;
- `created_at`;
- `published_at`.

## 6.5 `device_heartbeats`

Historico de heartbeat.

Campos:

- `id`;
- `device_id`;
- `current_campaign_id`;
- `current_config_version`;
- `current_media_id`;
- `current_media_name`;
- `queue_version`;
- `storage_used`;
- `storage_free`;
- `app_version`;
- `os`;
- `screen_resolution`;
- `playback_status`;
- `last_error`;
- `created_at`.

Observacao:

- Manter tabela particionada ou com retencao, pois heartbeat cresce rapido.

## 6.6 `device_commands`

Fila principal de comandos.

Campos:

- `id`;
- `device_id`;
- `tenant_id`;
- `command_type`;
- `payload`;
- `status`;
- `requested_by`;
- `requested_at`;
- `sent_at`;
- `received_at`;
- `started_at`;
- `finished_at`;
- `expires_at`;
- `error_message`.

## 6.7 `device_command_results`

Resultados detalhados dos comandos.

Campos:

- `id`;
- `command_id`;
- `device_id`;
- `status`;
- `output`;
- `error`;
- `metadata`;
- `created_at`.

## 6.8 `player_events`

Eventos operacionais do player.

Campos:

- `id`;
- `device_id`;
- `campaign_id`;
- `media_id`;
- `event_type`;
- `payload`;
- `severity`;
- `created_at`.

Eventos:

- `queue_received`;
- `queue_synced`;
- `playback_started`;
- `playback_completed`;
- `playback_failed`;
- `fallback_started`;
- `cache_failed`;
- `command_received`;
- `command_success`;
- `command_failed`.

## 6.9 `media_processing_jobs`

Processamento de midia.

Campos:

- `id`;
- `media_id`;
- `status`;
- `steps`;
- `metadata`;
- `error_message`;
- `started_at`;
- `finished_at`;
- `created_at`.

## 6.10 `media_playback_errors`

Erros de reproducao.

Campos:

- `id`;
- `media_id`;
- `device_id`;
- `campaign_id`;
- `error_code`;
- `error_message`;
- `player_context`;
- `created_at`.

## 6.11 `device_cache_status`

Cache por midia/dispositivo.

Campos:

- `id`;
- `device_id`;
- `media_id`;
- `status`;
- `progress`;
- `file_size`;
- `bytes_downloaded`;
- `checksum`;
- `cached_at`;
- `expires_at`;
- `last_error`;
- `updated_at`.

## 6.12 `campaign_conflicts`

Conflitos detectados.

Campos:

- `id`;
- `campaign_id`;
- `conflicting_campaign_id`;
- `device_id`;
- `conflict_type`;
- `severity`;
- `resolution`;
- `created_at`.

## 6.13 `audit_logs`

Auditoria geral.

Campos:

- `id`;
- `tenant_id`;
- `actor_user_id`;
- `action`;
- `entity_type`;
- `entity_id`;
- `before`;
- `after`;
- `ip_address`;
- `user_agent`;
- `created_at`.

## 6.14 `device_groups`

Grupos de dispositivos.

Campos:

- `id`;
- `tenant_id`;
- `name`;
- `description`;
- `tags`;
- `created_at`;
- `updated_at`.

## 6.15 `device_group_members`

Membros dos grupos.

Campos:

- `id`;
- `group_id`;
- `device_id`;
- `created_at`.

## 6.16 `campaign_target_rules`

Regras de segmentacao.

Campos:

- `id`;
- `campaign_id`;
- `rule_type`;
- `operator`;
- `value`;
- `created_at`.

Exemplos:

- `os equals android_tv`;
- `city in ["Sao Paulo", "Campinas"]`;
- `tag contains promocao`;
- `device_type equals totem`.

## 7. Endpoints REST Propostos

## 7.1 Campanhas

- `GET /campaigns`
- `GET /campaigns/{id}`
- `POST /campaigns`
- `PUT /campaigns/{id}`
- `POST /campaigns/{id}/validate`
- `POST /campaigns/{id}/publish`
- `POST /campaigns/{id}/pause`
- `POST /campaigns/{id}/resume`
- `POST /campaigns/{id}/archive`
- `POST /campaigns/{id}/duplicate`
- `POST /campaigns/{id}/emergency`
- `GET /campaigns/{id}/conflicts`
- `GET /campaigns/{id}/delivery`
- `GET /campaigns/{id}/devices`
- `GET /campaigns/{id}/media`
- `POST /campaigns/{id}/force-sync`

## 7.2 Player

- `GET /player/{device_id}/queue`
- `POST /player/{device_id}/queue/ack`
- `POST /player/{device_id}/heartbeat`
- `POST /player/{device_id}/events`
- `POST /player/{device_id}/cache-status`
- `POST /player/{device_id}/playback-log`
- `GET /player/{device_id}/commands/pending`
- `POST /player/{device_id}/commands/{command_id}/ack`
- `GET /player/{device_id}/stream`

Observacao:

- Pode coexistir com os endpoints atuais em `/devices/{id}/playlist`, mas o ideal e evoluir para namespace `player`.

## 7.3 Dispositivos

- `GET /devices`
- `GET /devices/{id}`
- `PUT /devices/{id}`
- `GET /devices/{id}/state`
- `GET /devices/{id}/queue`
- `GET /devices/{id}/cache`
- `GET /devices/{id}/events`
- `GET /devices/{id}/commands`
- `POST /devices/{id}/commands`
- `POST /devices/{id}/identify`
- `POST /devices/{id}/revoke-token`

## 7.4 Comandos

- `POST /commands`
- `GET /commands`
- `GET /commands/{id}`
- `POST /commands/{id}/cancel`
- `POST /commands/bulk`
- `GET /commands/{id}/results`

## 7.5 Midias

- `GET /media`
- `GET /media/{id}`
- `POST /media/upload`
- `POST /media/external`
- `PUT /media/{id}`
- `DELETE /media/{id}`
- `POST /media/{id}/process`
- `GET /media/{id}/processing`
- `GET /media/{id}/usage`
- `GET /media/{id}/playback-errors`
- `GET /media/{id}/cache-status`

## 7.6 Cache

- `GET /cache/devices/{device_id}`
- `GET /cache/media/{media_id}`
- `POST /cache/devices/{device_id}/clear`
- `POST /cache/devices/{device_id}/warmup`
- `POST /cache/campaigns/{campaign_id}/warmup`

## 7.7 Logs e Auditoria

- `GET /audit-logs`
- `GET /player-events`
- `GET /playback-logs`
- `GET /media-errors`
- `GET /system/health`
- `GET /system/metrics`

## 7.8 Relatorios

- `GET /reports/campaigns`
- `GET /reports/devices`
- `GET /reports/media`
- `GET /reports/delivery`
- `GET /reports/cache`
- `GET /reports/commands`

## 8. Telas Administrativas

## 8.1 Central de Campanhas

Funcoes:

- listar campanhas por status;
- criar campanha;
- validar;
- publicar;
- pausar;
- arquivar;
- criar emergencial;
- ver conflitos;
- ver entrega;
- ver midias e dispositivos alvo;
- duplicar campanha;
- preview do player.

Cards importantes:

- rascunhos;
- publicadas;
- ativas;
- emergenciais;
- com erro;
- expiradas.

## 8.2 Central de Players

Funcoes:

- listar dispositivos;
- status online/offline;
- campanha atual;
- midia atual;
- versao atual;
- versao esperada;
- armazenamento;
- app version;
- SO;
- resolucao;
- ultimo erro;
- comandos rapidos.

## 8.3 Central de Entrega

Tela mais importante para operacao.

Filtros:

- campanha;
- grupo;
- unidade;
- cidade;
- status;
- versao divergente;
- erro;
- offline.

Colunas:

- dispositivo;
- online/offline;
- ultima conexao;
- campanha esperada;
- versao esperada;
- versao atual;
- fila esperada;
- fila atual;
- midia atual;
- status de cache;
- ultimo erro;
- status final.

Acoes:

- forcar sync;
- limpar cache;
- reiniciar player;
- ver logs;
- tirar screenshot;

## 8.4 Central de Comandos

Funcoes:

- enviar comando individual;
- enviar comando em lote;
- ver status por dispositivo;
- cancelar comando;
- repetir comando;
- ver resultado;
- ver erro.

## 8.5 Central de Midias

Funcoes:

- upload;
- processamento;
- thumbnail;
- metadata;
- campanhas que usam;
- status de cache;
- erros de reproducao;
- bloquear exclusao perigosa;
- reprocessar midia.

## 8.6 Central de Relatorios

Relatorios:

- exibicoes por campanha;
- exibicoes por midia;
- exibicoes por dispositivo;
- falhas por midia;
- disponibilidade de players;
- taxa de entrega;
- taxa de cache;
- comandos executados.

## 8.7 Saude do Sistema

Indicadores:

- backend online;
- Redis online;
- Celery worker online;
- Celery beat online;
- RabbitMQ online;
- cache hit/miss;
- fila de comandos pendentes;
- players offline;
- erros recentes;
- latencia dos endpoints do player.

## 9. Fluxo Operacional Recomendado

## 9.1 Criar e publicar campanha

1. Usuario cria campanha em `draft`.
2. Seleciona midias.
3. Define ordem, duracao, modo e audio.
4. Define agenda.
5. Define segmentacao.
6. Backend calcula dispositivos alvo.
7. Usuario clica em validar.
8. Backend retorna erros, avisos, conflitos e impacto.
9. Usuario corrige ou confirma warnings.
10. Usuario publica.
11. Backend gera `config_version` e `queue_version`.
12. Backend gera fila por dispositivo.
13. Redis cache e invalidado para dispositivos afetados.
14. SSE/comando notifica players.
15. Players buscam nova fila.
16. Players confirmam recebimento.
17. Players baixam/cacheiam midias conforme politica.
18. Players confirmam sincronizacao.
19. Players executam.
20. Painel mostra status de entrega.

## 9.2 Player offline

1. Player perde conexao.
2. Continua fila local se politica permitir.
3. Marca estado local como offline.
4. Ao reconectar, envia heartbeat com fila atual.
5. Backend compara fila atual com fila esperada.
6. Se divergente, envia nova fila.
7. Central de Entrega atualiza status.

## 9.3 Midia com erro

1. Player tenta reproduzir midia.
2. Falha.
3. Player registra `media_playback_error`.
4. Player aplica fallback:
   - proxima midia;
   - midia fallback;
   - campanha fallback;
   - tela padrao.
5. Backend atualiza status da entrega.
6. Painel mostra erro por midia e dispositivo.

## 10. Matriz de Permissoes

Perfis:

- `super_admin`;
- `admin`;
- `operator`;
- `content_manager`;
- `viewer`;
- `support`.

Permissoes recomendadas:

| Acao | super_admin | admin | operator | content_manager | viewer | support |
|---|---:|---:|---:|---:|---:|---:|
| Criar campanha | sim | sim | sim | sim | nao | nao |
| Editar campanha | sim | sim | sim | sim | nao | nao |
| Publicar campanha | sim | sim | sim | nao | nao | nao |
| Criar emergencial | sim | sim | nao | nao | nao | nao |
| Pausar campanha | sim | sim | sim | nao | nao | sim |
| Arquivar campanha | sim | sim | nao | nao | nao | nao |
| Upload de midia | sim | sim | sim | sim | nao | nao |
| Apagar midia | sim | sim | nao | sim | nao | nao |
| Enviar comando simples | sim | sim | sim | nao | nao | sim |
| Reiniciar app | sim | sim | sim | nao | nao | sim |
| Reiniciar dispositivo | sim | sim | nao | nao | nao | sim |
| Factory reset | sim | nao | nao | nao | nao | nao |
| Ver relatorios | sim | sim | sim | sim | sim | sim |
| Ver auditoria | sim | sim | nao | nao | nao | nao |
| Gerenciar usuarios | sim | sim | nao | nao | nao | nao |

## 11. Prioridades de Implementacao

## Fase 1: Controle operacional minimo

1. Expandir heartbeat do player.
2. Criar `campaign_delivery_status`.
3. Criar endpoint `GET /campaigns/{id}/delivery`.
4. Criar tela de Entrega da Campanha.
5. Criar comando em lote `refresh_playlist` por campanha.
6. Mostrar versao esperada vs versao atual.

## Fase 2: Fila real por dispositivo

1. Criar `device_queue_snapshots`.
2. Gerar `queue_version`.
3. Player confirmar recebimento da fila.
4. Player confirmar execucao.
5. Detectar fila divergente.

## Fase 3: Campanhas robustas

1. Criar `campaign_devices`.
2. Criar `campaign_media`.
3. Criar validacao antes de publicar.
4. Criar conflitos de agenda.
5. Criar campanha emergencial.

## Fase 4: Midia e cache

1. Criar `media_processing_jobs`.
2. Processar metadata via Celery.
3. Criar `device_cache_status`.
4. Implementar politicas de cache.
5. Implementar fallback por midia.

## Fase 5: Auditoria e permissoes

1. Criar `audit_logs`.
2. Expandir roles.
3. Registrar before/after.
4. Tratar comandos sensiveis.

## 12. Riscos

1. Crescimento de heartbeat
   - Mitigacao: tabela particionada ou retencao curta.

2. Complexidade de fila por dispositivo
   - Mitigacao: gerar snapshot materializado e versionado.

3. Conflitos de agenda dificeis de entender
   - Mitigacao: tela de conflitos com explicacao clara.

4. Cache inconsistente
   - Mitigacao: `queue_version`, `cache_status` e confirmacao do player.

5. Comandos perigosos
   - Mitigacao: permissoes fortes, expiracao, auditoria e confirmacao.

6. Excesso de eventos
   - Mitigacao: consolidar eventos em batch e definir retencao.

## 13. Plano de Testes

## 13.1 Campanhas

- campanha sem midia deve falhar na validacao;
- campanha sem dispositivo alvo deve falhar na validacao;
- campanha com conflito bloqueante nao deve publicar;
- campanha com conflito resolvido por prioridade deve publicar com aviso;
- campanha emergencial deve vencer campanha normal;
- campanha expirada nao deve entrar na fila;
- campanha pausada deve sair da fila;
- campanha arquivada nao deve publicar diretamente;
- campanha com ordem customizada deve gerar fila correta;
- campanha com duracao customizada deve respeitar tempo por item.

## 13.2 Player

- player offline deve manter fila local se politica permitir;
- player offline deve aparecer como offline na entrega;
- player com versao antiga deve aparecer em alerta;
- player deve reportar `current_config_version`;
- player deve reportar `current_media_id`;
- fila divergente deve aparecer como pendente ou erro;
- player deve confirmar fila recebida;
- player deve confirmar playback iniciado;
- player deve confirmar playback finalizado.

## 13.3 Midias

- midia com MIME invalido deve ser rejeitada;
- midia com extensao invalida deve ser rejeitada;
- midia corrompida deve falhar processamento;
- thumbnail deve ser gerado para imagem/video;
- metadata real deve ser extraida;
- midia usada em campanha deve bloquear exclusao perigosa ou exigir confirmacao;
- erro de reproducao deve gerar registro em `media_playback_errors`;
- fallback deve tocar quando midia falhar.

## 13.4 Cache

- midia `download_before_play` deve baixar antes de tocar;
- campanha `cache_required` nao deve sincronizar se midia nao estiver cached;
- cache incompleto deve aparecer na Central de Entrega;
- cache failed deve gerar erro visivel;
- limpeza de cache deve atualizar status;
- player sem espaco deve reportar erro.

## 13.5 Comandos

- comando pendente deve aparecer como `pending`;
- comando enviado deve virar `sent`;
- player deve confirmar `received`;
- comando em execucao deve virar `running`;
- comando bem-sucedido deve virar `success`;
- comando com erro deve virar `failed`;
- comando expirado deve virar `expired`;
- comando cancelado deve virar `cancelled`;
- comando sem permissao deve ser bloqueado;
- `factory_reset` deve exigir permissao `super_admin`.

## 13.6 Entrega

- campanha publicada mas nao entregue deve aparecer como `pending`;
- campanha entregue mas nao executada deve aparecer como `synced` ou `pending_execution`;
- campanha executando deve aparecer como `executing`;
- dispositivo offline deve aparecer como `offline`;
- erro de cache deve aparecer como `error`;
- erro de midia deve aparecer com media e mensagem;
- versao atual diferente da esperada deve aparecer como divergente.

## 14. Criterios de Sucesso

O projeto atinge o novo nivel operacional quando:

- o admin sabe exatamente quais players receberam uma campanha;
- o admin sabe quais players estao executando a campanha;
- o admin sabe qual midia esta tocando em cada player;
- o admin consegue forcar sincronizacao por campanha;
- o admin consegue ver falhas por midia/dispositivo;
- o player consegue operar offline com politica clara;
- os comandos remotos possuem ciclo completo de status;
- toda acao sensivel fica registrada em auditoria;
- o backend resolve fila, prioridade, agenda e fallback de forma previsivel.

## 15. Conclusao

A expansao recomendada transforma o PlayWave em uma central de controle operacional. O ponto principal nao e adicionar mais telas de cadastro, mas criar uma camada de entrega, execucao e observabilidade.

A primeira entrega deve ser a Central de Entrega da Campanha, apoiada por heartbeat enriquecido e status por dispositivo. Essa etapa ja daria ao administrador a resposta mais importante: a campanha chegou, sincronizou e esta tocando?
