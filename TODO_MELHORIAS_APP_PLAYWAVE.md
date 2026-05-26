# To Do List: Melhorias do App PlayWave

Data: 2026-05-20

Este documento organiza as melhorias prioritarias do PlayWave para midias, campanhas/playlists, player, radio indoor/audio, banco de dados, backend, frontend, regras de negocio e validacao final.

## 1. Modulo de Midias

## 1.1 Duracao automatica de videos

- [ ] Ao fazer upload de video, detectar automaticamente a duracao real do arquivo.
- [ ] Remover a necessidade de digitar manualmente o tempo do video.
- [ ] Salvar no banco o campo `duration_seconds`.
- [ ] No formulario de edicao da midia, mostrar a duracao como campo somente leitura.
- [ ] Para imagem, manter duracao manual padrao, exemplo: 15 segundos.
- [ ] Para video, o padrao deve ser tocar ate o fim do arquivo.
- [ ] Permitir sobrescrever a duracao somente se for necessario.
- [ ] Exemplo de sobrescrita: exibir apenas 30 segundos de um video de 60 segundos.

## 1.2 Periodo de exibicao da midia

- [ ] Adicionar data de inicio de exibicao na propria midia.
- [ ] Adicionar data de fim de exibicao na propria midia.
- [ ] Permitir midia sem data final, para ficar ativa por tempo indeterminado.
- [ ] O player deve ignorar midias fora do periodo configurado.
- [ ] A listagem de midias deve mostrar status calculado.

Status de midia:

- [ ] Ativa.
- [ ] Agendada.
- [ ] Expirada.
- [ ] Inativa.

## 1.3 Substituir midia sem perder agendamento

- [ ] Criar opcao "Substituir arquivo".
- [ ] Ao substituir o arquivo, manter o mesmo cadastro da midia.
- [ ] Nao remover a midia das campanhas/playlists existentes.
- [ ] Nao quebrar os agendamentos vinculados.
- [ ] Atualizar thumbnail do novo arquivo.
- [ ] Atualizar duracao do novo arquivo.
- [ ] Atualizar metadados do novo arquivo.
- [ ] Registrar historico de substituicao.

Historico de substituicao:

- [ ] Arquivo antigo.
- [ ] Arquivo novo.
- [ ] Data da troca.
- [ ] Usuario responsavel.

## 1.4 Organizacao da biblioteca de midias

- [ ] Melhorar filtros por tipo.
- [ ] Melhorar filtros por categoria.
- [ ] Melhorar filtros por tags.
- [ ] Exibir duracao real nas listagens.
- [ ] Exibir periodo de exibicao nas listagens.
- [ ] Exibir se a midia esta sendo usada em alguma campanha.
- [ ] Impedir exclusao direta de midia em uso ou exigir confirmacao forte.

Tipos de midia:

- [ ] Video.
- [ ] Imagem.
- [ ] Link.
- [ ] Audio.

## 2. Campanhas e Playlists

## 2.1 Nao adicionar midias apenas por checkbox

Problema atual: a tela seleciona midia por checkbox, mas isso limita o controle real da playlist.

- [ ] Criar fluxo separado para adicionar midia a campanha.
- [ ] Substituir checkbox simples por modelo de montagem de playlist.
- [ ] Criar botao "Adicionar midia a campanha".
- [ ] Abrir drawer/modal com biblioteca de midias.
- [ ] Permitir selecionar uma ou varias midias.
- [ ] Ao adicionar, midias entram como itens da playlist.
- [ ] Cada item da playlist deve ter configuracao propria.

## 2.2 Ordem das midias na campanha

- [ ] Permitir mudar a ordem das midias.
- [ ] Implementar drag and drop.
- [ ] Salvar posicao no banco usando `order_index` ou `position`.
- [ ] Player deve respeitar exatamente a ordem configurada.
- [ ] Adicionar botao mover para cima.
- [ ] Adicionar botao mover para baixo.
- [ ] Adicionar botao enviar para o inicio.
- [ ] Adicionar botao enviar para o fim.

## 2.3 Configuracoes por item da playlist

Cada midia dentro da campanha pode precisar de regra propria.

- [ ] Permitir definir duracao especifica por item da playlist.
- [ ] Permitir ativar/desativar uma midia dentro da campanha sem excluir da biblioteca.
- [ ] Permitir definir periodo de exibicao dentro da campanha.
- [ ] Permitir repetir uma midia mais de uma vez na mesma playlist.
- [ ] Permitir remover a midia apenas da campanha, sem apagar da biblioteca.

Cada item deve exibir:

- [ ] Nome da midia.
- [ ] Tipo.
- [ ] Duracao.
- [ ] Status.
- [ ] Ordem.
- [ ] Periodo de exibicao.

## 2.4 Regras da campanha

