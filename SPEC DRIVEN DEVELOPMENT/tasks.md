# PlayWave — Tasks Map

Data base: 2026-05-20

Este arquivo transforma `requirements.md` e `design.md` em backlog executavel. Use os status:

- `[ ]` pendente
- `[~]` em andamento/parcial
- `[x]` concluido
- `[!]` bloqueado ou precisa decisao

## P0 — Mapa SDD do Projeto

- [x] Criar `requirements.md` como mapa de requisitos do PlayWave.
- [x] Criar `design.md` como mapa tecnico do PlayWave.
- [x] Criar `tasks.md` como backlog rastreavel.
- [x] Definir convencao de IDs para proximas specs: `SPEC-XXX` no SDD interno, pasta `docs/specs/NNN-nome-curto/` para detalhe.
- [x] Criar template de spec para novas features (em `docs/specs/_TEMPLATE/`).

## SPEC-DOC-007 — Roadmap Integrado Midias, Radio e Player

Objetivo: consolidar auditoria e plano tecnico das melhorias solicitadas, reaproveitando SPECs ja implementadas/parciais e separando radio indoor v2 em fases seguras.

**Detalhamento em `docs/specs/007-roadmap-integrado-midias-radio-player/`.**

- [x] Auditoria de estado atual backend/frontend/player.
- [x] Mapeamento de funcionalidades existentes, parciais e ausentes.
- [x] SPEC tecnica criada com requisitos, design, banco, API, frontend, player, tasks e testes.
- [~] Implementar Fase B: playlist visual real no frontend.
- [~] Implementar Fase C: radio indoor v2 backend.
- [ ] Implementar Fase D: radio indoor v2 frontend.
- [ ] Implementar Fase E: audio manager do player.

## SPEC-001 — Midias Inteligentes

Objetivo: midia com duracao real, periodo de exibicao, versionamento e substituicao segura de arquivo.

### Backend

- [x] Mapear model atual de midias.
- [x] Verificar campos existentes na tabela de midias.
- [x] Criar migration para `duration_seconds`.
- [x] Criar migration para `display_duration_seconds`.
- [x] Criar migration para `starts_at`.
- [x] Criar migration para `ends_at`.
- [x] Criar migration para `file_hash`.
- [x] Criar migration para `file_version`.
- [x] Criar tabela `media_versions`.
- [x] Implementar extracao de metadados com `ffprobe`.
- [x] Implementar deteccao de duracao de video.
- [x] Implementar deteccao de duracao de audio.
- [x] Implementar hash SHA-256 do arquivo.
- [x] Implementar endpoint `POST /media/{id}/replace-file`.
- [x] Implementar endpoint `GET /media/{id}/usage`.
- [x] Implementar endpoint `GET /media/{id}/versions`.
- [x] Validar datas de inicio e fim.
- [x] Validar tipo de arquivo.
- [~] Validar tamanho maximo.
- [x] Bloquear exclusao de midia em uso sem `force`.
- [x] Atualizar campanhas afetadas quando midia muda.
- [x] Invalidar cache dos devices afetados quando midia muda.
- [~] Gerar thumbnail real de video.
- [ ] Mover processamento pesado de midia para Celery.
- [ ] Criar tabela `media_processing_jobs`.
- [ ] Registrar falha de processamento em tabela propria.

### Frontend

- [x] Ajustar formulario de criacao de midia.
- [x] Ajustar formulario de edicao de midia.
- [x] Mostrar duracao detectada.
- [x] Mostrar campo de duracao personalizada opcional.
- [x] Adicionar data inicio.
- [x] Adicionar data fim.
- [x] Adicionar botao "Substituir arquivo".
- [x] Mostrar status calculado da midia na listagem.
- [x] Mostrar uso em campanhas na listagem quando backend retornar `usage_count`.
- [~] Mostrar aviso detalhado de midia em uso antes de substituir.
- [~] Mostrar confirmacao forte para exclusao forcada.
- [ ] Criar tela/modal de historico de versoes.

### Player

- [x] Atualizar contrato de sincronizacao.
- [x] Receber `duration_seconds`.
- [x] Receber `display_duration_seconds`.
- [x] Receber `file_version`.
- [x] Receber `file_hash`.
- [x] Ignorar midia expirada no backend antes de enviar ao player.
- [x] Ignorar midia agendada no backend antes de enviar ao player.
- [x] Video/audio sem duracao customizada tocam ate o fim.
- [~] Invalidar cache local quando `file_hash` mudar.
- [~] Registrar erro se midia nao tocar.
- [ ] Criar status de cache por midia/dispositivo.

