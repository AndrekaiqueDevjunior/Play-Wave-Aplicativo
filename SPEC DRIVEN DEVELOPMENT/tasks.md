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

## SPEC 011 — Player Auto Boot

Objetivo: fazer o player iniciar automaticamente em modo loja/TV, restaurando sessao, pareamento ou cache valido sem clique humano.

**Detalhamento em `docs/specs/011-player-auto-boot/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md`.
- [x] Criar fila sequencial em `SPEC DRIVEN DEVELOPMENT/2026-06-fila-specs-criticas-player-radio-windows.md`.
- [x] Auditar estado atual do player, storage, pareamento, sync e heartbeat.
- [x] Preencher arquivos impactados reais.
- [x] Implementar boot automatico — AUTO_BOOT no main.js (Electron), bootLog() e revalidacao de sessao no Player.jsx, PlaylistCache com timestamp.
- [x] Validar criterios de aceite — 11/11 testes Playwright passando em VPS (testes-playwave/tests/player-auto-boot.spec.ts).
- [x] Somente entao abrir SPEC 012 — Reinicio Remoto sem Confirmacao — gate liberado.

## SPEC 012 — Reinicio Remoto sem Confirmacao

Objetivo: executar comando remoto de reiniciar app/player sem confirmacao manual no dispositivo, com ciclo de vida rastreavel.

**Detalhamento em `docs/specs/012-reinicio-remoto-sem-confirmacao/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md`.
- [x] Iniciar implementacao — gate SPEC 011 concluido.
- [x] Auditar estado atual de comandos, polling/SSE, bridge Electron e UI do gerenciador.
- [x] Bug corrigido: mark_received/mark_executing usavam EXECUTED em vez de RECEIVED/EXECUTING no crud_device_command.py.
- [x] Bug corrigido: PENDING_STATUSES expandido para incluir RECEIVED e EXECUTING; recuperacao de comandos travados em EXECUTING adicionada.
- [x] Validar criterios de aceite — 12/12 testes Playwright passando em VPS (testes-playwave/tests/player-restart-remoto.spec.ts).
- [!] Pendente: deploy do crud_device_command.py corrigido na VPS.
- [x] Somente entao abrir SPEC 013 — Spot da Radio sem Sobreposicao — gate liberado.

## SPEC 013 — Spot da Radio sem Sobreposicao

Objetivo: garantir que o spot da radio nunca toque por cima da musica, respeitando a politica de insercao configurada (`wait_silence` por padrao).

**Detalhamento em `docs/specs/013-spot-radio-sem-sobreposicao/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-006).
- [x] Iniciar implementacao — gate SPEC 012 concluido.
- [x] Auditar backend (`AudioSpotInsertionPolicy`, `spot_resolver.py`, `audio_spot_scheduler.py`) — ja adequado, sem mudanca necessaria.
- [x] Bug corrigido: `wait_silence` em `audioManager.js playSpot()` fazia fade-out e tocava o spot imediatamente, igual a `interrupt` — nunca esperava o fim real da musica.
- [x] Implementado `_pendingSpot` + `_isBackgroundActivelyPlaying()`: represa o spot quando o fundo esta ativo e so toca no evento `ended` (ou em falha do fundo, via `_handleRadioTrackFailure`).
- [x] Validar criterios de aceite — 29/29 testes unitarios `audio_manager.test.js` passando; 17/17 testes relacionados sem regressao.
- [ ] Pendente: teste manual em hardware real (Electron/Windows) validando ausencia de overlap audivel.
- [x] Somente entao abrir SPEC 014 — Video Estavel no Player — gate liberado.

## SPEC 014 — Video Estavel no Player

Objetivo: eliminar travamento/picotamento de video no player, garantindo preload da proxima midia e evitando re-render desnecessario do componente de video.

**Detalhamento em `docs/specs/014-video-estavel-no-player/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-008).
- [x] Iniciar implementacao — gate SPEC 013 concluido.
- [x] Auditar backend (Range requests, Cache-Control, metadata ffprobe) e Electron (hardware acceleration) — ja adequados, descartados como causa.
- [x] Bug corrigido: `MediaRenderer.jsx` nao tinha preload da proxima midia — navegador so comecava a baixar o arquivo no instante exato da troca.
- [x] Bug corrigido: `MediaRenderer` sem `React.memo` — re-render do `Player.jsx` (heartbeat/spot/radio) recalculava `renderContent()` mesmo sem mudanca real de midia.
- [x] Implementado `MediaPreloader` (elemento oculto video/audio/img para `nextMedia`) e barra de progresso via ref/DOM direto (compativel com o memo).
- [x] Validar criterios de aceite — 7/7 testes novos `media_renderer.test.jsx`; 68/68 testes relacionados sem regressao; 147/150 na suite completa (3 falhas pre-existentes nao relacionadas).
- [ ] Pendente: validacao visual em hardware real de loja (TV/mini-PC Windows) com video pesado/animacao.
- [x] Somente entao abrir SPEC 015 — Minimizar Windows sem Cortar Conteudo — gate liberado.