- [ ] Campanha deve ter data de inicio.
- [ ] Campanha deve ter data de fim opcional.
- [ ] Campanha deve permitir vincular uma TV especifica.
- [ ] Campanha deve permitir vincular grupo de TVs.
- [ ] Campanha deve permitir vincular localizacao.
- [ ] Campanha deve permitir vincular ponto/radio.
- [ ] Player deve receber apenas campanhas validas para aquele dispositivo.

Status de campanha:

- [ ] Rascunho.
- [ ] Ativa.
- [ ] Pausada.
- [ ] Expirada.

## 3. Player e Reproducao

## 3.1 Respeitar duracao real das midias

- [ ] Video deve tocar ate o fim automaticamente.
- [ ] Imagem deve usar duracao configurada.
- [ ] Link/webview deve usar duracao configurada.
- [ ] Se video tiver duracao detectada, nao exigir preenchimento manual.
- [ ] Se houver duracao manual menor que o video, cortar no tempo configurado.
- [ ] Se houver duracao manual maior que o video, definir regra do produto.

Regra pendente para video com duracao manual maior que arquivo:

- [ ] Opcao A: repetir video ate completar o tempo.
- [ ] Opcao B: avancar ao final do video.

## 3.2 Fila de reproducao

- [ ] Criar fila real de reproducao no player.
- [ ] Montar fila com base na campanha ativa.
- [ ] Quando acabar a fila, reiniciar do comeco.
- [ ] Registrar logs de reproducao.

Fila deve respeitar:

- [ ] Ordem da playlist.
- [ ] Periodo de exibicao.
- [ ] Status da midia.
- [ ] Status da campanha.
- [ ] Regras do dispositivo.

Logs de reproducao:

- [ ] Midia exibida.
- [ ] Campanha.
- [ ] Dispositivo.
- [ ] Horario de inicio.
- [ ] Horario de fim.
- [ ] Erro, se houver.

## 3.3 Cache e substituicao de midia

- [ ] Quando uma midia for substituida, player deve baixar o novo arquivo.
- [ ] Invalidar cache antigo.
- [ ] Manter o mesmo item na campanha.
- [ ] Evitar tela preta durante atualizacao.
- [ ] Fazer troca segura apos terminar a midia atual.

## 4. Radio Indoor e Audio

## 4.1 Upload multiplo de musicas

- [ ] Permitir selecionar varias musicas do PC de uma vez.
- [ ] Fazer upload em lote.
- [ ] Mostrar progresso de upload por arquivo.
- [ ] Detectar duracao automatica de cada audio.
- [ ] Permitir tags para musicas.
- [ ] Permitir categorias para musicas.

Formatos aceitos:

- [ ] MP3.
- [ ] WAV.
- [ ] AAC.
- [ ] OGG, se o player suportar.

## 4.2 Selecionar varios audios para uma radio/ponto

- [ ] Permitir selecao multipla de musicas.
- [ ] Nao limitar selecao a um audio individual.
- [ ] Criar vinculo entre radio/ponto e playlist de audio.
- [ ] Permitir radio diferente por TV.
- [ ] Permitir radio diferente por grupo de TVs.
- [ ] Permitir radio diferente por ponto/localizacao.
- [ ] Permitir radio diferente por unidade.

## 4.3 Pastas ou playlists de musicas

- [ ] Criar opcao de "Pasta de musicas" ou "Playlist de audio".
- [ ] Permitir separar musicas por periodo ou finalidade.

Separacoes sugeridas:

- [ ] Manha.
- [ ] Tarde.
- [ ] Noite.
- [ ] Promocao.
- [ ] Ambiente.
- [ ] Campanha especial.

Cada pasta/playlist deve ter:

- [ ] Nome.
- [ ] Descricao.
- [ ] Data de inicio.
- [ ] Data de fim.
- [ ] Status ativo/inativo.
- [ ] Modo de reproducao.

## 4.4 Sequencial ou aleatorio

- [ ] Adicionar opcao "Tocar em sequencia".
- [ ] Adicionar opcao "Tocar embaralhado".
- [ ] Salvar modo no banco como `sequential` ou `shuffle`.
- [ ] Player deve respeitar esse modo.
- [ ] Evitar repetir a mesma musica muitas vezes no modo aleatorio.

## 4.5 Spots de audio

Spot e o audio promocional que toca a cada X minutos, independente da playlist principal.

- [ ] Criar cadastro de spots.
- [ ] Permitir escolher um ou varios audios como spot.
- [ ] Permitir configurar "tocar a cada X minutos".
- [ ] Permitir configurar horario de inicio e fim do spot.
- [ ] Permitir configurar data de inicio e fim.
- [ ] Permitir definir prioridade.
- [ ] Permitir escolher em quais radios/pontos o spot toca.
- [ ] Player deve interromper ou encaixar o spot entre musicas, conforme regra definida.
- [ ] Registrar logs de execucao dos spots.

