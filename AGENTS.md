# AGENTS.md — PlayWave

## Contexto do Projeto

Este projeto é o **PlayWave**, uma plataforma de gerenciamento de campanhas, mídias, playlists sonoras, rádio indoor e players de exibição.

O sistema possui:

- Painel gerenciador web.
- Backend em FastAPI.
- Player web de exibição.
- Módulo de Rádio Indoor.
- Módulo de Campanhas.
- Módulo de Mídias.
- Módulo de Dispositivos.
- Controle de playlists, spots, pastas de áudio e programação.

O objetivo principal desta fase é corrigir bugs críticos do player e evoluir a arquitetura de rádio/campanhas para que o sistema seja confiável em produção.

---

# Regra Principal

Não resolver apenas com ajustes visuais ou gambiarras de frontend.

A solução correta deve respeitar esta base:

```text
Banco bem relacionado
+ Backend resolvendo agenda corretamente
+ Player com fila própria e watchdog
+ Sincronização por versão/WebSocket/polling
+ Logs de debug por dispositivo
```

Sempre que houver dúvida entre fazer um atalho ou corrigir a arquitetura, corrigir a arquitetura.

---

# Problemas Críticos Conhecidos

## Rádio

- Upload de músicas precisa aceitar múltiplos arquivos.
- Cliente precisa criar categorias personalizadas de áudio.
- Cliente precisa criar pastas de áudio, exemplo: manhã, tarde, noite.
- Pastas precisam ter horário de início e fim.
- Pastas podem ter data de início e fim.
- Playlists precisam tocar em sequência ou embaralhado.
- Spots precisam tocar a cada X minutos.
- Spots não podem substituir a playlist principal.
- Spot programado atualmente pode não tocar.
- Quando há spot, o sistema pode tocar só spot e parar playlist.
- Rádio pode tocar música fora da playlist.
- Rádio pode tocar apenas uma música.
- Rádio pode pausar quando a aba fica em segundo plano.
- Áudio pode ficar sem som até iniciar outra música.

## Campanhas / Playlists

- Campanhas podem não passar no player.
- Campanhas não reconhecem pastas da playlist sonora.
- Rota `/radio/playlists` precisa reconhecer pasta como item válido.
- Mídias precisam ser adicionadas individualmente, não apenas por checkbox genérico.
- Mídias precisam ter ordem customizável.
- Player não deve reiniciar inteiro ao alterar algo no gerenciador.

## Mídia

- Duração de vídeos/áudios deve ser detectada automaticamente.
- Mídia precisa ter período de exibição.
- Usuário precisa substituir o arquivo da mídia sem perder agendamento.
- Áudio da mídia não pode misturar indevidamente com rádio.

## Player / Dispositivos

- Player não recebe comandos de desligar/reiniciar.
- Ao alterar código de pareamento, player antigo continua funcionando.
- Player precisa invalidar sessão antiga quando pareamento muda.
- Player precisa receber atualização sem limpar cache manualmente.
- Player precisa mostrar nome da música atual no canto da tela, se habilitado.
- Controle de mídia do navegador/Windows não pode quebrar o player.

---

# Prioridades

## P0 — Corrigir operação quebrada

Tratar primeiro:

1. Corrigir relacionamento de playlists com pastas.
2. Corrigir campanhas que não passam no player.
3. Corrigir player não recebendo comandos.
4. Corrigir alteração de código de pareamento sem invalidar sessão.
5. Corrigir player reiniciando ao mexer no gerenciador.
6. Corrigir rádio pausando em segundo plano.
7. Corrigir música fora da playlist.
8. Corrigir rádio tocando apenas uma música.
9. Corrigir áudio travado/sem som.
10. Criar versionamento de programação.

## P1 — Consolidar produto

1. Upload múltiplo de áudio.
2. Categorias personalizadas.
3. Pastas de áudio.
4. Agendamento de pastas.
5. Spots a cada X minutos.
6. Sequencial/aleatório.
7. Reordenação de mídias.
8. Substituição de mídia sem perder agendamento.
9. Detecção automática de duração.

## P2 — Acabamento

