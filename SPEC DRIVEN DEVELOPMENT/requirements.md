# PlayWave — Requirements Map

Data base: 2026-05-20

Este documento e o mapa de requisitos do PlayWave usando Spec Driven Development. Toda nova implementacao deve nascer aqui, passar pelo `design.md` e virar tarefa rastreavel em `tasks.md`.

## Visao Geral

PlayWave e uma plataforma de midia indoor/digital signage para administrar campanhas, playlists, midias, audio indoor e players em TVs/dispositivos.

O objetivo do produto e permitir que o administrador controle:

- o que toca;
- onde toca;
- quando toca;
- em qual ordem;
- com qual prioridade;
- com qual audio;
- com qual politica de cache;
- com qual fallback;
- e se realmente chegou, sincronizou e executou no player.

## Usuarios e Papeis

### Super Admin

Administra todos os tenants, usuarios, planos, configuracoes globais, infraestrutura e auditoria completa.

### Admin

Administra uma conta/tenant, cria campanhas, dispositivos, midias, grupos, relatorios e comandos.

### Operator

Opera campanhas e players no dia a dia, pode pausar, sincronizar, enviar comandos e acompanhar entrega.

### Content Manager

Gerencia biblioteca de midias, playlists visuais e playlists de audio.

### Support

Acessa saude dos players, logs, screenshots, comandos de suporte e diagnosticos.

### Viewer

Visualiza campanhas, players, relatorios e status, sem alterar dados.

## Modulos do Produto

### MOD001 — Autenticacao, Usuarios e Permissoes

O sistema deve permitir login seguro, controle de usuarios por tenant e matriz de permissoes por papel.

Requisitos:

- Autenticar usuarios administrativos.
- Associar usuarios a tenant.
- Restringir acesso por papel.
- Registrar acoes sensiveis em auditoria.
- Impedir acesso cruzado entre tenants.

### MOD002 — Biblioteca de Midias Inteligentes

O sistema deve gerenciar imagens, videos, audios e URLs com metadados reais, periodo de exibicao e versionamento de arquivo.

Requisitos:

- Detectar automaticamente duracao de video e audio.
- Salvar `duration_seconds` como duracao real do arquivo.
- Salvar `display_duration_seconds` como duracao configurada para reproducao.
- Para video/audio, tocar ate o fim por padrao.
- Para imagem/link/html, exigir ou aplicar duracao de exibicao.
- Permitir `starts_at` e `ends_at` na propria midia.
- Calcular disponibilidade: ativa, agendada, expirada, inativa, processando, com erro.
- Permitir substituir arquivo mantendo o mesmo `media_id`.
- Criar historico em `media_versions`.
- Mostrar uso da midia em campanhas.
- Bloquear exclusao perigosa de midia em uso, salvo confirmacao forte.
- Enviar ao player somente midias validas.

Critérios de aceite:

- Ao subir video, a duracao real e detectada e salva.
- Ao subir audio, a duracao real e detectada e salva.
- Imagem continua usando duracao manual/padrao.
- Midia expirada nao entra na fila do player.
- Substituir arquivo nao remove a midia da campanha.
- Player recebe `file_hash` e `file_version` atualizados.

### MOD003 — Campanhas e Playlists Visuais

Campanha e a unidade operacional que define quais midias tocam, em quais players e com quais regras.

Requisitos:

- Separar ciclo de vida: rascunho, validacao, publicada, ativa, pausada, expirada, arquivada.
- Validar campanha antes de publicar.
- Impedir publicacao sem midia valida.
- Impedir publicacao sem alvo valido.
- Permitir prioridade entre campanhas.
- Tratar conflito de agenda.
- Permitir campanha emergencial.
- Permitir ordem customizada de midias.
- Permitir duracao customizada por item.
- Permitir ativar/desativar item dentro da campanha.
- Permitir repetir a mesma midia na playlist.
- Permitir periodo de exibicao por item.
- Segmentar por dispositivo, grupo, unidade, cidade, tags e sistema operacional.
- Gerar nova `config_version` a cada mudanca relevante.

Critérios de aceite:

- Player respeita ordem configurada.
- Campanha pausada nao toca.
- Campanha fora do periodo nao toca.
- Campanha emergencial sobrescreve campanhas normais conforme regra.
- Alteracao em campanha invalida cache dos players afetados.

### MOD004 — Dispositivos e Players

Dispositivo representa uma TV/player pareado. Player e o app que consome playlists, executa midias e reporta estado.

Lacuna atual registrada:

- O player precisa evoluir para comandos remotos mais fortes, com diferenca clara entre recarregar player, reiniciar app, reiniciar dispositivo e desligar dispositivo fisico. → coberto por SPEC 003.
- Ao trocar/regenerar o codigo de pareamento, o token antigo do player deve ser invalidado com seguranca para impedir sincronizacao indevida. → coberto por SPEC 004.
- O player precisa ter regra clara para conflito entre audio da midia visual e radio ambiente. → coberto por SPEC 005.
- O player deve poder exibir o nome da musica atualmente tocando como overlay configuravel. → coberto por SPEC 006.

Requisitos:

- Parear dispositivo por codigo/token.
- Invalidar token antigo quando codigo de pareamento for regenerado.
- Manter `last_seen_at`, status, versao do app, sistema operacional e resolucao.
- Player deve reportar:
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
  - `last_error`;
  - `playback_status`.
- Criar fila real de reproducao por dispositivo.
- Confirmar recebimento, sincronizacao e execucao.
- Suportar modo offline com cache local.
- Registrar logs de reproducao e erros.

Critérios de aceite:

- Admin ve se player esta online/offline.
- Admin ve qual campanha/midia esta tocando.
- Player continua com cache local se backend falhar.
- Player pula midia com erro e tenta proxima valida.

### MOD005 — Entrega da Campanha

O sistema deve mostrar a entrega real da campanha por dispositivo.

Requisitos:

- Criar endpoint de entrega por campanha.
- Mostrar por dispositivo:
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
  - status final: sincronizado, pendente, offline, erro ou executando.
- Permitir forcar sincronizacao da campanha.

Critérios de aceite:

- Operador consegue confirmar se a campanha chegou no player.
- Operador consegue identificar divergencia de versao/fila.
- Operador consegue acionar sync em lote.

### MOD006 — Comandos Remotos

O sistema deve permitir executar comandos remotos em players.

Lacuna atual registrada:

- Os comandos remotos precisam evoluir para um ciclo operacional completo, com status mais granular, timeout, erro claro por plataforma e suporte separado para app/player/dispositivo fisico.

Atualizacao em 2026-05-22 (apos auditoria):

- Backend ja tem o lifecycle completo de comando (PENDING/SENT/RECEIVED/EXECUTING/COMPLETED/FAILED/EXPIRED/CANCELLED) e endpoints `/received`, `/started`, `/ack`.
- Bug real: comandos de energia (`restart_app`, `restart_device`, `shutdown_device`) caem em `platformUnsupported` no player porque o bridge nativo Electron (`window.__ELECTRON__.player`) eh boolean e nao expoe metodos, e o plugin Capacitor (`window.PlayWaveNative`) nao existe.
- Solucao na SPEC 003: reescrever `preload.js` para usar `contextBridge`, adicionar IPC handlers reais em `main.js`, criar plugin Capacitor `PlayWaveNativePlugin`, assumir Device Owner para Android, expandir gerenciador com timeline de status detalhada por comando.

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

Estados obrigatorios:

- pending;
- sent;
- received;
- running;
- success;
- failed;
- expired;
- cancelled.

Critérios de aceite:

- Todo comando tem historico de status.
- Comando expira se player nao confirmar dentro do prazo.
- Admin consegue ver resultado/erro do comando.

### MOD007 — Audio Indoor, Radio e Spots

O sistema deve permitir playlists de audio independentes ou associadas a campanhas/dispositivos.

Lacuna atual registrada:

- Falta evoluir para upload multiplo de musicas. → SPEC futura (escopo de r adio v2).
- Falta criar pastas/agrupamentos de audio. → SPEC futura.
- Falta agendamento de radio por horario, data e dias da semana. → SPEC futura.
- Falta criar spots recorrentes a cada X minutos. → SPEC futura.
- Falta politica de conflito entre radio e video/midia visual com audio. → coberto por SPEC 005.

Resumo do plano em fases (etapa 2 do diagnostico de 2026-05-22):

- **Fase atual (SPECs 003-006):** corrigir bugs do player que o cliente reclamou — shutdown, pareamento, conflito audio, OSD musica.
- **Fase seguinte:** evoluir radio (upload multiplo, pastas, schedule por horario, spots).

Requisitos:

- Upload unico e multiplo de musicas.
- Detectar duracao automatica de audio.
- Criar pastas/categorias operacionais de audio.
- Criar playlists de audio.
- Permitir playlist composta por audios individuais e pastas.
- Permitir agendamento de playlists/pastas por horario.
- Vincular playlist por campanha, dispositivo, grupo, ponto/local ou unidade.
- Suportar modo `sequential` e `shuffle`.
- Evitar repeticao excessiva no shuffle.
- Criar spots promocionais.
- Spot deve tocar a cada X minutos, respeitando data, horario, prioridade e alvo.
- Definir politica de audio entre radio e midia visual:
  - `radio_only`;
  - `media_audio_only`;
  - `mix`;
  - `auto`;
  - `muted_video_with_radio`.