## 5. Banco de Dados

## 5.1 Ajustar tabela `media`

Adicionar campos:

- [ ] `duration_seconds`.
- [ ] `display_duration_seconds`.
- [ ] `start_date`.
- [ ] `end_date`.
- [ ] `status`.
- [ ] `file_hash`.
- [ ] `thumbnail_url`.
- [ ] `metadata`.
- [ ] `created_at`.
- [ ] `updated_at`.
- [ ] `created_by`.
- [ ] `updated_by`.

## 5.2 Criar tabela `campaign_playlist_items`

Essa tabela evita depender apenas de checkbox ou listas JSON.

Campos:

- [ ] `id`.
- [ ] `campaign_id`.
- [ ] `media_id`.
- [ ] `order_index`.
- [ ] `display_duration_seconds`.
- [ ] `start_date`.
- [ ] `end_date`.
- [ ] `is_active`.
- [ ] `created_at`.
- [ ] `updated_at`.

## 5.3 Criar versionamento de midia

Tabela sugerida: `media_versions`.

Campos:

- [ ] `id`.
- [ ] `media_id`.
- [ ] `file_url`.
- [ ] `file_name`.
- [ ] `file_size`.
- [ ] `duration_seconds`.
- [ ] `thumbnail_url`.
- [ ] `created_at`.
- [ ] `created_by`.
- [ ] `is_current`.

Objetivo:

- [ ] Substituir arquivo sem quebrar campanhas.
- [ ] Preservar historico de versoes.
- [ ] Permitir auditoria de troca de arquivo.

## 5.4 Criar estrutura para radio

Tabelas sugeridas:

- [ ] `audio_tracks`.
- [ ] `audio_playlists`.
- [ ] `audio_playlist_items`.
- [ ] `radio_points`.
- [ ] `radio_point_playlists`.
- [ ] `audio_spots`.
- [ ] `audio_spot_schedules`.

## 6. Backend e API

## 6.1 Endpoints de midia

- [ ] `POST /media/upload`.
- [ ] `POST /media/bulk-upload`.
- [ ] `GET /media`.
- [ ] `GET /media/{id}`.
- [ ] `PATCH /media/{id}`.
- [ ] `POST /media/{id}/replace-file`.
- [ ] `DELETE /media/{id}`.
- [ ] `GET /media/{id}/usage`.

## 6.2 Endpoints de campanha/playlist

- [ ] `POST /campaigns`.
- [ ] `GET /campaigns`.
- [ ] `GET /campaigns/{id}`.
- [ ] `PATCH /campaigns/{id}`.
- [ ] `DELETE /campaigns/{id}`.
- [ ] `POST /campaigns/{id}/items`.
- [ ] `PATCH /campaigns/{id}/items/{item_id}`.
- [ ] `DELETE /campaigns/{id}/items/{item_id}`.
- [ ] `PATCH /campaigns/{id}/items/reorder`.

## 6.3 Endpoints de radio

- [ ] `POST /audio/upload`.
- [ ] `POST /audio/bulk-upload`.
- [ ] `GET /audio/tracks`.
- [ ] `POST /audio/playlists`.
- [ ] `GET /audio/playlists`.
- [ ] `POST /audio/playlists/{id}/items`.
- [ ] `PATCH /audio/playlists/{id}/items/reorder`.
- [ ] `POST /radio-points`.
- [ ] `POST /radio-points/{id}/playlists`.
- [ ] `POST /audio-spots`.
- [ ] `GET /audio-spots`.
- [ ] `PATCH /audio-spots/{id}`.

## 6.4 Endpoint de sincronizacao do player

Ajustar endpoint de sync para retornar:

- [ ] Campanhas ativas.
- [ ] Midias validas.
- [ ] Ordem da playlist.
- [ ] Duracao real.
- [ ] Duracao customizada.
- [ ] Periodo de exibicao.
- [ ] Playlist de audio.
- [ ] Spots.
- [ ] Modo sequencial/aleatorio.
- [ ] Versao dos arquivos.

Regras:

- [ ] Player deve validar se ha atualizacao antes de baixar tudo novamente.
- [ ] Player nao deve baixar arquivos ja cacheados e atuais.
- [ ] Player deve baixar arquivo novo quando `file_hash` ou versao mudar.

## 7. Frontend e Telas

## 7.1 Tela de edicao da midia

- [ ] Corrigir campo "Duracao".
- [ ] Para video, mostrar "Detectado automaticamente: 60s".
- [ ] Para imagem, permitir editar duracao.
- [ ] Adicionar campo Data inicio.
- [ ] Adicionar campo Data fim.
- [ ] Adicionar botao Substituir arquivo.
- [ ] Adicionar campo Status.
- [ ] Mostrar aviso quando a midia estiver em campanhas ativas.