1. Overlay com nome da música.
2. Melhorias de UX em modais.
3. Revisão da tela Agenda.
4. Controle de mídia do navegador/Windows.
5. Relatórios e painel de debug avançado.

---

# Arquitetura Esperada

## Backend

Stack principal:

- FastAPI.
- SQLAlchemy ou ORM equivalente.
- Alembic para migrations.
- Banco relacional.
- Worker assíncrono para processamento de mídia.
- FFmpeg/ffprobe para duração de áudio/vídeo.
- WebSocket ou polling confiável para comunicação player/backend.

O backend deve ser a fonte da verdade da programação.

O player não deve decidir sozinho quais campanhas, pastas ou spots são válidos sem receber dados claros do backend.

---

# Regra de Programação Resolvida

Sempre que o player consultar a programação, o backend deve conseguir informar:

```json
{
  "device_id": "...",
  "schedule_version": 42,
  "active_campaigns": [],
  "active_radio_playlist": {},
  "active_audio_folder": {},
  "current_track": {},
  "next_track": {},
  "pending_spot": {},
  "ignored_items": [
    {
      "item_id": "...",
      "reason": "outside_schedule"
    }
  ]
}
```

O backend deve explicar por que um item foi incluído ou ignorado.

Motivos comuns:

```text
outside_date_range
outside_time_range
inactive
missing_media_file
not_linked_to_device
invalid_folder
empty_playlist
expired_campaign
lower_priority
```

---

# Banco de Dados

## Categorias de Áudio

Criar tabela para categorias personalizadas.

```sql
audio_categories
- id
- tenant_id
- name
- slug
- is_default
- created_at
- updated_at
```

Regras:

- Categorias padrão continuam existindo.
- Cliente pode criar categorias próprias.
- Não permitir nome duplicado por tenant.
- Categoria deve aparecer em filtros, upload e organização.

---

## Pastas de Áudio

Criar estrutura para pastas.

```sql
audio_folders
- id
- tenant_id
- name
- description
- category_id
- is_active
- start_date
- end_date
- start_time
- end_time
- playback_mode
- created_at
- updated_at
```

Relacionamento entre pasta e faixas:

```sql
audio_folder_tracks
- id
- folder_id
- audio_track_id
- position
- created_at
```

Regras:

- Uma pasta pode conter várias músicas.
- Uma música pode estar em mais de uma pasta.
- Pasta pode ser programada por data e horário.
- Pasta pode tocar sequencial ou embaralhada.
- Pasta inativa nunca deve tocar.

---

## Itens da Playlist Sonora

A playlist sonora deve aceitar tanto música individual quanto pasta.

```sql
radio_playlist_items
- id
- playlist_id
- item_type -- 'track' ou 'folder'
- audio_track_id -- nullable
- audio_folder_id -- nullable
- position
- priority
- start_time
- end_time
- start_date
- end_date
- playback_mode
- is_active
- created_at
- updated_at
```

Regras:

- Se `item_type = track`, `audio_track_id` deve existir.
- Se `item_type = folder`, `audio_folder_id` deve existir.
- O player deve receber a estrutura resolvida ou uma estrutura clara para montar a fila.
- Pastas devem ter prioridade correta sobre itens individuais quando configurado.

---

## Spots

Criar ou revisar estrutura de spots.

```sql
radio_spots
- id
- tenant_id
- playlist_id
- audio_track_id
- name
- interval_minutes
- insertion_policy -- 'wait_current_track' ou 'interrupt'
- start_time
- end_time
- start_date
- end_date
- is_active
- priority
- created_at
- updated_at
```

Regras:

- Spot é inserção temporária.
- Spot não substitui a playlist principal.
- Spot deve tocar no intervalo configurado.
- Depois do spot, a rádio volta para a fila principal.
- Se `insertion_policy = wait_current_track`, aguardar a música atual terminar.
- Se `insertion_policy = interrupt`, interromper conforme regra explícita.

---

## Campanhas e Mídias

Itens de campanha devem ter relacionamento próprio.

```sql
campaign_media_items
- id
- campaign_id
- media_id
- position
- priority
- start_date
- end_date
- start_time
- end_time
- created_at
- updated_at
```

Regras:

- Player respeita `position`.
- Player respeita `priority`.
- Player respeita validade por data e horário.
- Alterar ordem não pode remover agendamento.
- Substituir arquivo da mídia não pode quebrar campanhas.

---

## Versões de Arquivo de Mídia

Para substituir arquivo sem perder agendamento:

```sql
media_assets
- id
- media_id
- file_url
- duration
- mime_type
- version
- is_current
- created_at
```

Regras:

- `media_id` permanece o mesmo.
- Novo arquivo cria nova versão.
- Campanhas continuam apontando para a mesma mídia lógica.
- Player deve usar apenas `is_current = true`.

---

## Comandos de Dispositivo

Criar fila confiável de comandos.

```sql
device_commands
- id
- device_id
- command_type
- payload
- status -- pending, delivered, executed, failed, expired
- created_at
- delivered_at
- executed_at
- error_message
```

Comandos mínimos:

```text
shutdown
restart
reload_schedule
clear_cache
pause
resume
invalidate_pairing
```

Regras:

- Gerenciador cria comando.
- Player recebe comando via WebSocket ou polling.
- Player confirma recebimento.
- Player confirma execução.
- Se offline, comando fica pendente ou expira.
- Gerenciador mostra status real do comando.

---

## Pareamento

Alterar código de pareamento deve invalidar sessões antigas.

Modelo sugerido:

```text
device.pairing_version
device_session.pairing_version
```

Regra:

- Quando código de pareamento mudar, incrementar `device.pairing_version`.
- Toda sessão antiga com versão diferente deve ser rejeitada.
- Player antigo deve voltar para tela de pareamento.
- Backend deve bloquear requests com sessão inválida.

---

# Versionamento da Programação

Criar versionamento para evitar cache velho.

Campos sugeridos:

```text
schedule_version
radio_playlist_version
campaign_version
content_hash
```

Regras:

- Toda alteração relevante incrementa a versão.
- Player compara versão local com versão do servidor.
- Se versão mudou, player atualiza a programação.
- Não deve ser necessário limpar cache manualmente.
- Não deve ser necessário reiniciar o sistema para player reconhecer alteração.

Eventos que devem incrementar versão:

```text
playlist criada/editada
pasta criada/editada
música adicionada/removida
spot criado/editado
campanha criada/editada
mídia substituída
horário/data alterado
dispositivo vinculado/desvinculado
```

---

# Comunicação Player x Backend

Preferência:

1. WebSocket.
2. Polling como fallback.

Eventos esperados:

```text
schedule.updated
playlist.updated
radio.folder.updated
radio.spot.updated
campaign.updated
media.replaced
device.command
pairing.invalidated
player.reload_required
```

Se WebSocket cair, o player deve usar polling:

```http
GET /api/v1/player/sync
```

Resposta mínima:

```json
{
  "device_id": "...",
  "server_time": "...",
  "schedule_version": 42,
  "commands": [],
  "requires_schedule_reload": true
}
```

---

# Player

## Regras Obrigatórias

O player:

- Não deve depender de refresh da página para atualizar programação.
- Não deve depender de cache antigo.
- Não deve reiniciar inteiro em qualquer alteração do gerenciador.
- Não deve tocar música fora da playlist ativa.
- Não deve tocar dois áudios principais ao mesmo tempo.
- Deve manter uma fila principal de rádio.
- Deve manter fila separada de spots.
- Deve ter watchdog para detectar áudio travado.
- Deve conseguir recuperar áudio pausado/travado.
- Deve limpar fila local quando `schedule_version` mudar.
- Deve confirmar comandos recebidos.

---

## Fila de Rádio

Separar:

```text
mainQueue = músicas/pastas da playlist
spotQueue = inserções comerciais/jingles
visualQueue = campanhas visuais
```

Regras:

- `mainQueue` é a trilha principal.
- `spotQueue` entra apenas quando devido.
- Depois do spot, voltar para `mainQueue`.
- `visualQueue` não deve bagunçar áudio da rádio.
- Se campanha visual tiver áudio próprio, aplicar regra de prioridade sonora.

---

## Regra de Áudio

Usar esta prioridade:

```text
1. Campanha visual com áudio próprio
2. Spot
3. Rádio ambiente
4. Silêncio
```

Regras:

- Vídeo com áudio próprio deve pausar ou reduzir rádio.
- Imagem sem áudio pode manter rádio.
- Spot não toca junto com outro spot.
- Rádio não deve sobrepor áudio de mídia.
- Player deve saber qual fonte de áudio está ativa.

---

## Watchdog de Áudio

Implementar verificação periódica.

A cada 5 segundos:

```text
- verificar se deveria estar tocando
- verificar se audio.paused está incorreto
- verificar se currentTime avançou
- verificar se volume/mute estão corretos
- verificar stalled/error/waiting
- tentar recuperar
- se não recuperar, pular para próxima faixa
```

Eventos do navegador que devem ser tratados:

```text
play
pause
ended
error
stalled
waiting
canplay
visibilitychange
timeupdate
```

O player não pode parar apenas porque a aba está em segundo plano.

---

# Frontend

## Upload Múltiplo

Tela de Faixas de Áudio deve permitir:

- Selecionar vários arquivos.
- Arrastar e soltar arquivos.
- Remover arquivo antes do upload.
- Definir categoria padrão.
- Definir status padrão.
- Exibir progresso por arquivo.
- Exibir relatório final.

Relatório final:

```text
enviados
falharam
duplicados
inválidos
```

---

## Categorias

O frontend deve permitir:

- Criar categoria personalizada.
- Editar categoria.
- Filtrar por categoria.
- Usar categoria no upload.
- Usar categoria em pastas.
- Usar categoria em playlists.

---

## Pastas de Áudio

O frontend deve permitir:

- Criar pasta.
- Editar pasta.
- Adicionar múltiplas músicas.
- Remover músicas.
- Reordenar músicas.
- Definir data inicial/final.
- Definir horário inicial/final.
- Definir modo sequencial/aleatório.
- Ativar/inativar pasta.

---

## Playlist Sonora

O frontend deve permitir:

- Adicionar músicas individuais.
- Adicionar pastas.
- Misturar músicas e pastas.
- Filtrar por categoria.
- Reordenar itens.
- Definir prioridade.
- Definir horário por item.
- Definir data por item.
- Exibir duração total estimada.
- Salvar ordem de reprodução.

---

## Spots

O frontend deve permitir:

- Criar spot.
- Escolher áudio do spot.
- Definir intervalo em minutos.
- Definir se aguarda a música terminar ou interrompe.
- Definir data inicial/final.
- Definir horário inicial/final.
- Ativar/inativar.
- Exibir próximo horário estimado do spot.

---

## Campanhas

O frontend deve permitir:

- Adicionar mídia individualmente.
- Reordenar mídia por drag-and-drop.
- Definir período por mídia.
- Definir prioridade por mídia.
- Remover mídia sem excluir arquivo original.
- Substituir arquivo de mídia sem perder campanha.

---

## Dispositivos

O frontend deve permitir:

- Enviar comando de desligar.
- Enviar comando de reiniciar.
- Enviar comando de recarregar programação.
- Enviar comando de limpar cache.
- Ver status do comando.
- Ver se player está online/offline.
- Ver última sincronização.
- Ver versão da programação.

---

# Endpoint de Debug

Criar endpoint:

```http
GET /api/v1/devices/{device_id}/debug-playback
```

Resposta esperada:

```json
{
  "device_id": "...",
  "online": true,
  "last_seen_at": "...",
  "schedule_version": 42,
  "radio_playlist": {
    "id": "...",
    "name": "...",
    "version": 18
  },
  "active_folder": {
    "id": "...",
    "name": "Manhã"
  },
  "current_track": {
    "id": "...",
    "name": "Bridge to You"
  },
  "next_track": {
    "id": "...",
    "name": "Amber Glow"
  },
  "pending_spot": null,
  "active_campaigns": [],
  "ignored_items": [
    {
      "type": "folder",
      "id": "...",
      "reason": "outside_time_range"
    }
  ],
  "last_command": {
    "type": "reload_schedule",
    "status": "executed"
  },
  "last_player_error": null
}
```