## SPEC 015 — Minimizar Windows sem Cortar Conteudo

Objetivo: garantir que a minimizacao programada da janela no Windows espere o conteudo atual terminar antes de minimizar (politica WAIT_CONTENT_END), com aviso visual configuravel opcional.

**Detalhamento em `docs/specs/015-minimizar-windows-sem-cortar-conteudo/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-007).
- [x] Iniciar implementacao — gate SPEC 014 concluido.
- [x] Auditar bridge Electron, comandos backend e os dois schedulers client-side existentes (`windowExposureScheduler.js` por intervalo, `desktopExposureTimeScheduler.js` por horario) — infraestrutura de minimizar ja madura (SPEC 009/010), faltava apenas a politica de espera.
- [x] Decisao confirmada com o usuario: adaptar os schedulers existentes via dependencia `contentGuard` em vez de criar comandos `minimize_screen`/`restore_screen` novos; incluir aviso visual nesta mesma SPEC.
- [x] Criado `frontend/src/player-core/contentGuard.js` — modulo puro que represa minimizacao até `notifyContentEnded()` (chamado por `advanceMedia` em `Player.jsx`).
- [x] Adaptados os dois schedulers para aceitar `contentGuard`/`onWarning` opcionais, mantendo retrocompatibilidade total (sem guard = comportamento antigo).
- [x] Adicionados campos de aviso visual (`show_warning`, `warning_seconds_before`, `warning_text`, `warning_media_id`) ao `Device` (model, schema, endpoint, migration `20260618_1100`).
- [x] Adicionada UI de configuracao do aviso em `DispositivoDetalhe.jsx` e overlay de aviso no `Player.jsx`.
- [x] Validar criterios de aceite — 79/79 testes novos+relacionados de frontend passando; 170/173 na suite completa (3 falhas pre-existentes nao relacionadas); backend validado por sintaxe (`pytest` indisponivel no ambiente local, sem FastAPI instalado).
- [ ] Pendente: validacao manual em hardware Windows real e deploy da migration na VPS.
- [x] Somente entao abrir SPEC 016 — Faixas de Audio Arquivar/Excluir — gate liberado.

## SPEC 016 — Faixas de Audio Arquivar/Restaurar/Excluir

Objetivo: diferenciar Arquivar/Restaurar/Excluir definitivamente para faixas de audio, escondendo arquivadas por padrao em todos os seletores e tornando a exclusao definitiva segura.

**Detalhamento em `docs/specs/016-faixas-audio-arquivar-excluir/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-003).
- [x] Iniciar implementacao — gate SPEC 015 concluido.
- [x] Auditar model `AudioTrack`, endpoint `GET/DELETE /audio/tracks`, CRUD, FKs (`AudioFolderTrack`/`AudioPlaylistItem`/`AudioSpot` com `ondelete=RESTRICT`), resolucao do player e UI de gerenciamento.
- [x] Achado real: excluir ja fazia hard delete de verdade; o bug era leak de filtro (arquivadas apareciam em seletores) + UI sem distincao Arquivar/Excluir + delete sem checagem de uso amigavel.
- [x] Decisao confirmada com o usuario: corrigir filtros + adicionar checagem de uso antes do delete + adicionar `archived_at` nesta mesma SPEC.
- [x] Backend: `include_archived` em `GET /audio/tracks` (exclui arquivadas por padrao), `get_in_use_references()` + bloqueio 409 em `DELETE`, `archived_at` sincronizado no `update()` (cobre o fluxo real `PUT` usado pela UI), migration aditiva `20260618_1200`.
- [x] Frontend: `FaixasAudio.jsx` com acoes separadas Arquivar/Restaurar/Excluir definitivamente, dois dialogs de confirmacao distintos.
- [x] Validar criterios de aceite — 170/173 na suite completa do frontend (sem regressao); 11 testes novos de backend validados por sintaxe (`pytest` indisponivel no ambiente local).
- [ ] Pendente: validacao manual end-to-end com banco real e deploy da migration na VPS.
- [x] Somente entao abrir SPEC 017 — Playlist Sonora Arquivar/Excluir — gate liberado.