### Banco

- [x] Adicionar campos em `media`.
- [x] Criar `media_versions`.
- [ ] Criar indices adicionais conforme volume real.
- [ ] Backfill completo de versoes para midias antigas.

### Testes

- [x] Criar testes unitarios basicos para regras puras de midia.
- [ ] Rodar testes no container/venv do backend.
- [ ] Testar upload de video com duracao automatica.
- [ ] Testar upload de audio com duracao automatica.
- [ ] Testar imagem com duracao manual.
- [ ] Testar midia expirada.
- [ ] Testar midia agendada.
- [ ] Testar substituicao mantendo mesmo `media_id`.
- [ ] Testar campanha mantendo vinculo apos substituicao.
- [ ] Testar player recebendo nova versao.

## SPEC-002 — Playlist Real de Campanha

Objetivo: substituir selecao simples por checkbox por construtor real de playlist.

### Backend

- [x] Criar tabela `campaign_playlist_items` (migration `campaign_playlist_items` aplicada em 2026-05-20).
- [x] Migrar dados atuais de `campaign.media_ids` para itens.
- [x] Migrar dados atuais de `campaign.media_order` para itens.
- [x] Implementar `GET /campaigns/{id}/items`.
- [x] Implementar `POST /campaigns/{id}/items` (aceita bulk via `items[]`).
- [x] Implementar `PUT /campaigns/{id}/items/{item_id}`.
- [x] Implementar `DELETE /campaigns/{id}/items/{item_id}`.
- [x] Implementar `PATCH /campaigns/{id}/items/reorder`.
- [x] Permitir repetir mesma midia na campanha (model permite N rows com mesmo `media_id`; player builder respeita `repeat_count`).
- [x] Permitir ativar/desativar item (`is_active`).
- [x] Permitir periodo por item (`starts_at`/`ends_at`).
- [x] Permitir duracao customizada por item (`display_duration_seconds`).
- [x] Atualizar builder de playlist do player para usar itens relacionais (com fallback para JSON legado).
- [~] Write-through: mutar items atualiza `media_ids`/`media_order`/`config_version` e invalida cache. Remover colunas legadas em SPEC futura.

### Frontend

- [x] Remover fluxo principal baseado em checkbox.
- [x] Criar botao "Adicionar midia a campanha".
- [~] Criar drawer/modal com biblioteca de midias. Implementado como biblioteca inline no construtor; drawer dedicado fica como refinamento.
- [~] Permitir selecao multipla. O fluxo atual permite adicionar varias midias e repetir midias, mas ainda nao faz selecao em lote.
- [x] Criar lista de itens da playlist.
- [x] Implementar drag and drop.
- [~] Implementar botoes mover para cima/baixo/inicio/fim. Cima/baixo implementado; inicio/fim pendente.
- [x] Mostrar duracao total estimada.
- [ ] Mostrar alertas de midia expirada/agendada/inativa.

### Testes

- [ ] Campanha com playlist vazia nao publica.
- [x] Ordem definida e respeitada no player.
- [x] Item inativo nao entra na fila.
- [x] Midia repetida toca conforme posicoes configuradas.
- [x] Helpers do playlist builder normalizam legado, API e payload de salvamento.

## SPEC-003 — Ciclo de Vida de Campanha

Objetivo: separar rascunho, validacao, publicacao, pausa, expiracao e arquivamento.

### Backend

- [ ] Definir enum final de status da campanha.
- [ ] Implementar validacao antes de publicar.
- [ ] Criar endpoint `POST /campaigns/{id}/validate`.
- [ ] Criar endpoint `POST /campaigns/{id}/publish`.
- [ ] Criar endpoint `POST /campaigns/{id}/pause`.
- [ ] Criar endpoint `POST /campaigns/{id}/resume`.
- [ ] Criar endpoint `POST /campaigns/{id}/archive`.
- [ ] Criar campanha emergencial.
- [ ] Criar regra de prioridade.
- [ ] Criar deteccao de conflito de agenda.
- [ ] Criar tabela `campaign_conflicts`.