Este endpoint é obrigatório para diagnosticar bugs sem acessar banco diretamente.

---

# Logs Obrigatórios

Usar logs estruturados.

Eventos mínimos:

```text
radio.playlist.loaded
radio.folder.resolved
radio.folder.ignored
radio.track.started
radio.track.ended
radio.track.failed
radio.spot.due
radio.spot.started
radio.spot.finished
player.schedule.updated
player.schedule.version_changed
player.command.received
player.command.executed
player.audio.watchdog_recovered
player.audio.watchdog_failed
campaign.media.selected
campaign.media.ignored
device.pairing.invalidated
```

Cada log deve ter, quando aplicável:

```text
tenant_id
device_id
playlist_id
folder_id
track_id
campaign_id
media_id
schedule_version
reason
```

---

# Campo Prioridade

Regra oficial:

```text
Maior número = maior prioridade.
```

Explicação:

Prioridade define qual conteúdo tem preferência quando há mais de um item válido no mesmo horário.

Exemplo:

```text
Prioridade 10 = mais importante
Prioridade 5 = média
Prioridade 1 = menor importância
```

Regras:

- Prioridade não substitui agendamento.
- Prioridade só desempata conteúdos válidos.
- Em empate, usar `position`.
- Frontend deve ter tooltip explicando o campo.

Tooltip sugerido:

```text
Prioridade define qual conteúdo tem preferência quando há mais de um item disponível no mesmo horário. Quanto maior o número, maior a prioridade.
```

---

# Regras de Implementação

## Antes de alterar código

1. Entender a regra de negócio.
2. Identificar se a falha está no banco, backend, frontend ou player.
3. Não corrigir no player algo que deveria ser resolvido no backend.
4. Não corrigir no frontend algo que deveria ter validação no backend.
5. Verificar impacto em campanhas, rádio, spots e dispositivos.

---

## Ao alterar banco

Sempre:

- Criar migration.
- Preservar dados existentes.
- Criar valores padrão quando necessário.
- Evitar quebrar playlists/campanhas já cadastradas.
- Fazer script de backfill se necessário.
- Garantir índices em campos usados por agenda e filtros.

Campos que geralmente precisam de índice:

```text
tenant_id
device_id
playlist_id
campaign_id
is_active
start_date
end_date
start_time
end_time
schedule_version
```

---

## Ao alterar API

Sempre:

- Manter compatibilidade quando possível.
- Criar schema claro de request/response.
- Validar permissões por tenant.
- Retornar erros explícitos.
- Não retornar item inválido silenciosamente.
- Incluir motivo de item ignorado em endpoints de debug.

---

## Ao alterar player

Sempre:

- Evitar reload completo desnecessário.
- Preservar estado de reprodução quando possível.
- Limpar cache apenas quando versão mudar.
- Separar rádio, spot e campanha.
- Adicionar logs para qualquer decisão automática.
- Tratar falha de áudio e fallback.

---

## Ao alterar frontend

Sempre:

- Priorizar clareza operacional.
- Mostrar status real.
- Evitar telas que escondem regra importante.
- Mostrar mensagens úteis de erro.
- Não permitir salvar configuração ambígua.
- Confirmar ações destrutivas.

---

# Testes Obrigatórios

## Rádio

Testar:

- Playlist com músicas individuais.
- Playlist apenas com pasta.
- Playlist com música + pasta.
- Pasta fora do horário.
- Pasta dentro do horário.
- Pasta expirada.
- Pasta futura.
- Modo sequencial.
- Modo aleatório.
- Spot a cada X minutos.
- Spot aguardando música terminar.
- Spot interrompendo.
- Retorno correto para playlist após spot.

---

## Player

Testar:

- Atualização de playlist sem refresh.
- Alteração de pasta sem limpar cache.
- Alteração de campanha sem reiniciar player.
- Aba em segundo plano.
- Áudio travado.
- Áudio com erro.
- Próxima música após erro.
- Comando desligar.
- Comando reiniciar.
- Comando limpar cache.
- Código de pareamento alterado.

---

## Campanhas

Testar:

- Campanha ativa.
- Campanha inativa.
- Campanha fora do horário.
- Campanha fora da data.
- Campanha sem mídia válida.
- Campanha com mídia reordenada.
- Campanha com mídia substituída.
- Campanha vinculada ao dispositivo correto.
- Campanha não vinculada ao dispositivo.

---

## Mídia

Testar:

- Upload de vídeo.
- Upload de áudio.
- Extração automática de duração.
- Falha na extração de duração.
- Substituição de arquivo.
- Manutenção de agendamento após substituição.
- Validade por data.
- Validade por horário.

---

# Definition of Done

Uma task só está concluída quando:

- Implementação está funcionando.
- Migration foi criada, se houve alteração de banco.
- API está validando corretamente.
- Frontend mostra estado correto.
- Player respeita a regra.
- Logs foram adicionados.
- Endpoint de debug ajuda a diagnosticar.
- Testes manuais principais foram executados.
- Não exige limpar cache manualmente.
- Não exige reiniciar player manualmente, exceto quando o comando for explicitamente de reinício.
- Não quebra campanhas, playlists ou mídias já existentes.

---

# O que Não Fazer

Não fazer:

- Não hardcodar IDs.
- Não resolver com `setTimeout` aleatório sem lógica de estado.
- Não fazer player dar reload em toda alteração.
- Não deixar player tocar cache antigo sem comparar versão.
- Não misturar spot com playlist principal.
- Não tocar dois áudios principais ao mesmo tempo.
- Não ignorar item sem registrar motivo.
- Não criar regra duplicada entre Agenda e Campanha.
- Não apagar agendamentos ao substituir mídia.
- Não invalidar dados antigos sem migration segura.

---

# Ordem Recomendada de Execução

## Sprint 1

1. Criar/revisar `radio_playlist_items`.
2. Corrigir `/radio/playlists` para reconhecer pastas.
3. Criar programação resolvida para player.
4. Criar `schedule_version`.
5. Corrigir cache do player.
6. Corrigir avanço da fila da rádio.
7. Corrigir comandos de dispositivo.
8. Corrigir pareamento.
9. Criar endpoint `debug-playback`.

## Sprint 2

1. Criar pastas de áudio.
2. Criar categorias personalizadas.
3. Criar agendamento de pastas.
4. Criar modo sequencial/aleatório.
5. Criar spots por intervalo.
6. Separar fila principal e fila de spots.
7. Criar watchdog do player.

## Sprint 3

1. Melhorar campanhas.
2. Criar reordenação de mídias.
3. Criar validade por mídia.
4. Criar substituição de arquivo.
5. Criar extração automática de duração.
6. Corrigir mistura de áudio entre rádio e mídia.

## Sprint 4

1. Melhorar UX de upload múltiplo.
2. Melhorar modal de seleção.
3. Criar overlay do nome da música.
4. Revisar tela Agenda.
5. Melhorar controle de mídia do navegador/Windows.
6. Consolidar logs e painel de diagnóstico.

---

# Comportamento Esperado do Agente

Ao receber uma task:

1. Identificar o epic relacionado.
2. Ler as regras deste arquivo.
3. Procurar modelos, rotas, services e componentes existentes.
4. Preferir mudanças incrementais e seguras.
5. Criar migrations quando necessário.
6. Atualizar schemas e validações.
7. Atualizar player quando a regra impactar reprodução.
8. Adicionar logs.
9. Criar ou ajustar testes.
10. Explicar claramente o que foi alterado.

Sempre priorizar previsibilidade, rastreabilidade e operação estável do player.

---

# Resultado Esperado

Depois dessas correções, o PlayWave deve conseguir:

- Subir múltiplos áudios.
- Organizar áudios por categoria e pasta.
- Programar pastas por horário/data.
- Tocar rádio em sequência ou aleatório.
- Inserir spots sem matar a playlist.
- Resolver campanhas corretamente.
- Atualizar player sem limpar cache.
- Enviar comandos confiáveis ao player.
- Invalidar player antigo ao trocar pareamento.
- Evitar áudio travado.
- Evitar tocar música fora da playlist.
- Diagnosticar problemas por dispositivo.
- Operar com estabilidade em ambiente real de cliente.