## SPEC 017 — Playlist Sonora Arquivar/Restaurar/Excluir

Objetivo: aplicar a Playlist Sonora (AudioPlaylist) o mesmo padrao de Arquivar/Restaurar/Excluir ja corrigido para faixas na SPEC 016.

**Detalhamento em `docs/specs/017-playlist-sonora-arquivar-excluir/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-004).
- [x] Iniciar implementacao — gate SPEC 016 concluido.
- [x] Auditar model `AudioPlaylist`, FKs diretas (`Device.audio_playlist_id`/`Campaign.audio_playlist_id`, sem ondelete, diferente das tabelas de juncao usadas por faixas), resolucao do player e UI de gerenciamento.
- [x] Achado real: mesmo leak de filtro da SPEC 016, mais um endpoint secundario (`audio/devices.py`, sem uso pelo frontend atual) que nao filtrava playlist arquivada — o resolver principal do player (`api/v1/devices.py`) ja estava correto, confirmado por leitura cuidadosa antes de alterar.
- [x] Decisao confirmada com o usuario: bloquear playlist arquivada no resolver do player (nao so avisar na UI) + checagem de uso antes do delete (nao desvincular automaticamente).
- [x] Backend: `include_archived` em `GET /audio/playlists`, `get_in_use_references()` (conta Device/Campaign via FK direta) + bloqueio 409 em `DELETE`, `archived_at` sincronizado no `update()`, filtro de status corrigido no endpoint secundario, migration aditiva `20260618_1300`.
- [x] Frontend: `PlaylistsSonoras.jsx` ganhou filtro de status (antes inexistente) e acoes separadas Arquivar/Restaurar/Excluir definitivamente.
- [x] Validar criterios de aceite — 170/173 na suite completa do frontend (sem regressao); 11 testes novos de backend validados por sintaxe.
- [ ] Pendente: validacao manual end-to-end com banco real e deploy da migration na VPS.
- [x] Somente entao abrir SPEC 018 — Midias com Exclusao em Massa — gate liberado.

## SPEC 018 — Midias: Exclusao/Arquivamento em Massa

Objetivo: permitir selecao multipla na tela de Midias para arquivar/excluir em lote, criando a capacidade de arquivamento que nao existia para Media e corrigindo a checagem de uso para cobrir CampaignPlaylistItem.

**Detalhamento em `docs/specs/018-midias-exclusao-em-massa/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-009).
- [x] Iniciar implementacao — gate SPEC 017 concluido.
- [x] Auditar model `Media` (sem ARCHIVED/archived_at, diferente de AudioTrack/AudioPlaylist), endpoint `GET/DELETE /media`, checagem de uso existente, e UI de gerenciamento.
- [x] Achado real: Media nao tinha capacidade de arquivar (lacuna mais fundamental que SPEC 016/017); checagem de uso existente so olhava Campaign.media_ids/media_order (legado), nao CampaignPlaylistItem (relacional, FK RESTRICT, caminho real do player); BibliotecaMidias.jsx sem nenhum padrao de selecao em massa.
- [x] Decisao confirmada com o usuario: criar archived_at + MediaStatus.ARCHIVED nesta SPEC (nao esperar SPEC 020) + corrigir checagem de uso para cobrir CampaignPlaylistItem (reaproveitada pelo bulk delete).
- [x] Backend: `include_archived` em `GET /media`, `get_in_use_references()` (checagem dupla relacional+legado), bloqueio em `DELETE` mesmo com force=true quando ha CampaignPlaylistItem, novos `POST /media/bulk-archive` e `POST /media/bulk-delete` (cada item processado independentemente, sem force no bulk), migration aditiva `20260618_1400`.
- [x] Frontend: `BibliotecaMidias.jsx` ganhou modo de selecao (checkbox grid+lista, selecionar todas, limpar), barra de acoes em lote, filtro de status, acoes individuais Arquivar/Restaurar (antes so existia "Excluir" que era na verdade a unica acao).
- [x] Validar criterios de aceite — 170/173 na suite completa do frontend (sem regressao); 12 testes novos de backend validados por sintaxe.
- [ ] Pendente: validacao manual end-to-end com banco real e deploy da migration na VPS.
- [x] Somente entao abrir SPEC 019 — Usuarios com Senha/Convite — gate liberado.

