# Auditoria: Campanhas, Midias, Dispositivos e Player

Data: 2026-05-20

## Resumo Executivo

O sistema esta em uma base funcional: campanhas conseguem selecionar midias e dispositivos, o player recebe playlist pelo backend, ha cache Redis para resposta rapida e existe canal SSE para atualizacoes em tempo real.

Depois das ultimas melhorias, o relacionamento entre campanha, midia e dispositivo ficou mais seguro. O backend agora valida IDs, evita referencias quebradas e invalida cache de forma mais direcionada. O player tambem ficou mais leve no caminho critico, especialmente em playlist, heartbeat e comandos.

Ainda assim, a arquitetura principal de relacionamento usa listas JSON em `campaigns.device_ids`, `campaigns.media_ids` e `campaigns.media_order`. Isso funciona para o momento atual, mas deve virar tabelas relacionais quando o volume crescer ou quando relatorios/conflitos/agendamentos ficarem mais importantes.

## Estado Atual por Modulo

## Campanhas

As campanhas hoje funcionam como o centro de distribuicao do conteudo. Elas guardam:

- dispositivos alvo;
- midias selecionadas;
- ordem das midias;
- status;
- prioridade;
- janela de data/horario;
- playlist de audio opcional;
- `config_version` para sinalizar mudancas ao player.

Pontos bons:

- Existe `config_version`, essencial para sincronizacao entre painel e player.
- Campanha ja suporta prioridade, status, agendamento e ordenacao de midias.
- Ao criar/atualizar campanha, dispositivos vinculados sao sincronizados com `current_campaign_id`.
- As referencias de dispositivos e midias agora sao validadas antes de salvar.
- Ao atualizar campanha, o cache dos players afetados e invalidado.

Pontos de atencao:

- `device_ids`, `media_ids` e `media_order` ainda sao JSON. Isso dificulta constraints reais no banco.
- Ainda nao existe tela forte de entrega por player: sincronizado, pendente, offline, erro.
- Conflitos de agenda/prioridade ainda nao parecem ser tratados como regra de produto completa.
- Publicar e salvar ainda estao proximos demais conceitualmente. O ideal e separar rascunho, revisao e publicacao.

Prioridade para campanha:

1. Painel "Dispositivos da campanha" com status de sincronizacao.
2. Botao "Forcar sincronizacao" para todos os players da campanha.
3. Preview real de como a campanha chega ao player.
4. Tabela relacional `campaign_devices`.
5. Tabela relacional `campaign_media` com ordem, duracao customizada e regras por item.

## Midias

As midias representam os arquivos ou URLs exibidos pelo player.

Pontos bons:

- Upload valida MIME/extensao.
- Midia possui tipo, status, duracao, categoria, tags e URL.
- Ao deletar midia, logs e relatorios associados sao limpos.
- Ao deletar midia, campanhas que usavam essa midia agora sao atualizadas.
- Cache dos dispositivos afetados e invalidado quando a midia removida altera campanhas.

Pontos de atencao:

- Ainda falta um ciclo completo de processamento: thumbnail, duracao real, resolucao real e validacao de arquivo em background.
- Status `processing` existe, mas ainda nao parece ter pipeline robusto.
- Nao ha controle forte de "midia usada por X campanhas" antes de deletar.
- Falta fallback visual/operacional quando midia falha no player.

Prioridade para midias:

1. Mostrar em quais campanhas cada midia esta sendo usada.
2. Antes de deletar, exibir impacto: campanhas e players afetados.
3. Criar processamento assincromo com Celery para extrair metadata.
4. Registrar erro de reproducao por midia vindo do player.
5. Criar regra de fallback: pular midia com erro e seguir playlist.

## Dispositivos

Os dispositivos representam os players/TVs que recebem campanhas.

Pontos bons:

- Pareamento por codigo e token de dispositivo ja existem.
- Dispositivo tem status, `last_seen_at`, versao do player, sistema operacional e campanha atual.
- Heartbeat do player atualiza dados operacionais.
- Comandos remotos existem: sync, refresh playlist, clear cache, restart, screenshot.
- Ao deletar dispositivo, ele agora e removido das campanhas que o referenciam.

Pontos de atencao:

- `current_campaign_id` e `campaign.device_ids` podem divergir se alguma rotina futura nao sincronizar corretamente.
- O status de sincronizacao ainda nao e uma entidade clara.
- Nao ha historico consolidado de versoes recebidas/executadas por dispositivo.
- Logs existem, mas falta transformar isso em visao operacional simples.

Prioridade para dispositivos:

1. Guardar versao de campanha atualmente recebida/executada.
2. Mostrar se o dispositivo esta na versao esperada da campanha.
3. Criar uma visao de saude: online, offline, atrasado, com erro, sem campanha.
4. Melhorar comandos em lote por campanha/local/grupo.
5. Criar historico de sessoes do player mais util para suporte.

## Player

O player e o consumidor final da campanha. Ele busca playlist, executa midias, envia heartbeat, registra playback e recebe atualizacoes/comandos.

Pontos bons:

- Player busca `/devices/{id}/playlist`.
- Ha cache Redis por `device_playlist:{device_id}`.
- Ha SSE para eventos de playlist/comandos.
- Heartbeat informa disponibilidade e compara `config_version`.
- Existe cache local no frontend/player para continuar em caso de falha.
- O endpoint de playlist foi otimizado para ser mais read-mostly.
- Heartbeat foi reduzido para um commit principal.
- Comandos pendentes agora sao marcados como enviados em lote.

Pontos de atencao:

- O player ainda precisa reportar melhor o estado atual: campanha em execucao, versao, midia atual e ultimo erro.
- O backend ainda monta playlist em tempo real quando o Redis expira.
- Ainda nao existe snapshot materializado completo por device.
- Faltam metricas de tempo de resposta por endpoint do player.

Prioridade para player:

1. Enviar no heartbeat:
   - `current_campaign_id`;
   - `current_config_version`;
   - `current_media_id`;
   - `current_media_name`;
   - `last_error`.
2. Criar status calculado por dispositivo:
   - sincronizado;
   - pendente;
   - offline;
   - erro;
   - sem campanha.
3. Criar endpoint ou painel de "entrega da campanha".
4. Criar snapshot/cache materializado por dispositivo.
5. Adicionar metricas e logs de performance nos endpoints do player.

## Redis

Redis esta sendo usado principalmente para:

- cache de playlist por dispositivo;
- pub/sub dos eventos SSE;
- backend de resultado do Celery.

Melhorias feitas:

- Cliente Redis reutilizavel por processo.
- Pool com limite de conexoes.
- Timeouts configurados.
- Invalidation por dispositivo afetado em campanhas, midias e playlists de audio.
- Docker Compose com limite de memoria e politica `allkeys-lru`.

Estado atual:

- Melhorou bastante para o caminho do player.
- Ainda existem fallbacks globais com `scan_iter`, mas agora eles ficam como caminho de seguranca, nao como regra principal.

Proximo passo ideal:

- Criar helpers centralizados de cache para evitar duplicacao entre campanhas, midias, audio e dispositivos.

## Celery

Celery existe para tarefas de manutencao e background.

Melhorias feitas:

- Removida do beat a tarefa que invalidava cache de todos os devices a cada 30 segundos.
- Resultados de task passam a ser ignorados por padrao.
- Resultado expira.
- Workers reciclam apos quantidade de tarefas.
- Broker tem pool limitado e retry no startup.
- Tarefa `recalculate_device_playlists` virou fallback/manual e so invalida cache divergente.

Estado atual:

- Mais leve e menos agressivo.
- Ainda falta separar filas por tipo de tarefa.

Proximo passo ideal:

- Criar filas:
  - `player` para acoes operacionais;
  - `media` para processamento de arquivos;
  - `reports` para relatorios;
  - `maintenance` para tarefas periodicas.

## Riscos Atuais

1. Relacionamentos em JSON
   - Funciona agora, mas escala mal para filtros, relatorios, integridade e conflitos.

2. Falta de painel de entrega
   - O operador ainda nao ve claramente se a campanha chegou e esta rodando.

3. Playlist montada sob demanda
   - Quando cache expira, backend monta playlist na hora. Em muitos players simultaneos pode pesar.

4. Pouco feedback do player
   - Sem reportar midia atual, versao executada e erro, o suporte fica cego.

5. Processamento de midia incompleto
   - Metadata real de arquivo deveria ser extraida fora da request de upload.

## O Que Esta Mais Importante Agora

O recurso mais importante a implementar agora e:

## Entrega da Campanha por Player

Na tela de campanha, mostrar cada dispositivo alvo com:

- nome;
- status online/offline;
- ultima conexao;
- campanha esperada;
- versao esperada;
- versao atual no player;
- midia atual;
- ultimo erro;
- status final: sincronizado, pendente, offline ou erro.

Isso fecha a principal lacuna operacional do sistema: saber se a campanha cadastrada realmente chegou aos players.

## Roadmap Recomendado

## Curto Prazo

1. Player enviar `current_config_version` e `current_media_id` no heartbeat.
2. Backend expor endpoint `GET /campaigns/{id}/delivery`.
3. Tela de campanha mostrar status dos dispositivos alvo.
4. Botao "Forcar sincronizacao" por campanha.
5. Alertar campanha sem midias validas.

## Medio Prazo

1. Criar `campaign_devices`.
2. Criar `campaign_media`.
3. Criar snapshot materializado por device.
4. Processar metadata de midias via Celery.
5. Melhorar conflitos de agenda e prioridade.

## Longo Prazo

1. Motor de regras de exibicao por local/grupo/tags.
2. Relatorios de execucao por campanha, midia e dispositivo.
3. Observabilidade do player: latencia, erros, downloads, cache local.
4. Deploy com filas Celery separadas e monitoramento.

## Conclusao

O sistema ja tem uma espinha dorsal boa. Campanhas, midias, dispositivos e player estao conectados e agora o backend esta mais consistente e mais leve.

O principal salto de qualidade nao e criar mais cadastro. E transformar campanha em uma tela operacional, mostrando entrega real nos players. Quando isso existir, o sistema deixa de ser apenas gerenciador de conteudo e vira uma plataforma confiavel de execucao em telas.