## 7.2 Tela de edicao da campanha

- [ ] Trocar selecao por checkbox por construtor de playlist.
- [ ] Adicionar botao "Adicionar midia".
- [ ] Adicionar drag and drop.
- [ ] Exibir ordem numerica.
- [ ] Permitir remover midia da campanha.
- [ ] Permitir editar configuracoes da midia dentro da campanha.
- [ ] Mostrar duracao total estimada da playlist.
- [ ] Mostrar alertas de midia expirada.
- [ ] Mostrar alertas de midia indisponivel.

## 7.3 Tela de radio

- [ ] Criar tela de musicas.
- [ ] Criar tela de playlists de audio.
- [ ] Criar tela de pontos/radios.
- [ ] Criar tela de spots.
- [ ] Criar upload multiplo.
- [ ] Criar selecao multipla de audios.
- [ ] Criar configuracao de sequencia/aleatorio.
- [ ] Criar configuracao por periodo.

Periodos sugeridos:

- [ ] Manha.
- [ ] Tarde.
- [ ] Noite.
- [ ] Datas especificas.

## 8. Regras de Negocio

## 8.1 Midia

- [ ] Midia expirada nao deve tocar.
- [ ] Midia inativa nao deve tocar.
- [ ] Midia sem arquivo valido nao deve tocar.
- [ ] Midia substituida deve manter vinculo com campanhas.
- [ ] Video deve usar duracao real por padrao.
- [ ] Imagem precisa de duracao configurada.

## 8.2 Campanha

- [ ] Campanha pausada nao toca.
- [ ] Campanha fora do periodo nao toca.
- [ ] Campanha sem midia valida nao deve ser enviada ao player.
- [ ] Player deve respeitar a ordem configurada.
- [ ] Alteracoes na campanha devem gerar nova versao de sincronizacao.

## 8.3 Radio

- [ ] Radio sem playlist nao toca.
- [ ] Playlist fora do periodo nao toca.
- [ ] Spot deve respeitar intervalo configurado.
- [ ] Spot nao deve tocar sobre outro spot.
- [ ] Modo aleatorio nao deve repetir sempre a mesma musica.
- [ ] Modo sequencial deve continuar de onde parou, se possivel.

## 9. Prioridade de Implementacao

## 9.1 Prioridade Alta

- [ ] Detectar duracao automatica de videos.
- [ ] Adicionar periodo de exibicao na midia.
- [ ] Criar substituicao de arquivo sem quebrar campanha.
- [ ] Trocar checkbox da campanha por playlist real.
- [ ] Permitir ordenar midias na campanha.
- [ ] Player respeitar ordem, duracao e validade das midias.

## 9.2 Prioridade Media

- [ ] Upload multiplo de musicas.
- [ ] Criar playlists de audio.
- [ ] Selecionar multiplos audios por radio/ponto.
- [ ] Criar modo sequencial/aleatorio.
- [ ] Criar logs de reproducao mais completos.

## 9.3 Prioridade Baixa

- [ ] Pastas inteligentes por manha/tarde/noite.
- [ ] Spots com prioridade.
- [ ] Historico avancado de substituicoes.
- [ ] Relatorios por midia, campanha, radio e ponto.

## 10. Checklist Final de Validacao

Antes de considerar pronto:

- [ ] Subi um video e o sistema detectou a duracao sozinho.
- [ ] Subi uma imagem e consegui definir duracao manual.
- [ ] Configurei data de inicio e fim em uma midia.
- [ ] Midia expirada nao tocou no player.
- [ ] Substitui uma midia e ela continuou na campanha.
- [ ] Criei uma campanha adicionando midias por playlist, nao apenas checkbox.
- [ ] Mudei a ordem das midias e o player respeitou.
- [ ] Subi varias musicas ao mesmo tempo.
- [ ] Criei uma playlist de audio.
- [ ] Vinculei a playlist de audio a uma radio/ponto.
- [ ] Configurei musicas em sequencia.
- [ ] Configurei musicas embaralhadas.
- [ ] Configurei spot para tocar a cada X minutos.
- [ ] Player sincronizou tudo sem precisar recarregar manualmente.
- [ ] Logs registraram midia, campanha, audio, spot e dispositivo.

## 11. Observacoes Tecnicas

- As mudancas de campanha devem migrar gradualmente de `campaign.media_ids` e `campaign.media_order` para `campaign_playlist_items`.
- O endpoint atual de playlist do player deve continuar funcionando durante a migracao.
- A primeira etapa deve preservar compatibilidade com os players existentes.
- Extracao de duracao, thumbnail e metadata deve ser feita em background com Celery.
- Substituicao de arquivo deve gerar nova versao de midia e invalidar cache por `file_hash`.
- O player deve trocar arquivo de forma segura, apos terminar a midia atual.