### Frontend

- [ ] Mostrar status de ciclo de vida.
- [ ] Adicionar acoes publicar/pausar/retomar/arquivar.
- [ ] Mostrar erros de validacao antes de publicar.
- [ ] Mostrar conflitos de agenda.
- [ ] Mostrar prioridade e emergencia.

## SPEC-004 — Segmentacao e Grupos de Dispositivos

Objetivo: permitir alvo por dispositivo, grupo, unidade, cidade, tags e sistema operacional.

### Banco

- [ ] Criar `device_groups`.
- [ ] Criar `device_group_members`.
- [ ] Criar `campaign_target_rules`.
- [ ] Criar indices por tenant/localidade/tags.

### Backend

- [ ] Resolver alvos da campanha por regras.
- [ ] Expor preview de dispositivos atingidos.
- [ ] Atualizar invalidacao de cache por alvos resolvidos.

### Frontend

- [ ] Criar CRUD de grupos.
- [ ] Criar seletor de regras de alvo na campanha.
- [ ] Mostrar quantidade de players afetados.

## SPEC-005 — Entrega da Campanha por Player

Objetivo: painel operacional que confirma se a campanha chegou, sincronizou e executou.

### Banco

- [ ] Criar `campaign_delivery_status`.
- [ ] Criar `device_queue_snapshots`.
- [ ] Criar `device_heartbeats`.
- [ ] Criar `player_events`.

### Backend

- [ ] Expandir heartbeat para receber estado atual completo.
- [ ] Salvar ultimo estado operacional do player.
- [ ] Criar endpoint `GET /campaigns/{id}/delivery`.
- [ ] Comparar versao esperada vs atual.
- [ ] Comparar fila esperada vs atual.
- [ ] Calcular status final: sincronizado, pendente, offline, erro, executando.
- [ ] Criar endpoint de sync em lote por campanha.

### Frontend

- [ ] Criar tela "Entrega" dentro da campanha.
- [ ] Mostrar dispositivos alvo.
- [ ] Mostrar versao esperada/atual.
- [ ] Mostrar fila esperada/atual.
- [ ] Mostrar midia atual e ultimo erro.
- [ ] Botao "Forcar sincronizacao".

### Testes

- [ ] Campanha publicada mas nao entregue.
- [ ] Campanha entregue mas nao executada.
- [ ] Player offline.
- [ ] Fila divergente.
- [ ] Versao divergente.

## SPEC-006 — Estado Atual do Player

Objetivo: player reportar estado operacional completo.

### Player

- [ ] Reportar `current_campaign_id`.
- [ ] Reportar `current_config_version`.
- [ ] Reportar `current_media_id`.
- [ ] Reportar `current_media_name`.
- [ ] Reportar `queue_version`.
- [ ] Reportar `storage_used`.
- [ ] Reportar `storage_free`.
- [ ] Reportar `app_version`.
- [ ] Reportar `os`.
- [ ] Reportar `screen_resolution`.
- [ ] Reportar `last_error`.
- [ ] Reportar `playback_status`.

### Backend

- [ ] Persistir estado atual no device.
- [ ] Criar historico em `device_heartbeats`.
- [ ] Criar eventos em `player_events`.

## SPEC-007 — Comandos Remotos 2.0

Objetivo: comandos com ciclo de vida completo, resultado e auditoria.

**Detalhamento em `docs/specs/003-player-comandos-nativos/`** (auditoria 2026-05-22 identificou bug real: bridge nativo Electron/Capacitor incompleto).

### Backend

- [x] Revisar `device_commands` (migration 20260521_0915 ja aplicada).
- [~] Criar `device_command_results` — adiar; usar `result` JSON em `device_commands` ja eh suficiente para SPEC 003.
- [x] Implementar estados: pending, sent, received, executing, completed, failed, expired, cancelled (migration 20260521_0915).
- [ ] Implementar expiracao automatica via Celery task `expire_stale_commands` (SPEC 003).
- [ ] Implementar comandos em lote (escopo de Central de Comandos futura).
- [x] Registrar quem enviou comando (campo `requested_by`).
- [ ] Auditar comandos sensiveis (campo `is_destructive` em SPEC 003).

### Player