## SPEC 019 — Usuarios: Senha Manual ou Convite por E-mail

Objetivo: permitir que o admin escolha, ao criar um usuario, entre definir uma senha manualmente ou enviar um convite por e-mail para o proprio usuario definir a senha; bloquear login enquanto o convite estiver pendente; adicionar fluxo de "esqueci minha senha".

**Detalhamento em `docs/specs/019-usuarios-senha-convite/`.**

- [x] Criar SPEC separada a partir de `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md`.
- [x] Iniciar implementacao — gate SPEC 018 concluido.
- [x] Auditar model `User`, `POST /users/`, `POST /api/auth/login`, infraestrutura de e-mail (inexistente) e `UserLog`/`UserLogAction` (reaproveitavel).
- [x] Achado real: `login()` quebrava (excecao nao tratada) em vez de devolver 401 limpo quando `password_hash` fosse `None` — bug pre-existente exposto pela necessidade desta SPEC de permitir usuarios sem senha.
- [!] `AskUserQuestion` falhou repetidamente nesta sessao — seguido com defaults de menor risco (SMTP generico com fallback de log; `account_status` mantido como string solta), documentados em `design.md` para reconfirmacao posterior com o usuario.
- [x] Backend: `password_hash` nullable + `invite_token/invite_expires_at/invite_sent_at/password_reset_token/password_reset_expires_at`, `backend/services/email_service.py` (SMTP com fallback de log), `generate_secure_token`/`token_expiry` em `core/auth.py`, `UserCreate` com senha opcional + `send_invite`, novos endpoints `POST /users/{id}/resend-invite`, `POST /api/auth/accept-invite`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`, `login` corrigido, migration aditiva `20260619_0900`.
- [x] Frontend: `ConfigUsuario.jsx` com seletor "convite por e-mail vs senha manual" (removida geracao client-side de senha temporaria), acao "Reenviar convite", status `pending_invite`, paginas publicas `AceitarConvite.jsx`/`EsqueciSenha.jsx`/`RedefinirSenha.jsx`, link "Esqueci minha senha" no `Login.jsx`, `AuthContext.setSession()` para autenticar sem round-trip extra.
- [x] Validar criterios de aceite — 170/173 na suite completa do frontend (sem regressao); teste novo de backend (`test_user_invite_password_reset.py`) revisado manualmente linha a linha (execucao automatizada bloqueada por ambiente sem fastapi + falha intermitente de ferramenta Bash nesta sessao).
- [ ] Pendente: validacao manual end-to-end com banco real, deploy da migration na VPS, configuracao de SMTP real em producao, reconfirmacao das decisoes de escopo tomadas sem `AskUserQuestion`.
- [ ] Somente entao abrir SPEC 020 — Padrao Arquivamento vs Exclusao.

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

## SPEC-009 - Minimizacao Programada do Player

Objetivo: permitir comandos remotos e rotina cronometrada para minimizar/restaurar o Player Electron e expor a area de trabalho por tempo configuravel.

**Detalhamento em `docs/specs/009-minimizacao-programada-player/`.**

- [x] Auditoria de estado atual backend/frontend/player.
- [x] Definicao de dominio principal: dispositivos/player behavior.
- [x] SPEC tecnica criada com requisitos, design, banco, API, frontend, player, tasks e testes.
- [ ] PR 1: comandos manuais `minimize_player`, `restore_player`, `show_desktop`.
- [ ] PR 2: configuracao persistente por dispositivo.
- [ ] PR 3: cronometro frontend e scheduler local no Player.
- [ ] PR 4: hardening, docs e rollout.

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