- Registrar logs de execucao de audio e spots.

Critérios de aceite:

- Radio sem playlist nao toca.
- Playlist fora do periodo nao toca.
- Spot nao toca sobre outro spot.
- Player respeita sequencial/aleatorio.

### MOD008 — Cache, Download e Fallback

O sistema deve controlar cache de midias por player.

Estados de cache:

- not_downloaded;
- downloading;
- cached;
- failed;
- expired;
- deleted.

Politicas:

- streaming;
- download_before_play;
- hybrid;
- cache_required.

Requisitos:

- Player deve invalidar cache se `file_hash` ou `file_version` mudar.
- Player deve evitar tela preta durante atualizacao.
- Player deve trocar arquivo preferencialmente apos terminar a midia atual.
- Se download falhar, registrar erro e tentar proxima midia valida.

### MOD009 — Relatorios e Auditoria

O sistema deve registrar execucao operacional e mudancas administrativas.

Auditoria obrigatoria:

- quem criou campanha;
- quem editou campanha;
- quem publicou campanha;
- quem pausou campanha;
- quem enviou comando;
- quem reiniciou player;
- quem apagou midia;
- antes/depois das alteracoes.

Relatorios:

- execucao por campanha;
- execucao por midia;
- execucao por dispositivo;
- falhas por player;
- cache/download;
- comandos remotos.

### MOD010 — Observabilidade e Saude do Sistema

O sistema deve expor saude operacional para suporte.

Requisitos:

- Tela de saude com Redis, Celery, banco, backend e players.
- Medir latencia dos endpoints de player.
- Medir falhas de sync.
- Mostrar filas Celery.
- Mostrar players atrasados/offline.

## Modos de Reproducao

O sistema deve suportar conceitualmente e tecnicamente:

- `video_only`;
- `video_muted`;
- `video_with_background_audio`;
- `image_only`;
- `image_with_background_audio`;
- `audio_only`;
- `web_url`;
- `html_template`;
- `split_screen`;
- `ticker_overlay`.

## Requisitos Nao Funcionais

- Endpoints do player devem ser rapidos e cacheaveis.
- Playlist deve usar Redis e invalidacao direcionada por dispositivo afetado.
- Operacoes pesadas de midia devem ir para background quando possivel.
- O sistema deve manter compatibilidade com campanhas existentes.
- Nenhuma substituicao de arquivo deve gerar novo `media_id`.
- Toda regra sensivel deve ter log/auditoria.
- O player deve conseguir operar temporariamente offline.
- O frontend nao deve depender de mock/localStorage para funcionalidades administrativas reais.

## Prioridades do Produto

### P0 — Controle Operacional Basico

- Midias inteligentes (SPEC 001 — em andamento).
- Playlist real por campanha (SPEC 002 — backend pronto).
- Player respeitar validade, ordem e duracao.
- Entrega da campanha por player (SPEC 005 do mapa interno SDD — diferente das SPECs em `docs/specs/`).

### P1 — Confiabilidade Operacional

- **Comandos remotos completos** → SPEC 003 (`docs/specs/003-player-comandos-nativos/`).
- **Invalidacao segura de token ao trocar codigo de pareamento** → SPEC 004 (`docs/specs/004-pareamento-revocacao/`).
- **Politica de conflito entre radio e midia visual com audio** → SPEC 005 (`docs/specs/005-conflito-audio-midia/`).
- **Overlay com nome da musica atual** → SPEC 006 (`docs/specs/006-osd-musica-atual/`).
- Estado atual do player.
- Cache por midia/dispositivo.
- Auditoria administrativa.

### P2 — Radio Indoor Completa

- Upload multiplo de audios.
- Pastas/agrupamentos de musicas.
- Playlists de audio.
- Agendamento de radio por horario.
- Spots.
- Regras por ponto/localidade.

### P3 — Escala e Relatorios

- Tabelas relacionais completas.
- Relatorios avancados.
- Observabilidade e metricas.

## Convencao de Numeracao

A partir de 2026-05-22, especificacoes completas (com requirements, design, banco, contrato, frontend, player, tasks e tests) vivem em `docs/specs/NNN-nome-curto/`. Use o template em `docs/specs/_TEMPLATE/`.

O mapa interno SDD em `SPEC DRIVEN DEVELOPMENT/tasks.md` continua valido como visao agregada, e cada item `SPEC-XXX` ali pode apontar para uma pasta correspondente em `docs/specs/` quando essa pasta existir.