- [x] Confirmar recebimento (`POST /commands/{id}/received`).
- [x] Confirmar execucao iniciada (`POST /commands/{id}/started`).
- [x] Confirmar sucesso/falha (`POST /commands/{id}/ack`).
- [~] Implementar `take_screenshot` (SPEC 003 — Electron sim, Android limitado).
- [ ] Implementar `get_logs`.
- [ ] Implementar `identify_screen`.
- [x] Implementar `set_volume`, `mute`, `unmute` (ja em `commands.js`).
- [ ] **SPEC 003: bridge nativo Electron (`preload.js` + `contextBridge` + IPC handlers reais em `main.js`).**
- [ ] **SPEC 003: plugin Capacitor `PlayWaveNativePlugin` para Android.**
- [ ] **SPEC 003: provisionamento Device Owner Android documentado.**
- [ ] **SPEC 003: pre-ACK para comandos destrutivos.**

### Frontend

- [ ] Criar Central de Comandos consolidada (escopo futuro).
- [ ] **SPEC 003: timeline de status por comando em DispositivoDetalhe.**
- [ ] **SPEC 003: badge "Nao suportado" para `failed` com `platform_unsupported=true`.**
- [ ] **SPEC 003: modal de confirmacao destrutiva.**
- [ ] **SPEC 003: tooltips por comando explicando plataformas suportadas.**

## SPEC-009 — Audio Indoor e Spots

Reescopo apos auditoria 2026-05-22: apenas o item de politica de conflito foi destacado em SPEC 005. Demais itens (upload multiplo, pastas, schedule, spots) ficam para SPEC futura (radio v2).

### Politica de conflito audio visual vs radio

**Detalhamento em `docs/specs/005-conflito-audio-midia/`.**

- [x] Migration `audio_policy_enum` + colunas em tenants/devices/campaigns/media.
- [x] Coluna `has_audio` em media com deteccao via ffprobe.
- [x] Backend resolver hierarquico (media > campaign > device > tenant > auto).
- [x] Player hook `useAudioConflictResolver`.
- [x] AudioPlayer com fade in/out de 200ms.
- [x] Selector reusavel em 4 telas admin (Campaign, Media, Device, Tenant).
- [x] Backfill de `audio_policy` baseado em `video_muted` legado.

### Outras (escopo futuro de radio v2)

- [ ] Upload multiplo de audio.
- [ ] Deteccao automatica de duracao de audio.
- [x] Criar `audio_playlist_items` relacional.
- [x] Criar `audio_folders` e `audio_folder_tracks`.
- [ ] Criar `audio_playlist_schedules`.
- [ ] Criar `audio_spots` e `audio_spot_schedules`.
- [ ] Regras de sequencial/shuffle no AudioPlayer (shuffle hoje so flag, sem logica).
- [ ] Anti-repeticao no shuffle.
- [ ] Frontend: tela de pastas, spots, schedules, upload multiplo.

## SPEC-012 — Pareamento e Revogacao de Token

**Detalhamento em `docs/specs/004-pareamento-revocacao/`.**

Objetivo: garantir que regenerar codigo de pareamento expulse player antigo de fato, e adicionar defesa em profundidade via `token_version`.

- [ ] Migration `device_pairing_events` (auditoria).
- [ ] Validacao de `token_version` em `get_device_by_token`.
- [ ] Header obrigatorio `X-Device-Token-Version` (compat-period 1 release).
- [ ] Endpoint `POST /devices/{id}/force-repair` (sem trocar codigo).
- [ ] Endpoint `GET /devices/{id}/pairing-events`.
- [ ] Player armazena `token_version` em PairingStorage.
- [ ] Player trata 401/403 com error_code especifico via `forceRepair()`.
- [ ] SSE `pairing:revoked` para revocacao em tempo real.
- [ ] Gerenciador: modal de confirmacao com impacto + timeline de eventos.

## SPEC-013 — OSD Configuravel com Musica Atual

**Detalhamento em `docs/specs/006-osd-musica-atual/`.**

Objetivo: exibir nome da musica atual no player como overlay configuravel (posicao, duracao, opacidade, fonte).

- [ ] Migration `osd_position_enum`, `osd_font_size_enum`, colunas em tenants/devices.
- [ ] Colunas `current_audio_track_*` em devices.
- [ ] Backend resolver hierarquico device > tenant > default.
- [ ] Endpoints `PATCH /devices/{id}/osd-config` e `PATCH /tenants/{id}/osd-config`.
- [ ] Heartbeat estendido com track atual.
- [ ] AudioPlayer prop `onTrackChange` com debounce 500ms.
- [ ] PlayerOSD slot novo para musica atual.
- [ ] Frontend admin: OSDConfigForm + OSDConfigPreview reusaveis.
- [ ] DispositivoDetalhe mostra "Tocando agora" com elapsed.

## SPEC-008 — Cache por Midia e Dispositivo

Objetivo: controlar download/cache para evitar tela preta e operar offline.

### Banco

- [ ] Criar `device_cache_status`.

### Backend

- [ ] Expor cache esperado por device.
- [ ] Receber status de cache do player.
- [ ] Criar endpoint `GET /devices/{id}/cache`.

### Player

- [ ] Comparar `file_hash`.
- [ ] Comparar `file_version`.
- [ ] Baixar antes de tocar quando politica exigir.
- [ ] Trocar arquivo apos finalizar midia atual.
- [ ] Tentar proxima midia se download falhar.

### Frontend

- [ ] Mostrar cache por player.
- [ ] Mostrar midias falhadas.
- [ ] Acao "limpar cache".

## SPEC-009 — Audio Indoor e Spots

Objetivo: radio indoor completa com playlists e spots promocionais.

### Backend

- [ ] Upload multiplo de audio.
- [ ] Deteccao automatica de duracao de audio.
- [x] Criar `audio_playlist_items`.
- [ ] Criar `radio_points`.
- [ ] Criar `radio_point_playlists`.
- [ ] Criar `audio_spots`.
- [ ] Criar `audio_spot_schedules`.
- [ ] Criar regras de sequencial/shuffle.
- [ ] Criar regra anti repeticao no shuffle.

### Frontend

- [ ] Tela de musicas.
- [ ] Tela de playlists de audio.
- [ ] Tela de pontos/radios.
- [ ] Tela de spots.
- [ ] Upload multiplo.
- [ ] Selecao multipla.
- [ ] Configurar sequencial/aleatorio.

### Player

- [ ] Respeitar playlist de audio por campanha.
- [ ] Respeitar playlist por device/grupo/ponto.
- [ ] Executar spots conforme agenda.
- [ ] Registrar logs de spots.

## SPEC-010 — Auditoria e Permissoes

Objetivo: rastrear acoes e controlar acesso por papel.

### Banco

- [ ] Criar `audit_logs`.
- [ ] Criar estrutura de permissoes por papel.

### Backend

- [ ] Middleware/helper de auditoria.
- [ ] Auditar campanha criada/editada/publicada/pausada.
- [ ] Auditar midia criada/substituida/excluida.
- [ ] Auditar comandos remotos.
- [ ] Auditar alteracoes de dispositivos.
- [ ] Registrar antes/depois.

### Frontend

- [ ] Esconder acoes conforme permissao.
- [ ] Criar tela de auditoria para admin/super_admin.

## SPEC-011 — Relatorios e Saude do Sistema

Objetivo: consolidar visao operacional e tecnica.

### Backend

- [ ] Relatorio por campanha.
- [ ] Relatorio por midia.
- [ ] Relatorio por dispositivo.
- [ ] Relatorio de comandos.
- [ ] Endpoint de saude Redis.
- [ ] Endpoint de saude Celery.
- [ ] Endpoint de saude banco.

### Frontend

- [ ] Central de Relatorios.
- [ ] Tela de Saude do Sistema.
- [ ] Cards de players offline/atrasados.
- [ ] Grafico de execucao por campanha.
- [ ] Grafico de erros por player.

## Checklist de Qualidade por Spec

Antes de considerar uma spec pronta:

- [ ] Requisitos escritos em `requirements.md`.
- [ ] Design tecnico escrito em `design.md`.
- [ ] Tasks quebradas em backend/frontend/player/testes.
- [ ] Migration criada quando houver banco.
- [ ] Compatibilidade com dados existentes avaliada.
- [ ] Endpoint documentado.
- [ ] Frontend sem mock/localStorage para funcionalidade real.
- [ ] Player atualizado quando contrato muda.
- [ ] Cache/invalidacao avaliados.
- [ ] Auditoria avaliada.
- [ ] Testes ou plano manual registrado.
- [ ] Build/compilacao executado.
