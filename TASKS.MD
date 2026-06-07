Abaixo está o backlog organizado em **tasks reais para desenvolvimento**, separado por prioridade e área: **Rádio, Player, Campanhas/Playlist, Mídia, Banco/API e Correções Críticas**.

---

# Backlog PlayWave — Correções e Melhorias

## EPIC 01 — Rádio Indoor: Upload, Categorias, Pastas e Playlists

### TASK 01 — Upload múltiplo de músicas no sistema

**Prioridade:** P1
**Área:** Frontend + Backend
**Problema:** Hoje o cliente precisa subir músicas uma por uma ou sente dificuldade em organizar muitos arquivos.

**Descrição:**
Permitir upload múltiplo de arquivos de áudio na tela de **Faixas de Áudio**, aceitando vários arquivos de uma vez, com categoria padrão, status padrão e validação individual por arquivo.

**Critérios de aceite:**

- Usuário consegue selecionar vários arquivos do computador.
- Sistema mostra lista dos arquivos antes do envio.
- Usuário consegue remover um arquivo da fila antes do upload.
- Usuário define categoria padrão para todos.
- Usuário define status padrão para todos.
- Backend processa os arquivos individualmente.
- Se um arquivo falhar, os outros continuam sendo enviados.
- Exibir relatório final: enviados, falharam, duplicados ou inválidos.

---

### TASK 02 — Criar categorias personalizadas de áudio

**Prioridade:** P1
**Área:** Frontend + Backend + Banco
**Problema:** As categorias fixas, como Música, Jingle, Anúncio, Ambiente e Outro, não resolvem a organização do cliente.

**Descrição:**
Permitir que o usuário crie categorias de áudio personalizadas diretamente pelo sistema, sem depender apenas das categorias padrão.

**Critérios de aceite:**

- Usuário pode clicar em **“Criar categoria”**.
- Categoria tem nome editável.
- Categoria aparece no upload de áudio.
- Categoria aparece nos filtros de faixas.
- Categoria pode ser usada nas pastas e playlists.
- Não permitir categorias duplicadas com o mesmo nome para o mesmo cliente/tenant.
- Categorias padrão continuam existindo.

**Sugestão de banco:**

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

---

### TASK 03 — Criar pastas de músicas para separar manhã, tarde, noite e outros grupos

**Prioridade:** P0
**Área:** Frontend + Backend + Banco
**Problema:** As músicas ficam misturadas quando o cliente monta a programação.

**Descrição:**
Criar recurso de **Pastas de Áudio** dentro da Rádio Indoor, permitindo agrupar músicas por contexto, por exemplo: Manhã, Tarde, Noite, Promoções, Ambiente, Fim de Semana etc.

**Critérios de aceite:**

- Usuário consegue criar uma pasta.
- Usuário consegue adicionar múltiplas músicas dentro da pasta.
- Usuário consegue remover músicas da pasta.
- Uma música pode estar em mais de uma pasta, se necessário.
- Pasta pode ter status ativo/inativo.
- Pasta pode ter categoria ou tipo.
- Pasta aparece na criação/edição da playlist sonora.
- Pasta aparece separada de músicas individuais.

**Sugestão de banco:**

```sql
audio_folders
- id
- tenant_id
- name
- description
- category_id
- is_active
- created_at
- updated_at

audio_folder_tracks
- id
- folder_id
- audio_track_id
- position
- created_at
```

---

### TASK 04 — Programar pasta de músicas por horário de início e fim

**Prioridade:** P0
**Área:** Frontend + Backend + Player
**Problema:** Cliente precisa tocar pastas diferentes em horários diferentes.

**Descrição:**
Permitir que uma pasta seja programada dentro da playlist sonora com horário de início e fim, por exemplo:

- Manhã: 08:00 até 12:00
- Tarde: 12:00 até 18:00
- Noite: 18:00 até 22:00

**Critérios de aceite:**

- Usuário consegue selecionar uma pasta na playlist.
- Usuário consegue definir horário inicial e final.
- Usuário pode deixar sem data final.
- Player respeita o horário da pasta.
- Fora do horário, a pasta não deve tocar.
- Quando o horário muda, o player troca automaticamente para a pasta válida.
- O sistema não precisa limpar cache/reiniciar para reconhecer a mudança.

---

### TASK 05 — Definir data de início e fim para pastas de áudio

**Prioridade:** P1
**Área:** Frontend + Backend + Player
**Problema:** Algumas pastas devem tocar apenas em um período específico.

**Descrição:**
Adicionar período de validade nas pastas de áudio.

**Critérios de aceite:**

- Pasta pode ter data de início.
- Pasta pode ter data de fim.
- Pasta pode ficar sem data de fim.
- Player só toca a pasta se estiver dentro do período válido.
- Interface mostra claramente se a pasta está vigente, futura ou expirada.

---

### TASK 06 — Opção de tocar músicas em sequência ou embaralhado

**Prioridade:** P0
**Área:** Frontend + Backend + Player
**Problema:** Cliente pediu opção de tocar na sequência ou misturado.

**Descrição:**
Adicionar modo de reprodução para playlists e pastas.

**Opções:**

- Sequencial
- Aleatório
- Aleatório sem repetir até tocar todas
- Loop ligado/desligado

**Critérios de aceite:**

- Usuário escolhe o modo na playlist sonora.
- Usuário escolhe o modo por pasta, se necessário.
- Player respeita o modo configurado.
- No modo aleatório, evitar repetir sempre a mesma música.
- Estado da fila deve persistir, para evitar repetir a mesma faixa após refresh.

---

## EPIC 02 — Spots / Áudios Programados

### TASK 07 — Criar agendamento de spot a cada X minutos

**Prioridade:** P0
**Área:** Frontend + Backend + Player
**Problema:** Cliente quer tocar spots em intervalos, por exemplo a cada 10, 20 ou 30 minutos.

**Descrição:**
Permitir que o usuário configure um spot para tocar a cada X minutos dentro da programação da rádio.

**Critérios de aceite:**

- Usuário cria um spot.
- Usuário define o áudio do spot.
- Usuário define intervalo: a cada X minutos.
- Usuário define se o spot aguarda a música terminar ou interrompe.
- Usuário define período ativo: horário inicial/final.
- Spot toca junto com a rádio, sem matar a playlist.
- Após o spot, a rádio volta para a música/fila corretamente.

---

### TASK 08 — Corrigir bug: spot programado não toca

**Prioridade:** P0
**Área:** Backend + Player
**Problema:** Cliente informou que os spots estavam programados, mas não tocavam.

**Descrição:**
Auditar a lógica de seleção de spots no backend e no player para garantir que o spot agendado entre na fila de execução no momento correto.

**Critérios de aceite:**

- Spot ativo toca quando chega o intervalo configurado.
- Spot inativo não toca.
- Spot fora do horário não toca.
- Spot sem arquivo válido não quebra a rádio.
- Logs mostram quando um spot foi selecionado, ignorado ou executado.
- Player recebe claramente o próximo spot pela API ou websocket.

**Logs necessários:**

```text
[radio.scheduler] spot_due=true
[radio.scheduler] selected_spot_id=...
[radio.player] playing_spot=...
[radio.player] returning_to_music_queue=true
```

---

### TASK 09 — Corrigir bug: quando agenda spot, só toca spot e não toca playlist

**Prioridade:** P0
**Área:** Player + Backend
**Problema:** Ao configurar agendamento de spot, o player toca apenas spot e ignora a playlist.

**Descrição:**
Separar a fila principal da rádio da fila de inserções comerciais/spots.

**Regra esperada:**

- Rádio/playlist é a trilha principal.
- Spot é uma inserção temporária.
- Spot não substitui a playlist.
- Ao terminar o spot, volta para a música.

**Critérios de aceite:**

- Player mantém uma fila principal de músicas.
- Player mantém uma fila separada de spots.
- Spot entra apenas quando estiver vencido/agendado.
- Após o spot, o player volta para o ponto correto da playlist.
- Não reiniciar música desnecessariamente após o spot.

---

## EPIC 03 — Playlist Sonora e Pastas

### TASK 10 — Corrigir bug da rota `/radio/playlists`: campanhas não reconhecem pasta

**Prioridade:** P0
**Área:** Backend + Banco + Player
**Problema:** Campanhas não reconhecem a pasta da playlist; o sistema toca apenas músicas individuais e ignora a pasta.

**Descrição:**
Criar relacionamento correto entre playlist sonora, pastas e faixas para que o backend retorne uma programação resolvida corretamente ao player.

**Solução técnica sugerida:**
Criar tabela de relacionamento entre playlists e itens da playlist, aceitando tanto áudio individual quanto pasta.

**Sugestão de banco:**

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

**Critérios de aceite:**

- Playlist pode conter músicas individuais.
- Playlist pode conter pastas.
- Playlist pode conter músicas e pastas juntas.
- Backend resolve as músicas dentro da pasta.
- Player recebe a lista final já resolvida ou recebe estrutura clara para resolver.
- Campanha reconhece a pasta como item válido.
- Player respeita prioridade, horário, data e ordem.

---

### TASK 11 — Selecionar múltiplos áudios ao criar playlist/radio/ponto

**Prioridade:** P1
**Área:** Frontend + Backend
**Problema:** Cliente não quer selecionar áudio um por um.

**Descrição:**
Na criação/edição de playlist sonora, permitir seleção em massa de faixas e pastas.

**Critérios de aceite:**

- Usuário consegue selecionar várias músicas.
- Usuário consegue selecionar uma pasta inteira.
- Usuário consegue filtrar por categoria.
- Usuário consegue desmarcar todos.
- Usuário consegue ver a ordem final de reprodução.
- Usuário consegue reordenar antes de salvar.

---

### TASK 12 — Melhorar modal de seleção de faixas

**Prioridade:** P2
**Área:** Frontend
**Problema:** A tela já permite seleção, mas pode ficar confusa com muitos áudios e pastas.

**Descrição:**
Melhorar o modal de seleção de faixas para suportar músicas, categorias e pastas.

**Critérios de aceite:**

- Campo de busca por nome.
- Filtro por categoria.
- Filtro por pasta.
- Checkbox para seleção em massa.
- Lista de selecionados separada.
- Ordenação por drag-and-drop.
- Exibir duração de cada faixa.
- Exibir duração total da playlist.

---

## EPIC 04 — Campanhas e Playlists de Mídia

### TASK 13 — Não selecionar todas as mídias apenas por “tique”

**Prioridade:** P1
**Área:** Frontend + Backend
**Problema:** Cliente quer subir/adicionar mídias na campanha/playlist de forma mais controlada, não apenas marcar todas.

**Descrição:**
Refatorar criação de campanha/playlist para tratar mídias como itens individuais com ordem, período, prioridade e configuração própria.

**Critérios de aceite:**

- Campanha pode receber mídias individualmente.
- Cada mídia na campanha pode ter configuração própria.
- Usuário consegue adicionar e remover mídia sem recriar campanha.
- Interface mostra lista de mídias adicionadas.
- Interface mostra ordem da reprodução.
- Não misturar todas as mídias sem controle.

---

### TASK 14 — Reordenar mídias em campanhas/playlists

**Prioridade:** P1
**Área:** Frontend + Backend + Player
**Problema:** Cliente pediu opção de mudar a ordem das mídias.

**Descrição:**
Adicionar ordenação manual por drag-and-drop em campanhas/playlists.

**Critérios de aceite:**

- Usuário consegue arrastar mídia para cima ou para baixo.
- Ordem é salva no banco.
- Player respeita a ordem.
- API retorna campo `position`.
- Reordenação não remove agendamentos existentes.

**Sugestão de banco:**

```sql
campaign_media_items
- id
- campaign_id
- media_id
- position
- priority
- start_date
- end_date
- created_at
- updated_at
```

---

### TASK 15 — Corrigir bug: conteúdo da campanha não passa no player

**Prioridade:** P0
**Área:** Backend + Player
**Problema:** Cliente percebeu que conteúdo cadastrado na campanha não estava passando no player.

**Descrição:**
Auditar a montagem da playlist do player para campanhas ativas, datas, horários, dias da semana, dispositivos e mídias válidas.

**Critérios de aceite:**

- Campanha ativa aparece no player.
- Campanha fora do horário não aparece.
- Campanha sem mídia válida gera log claro.
- Campanha vinculada ao dispositivo correto é carregada.
- Player atualiza a programação sem precisar limpar cache.
- Criar endpoint de debug por dispositivo.

**Endpoint sugerido:**

```http
GET /api/v1/devices/{device_id}/debug-playback
```

**Resposta esperada:**

```json
{
  "device_id": "...",
  "active_campaigns": [],
  "active_radio_playlist": {},
  "resolved_queue": [],
  "ignored_items": [
    {
      "item_id": "...",
      "reason": "outside_schedule"
    }
  ]
}
```

---

## EPIC 05 — Mídias

### TASK 16 — Detectar duração automática de vídeos e áudios

**Prioridade:** P1
**Área:** Backend + Storage/Worker
**Problema:** Hoje o usuário precisa digitar o tempo da mídia manualmente.

**Descrição:**
Ao subir vídeo ou áudio, o backend deve detectar automaticamente a duração usando processamento no servidor.

**Critérios de aceite:**

- Backend extrai duração de vídeo.
- Backend extrai duração de áudio.
- Campo de duração é preenchido automaticamente.
- Usuário pode visualizar duração na interface.
- Se a extração falhar, exibir aviso e permitir preenchimento manual.
- Processamento não deve travar a API principal.

**Solução sugerida:**
Usar worker assíncrono com FFmpeg/ffprobe.

---

### TASK 17 — Definir período de exibição na própria mídia

**Prioridade:** P1
**Área:** Frontend + Backend + Player
**Problema:** Cliente quer colocar data/período diretamente na mídia ao subir.

**Descrição:**
Adicionar campos de validade na mídia.

**Campos:**

```text
start_date
end_date
start_time
end_time
days_of_week
```

**Critérios de aceite:**

- Usuário define data inicial.
- Usuário define data final opcional.
- Usuário define horário opcional.
- Player ignora mídia fora do período.
- Interface mostra status: vigente, futura ou expirada.

---

### TASK 18 — Substituir mídia sem perder agendamento

**Prioridade:** P1
**Área:** Frontend + Backend + Banco
**Problema:** Cliente quer trocar o arquivo de uma mídia sem remover ela das campanhas/agendamentos.

**Descrição:**
Criar ação **“Substituir arquivo”** na mídia.

**Critérios de aceite:**

- Usuário seleciona uma mídia existente.
- Usuário sobe um novo arquivo.
- O ID lógico da mídia permanece o mesmo.
- Campanhas que usam a mídia continuam funcionando.
- Histórico da versão anterior pode ser mantido.
- Player passa a usar o novo arquivo após sincronização.

**Sugestão de banco:**

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

---

## EPIC 06 — Player e Dispositivos

### TASK 19 — Corrigir comando de desligar/reiniciar pelo gerenciador

**Prioridade:** P0
**Área:** Backend + Player + WebSocket/Polling
**Problema:** O player não recebe comando pela tela de dispositivos.

**Descrição:**
Implementar canal confiável de comandos entre gerenciador e player.

**Comandos mínimos:**

- Desligar player
- Reiniciar player
- Recarregar programação
- Limpar cache local
- Pausar
- Continuar
- Atualizar pareamento

**Critérios de aceite:**

- Comando enviado pelo gerenciador chega no player.
- Player confirma recebimento.
- Player confirma execução.
- Se player estiver offline, comando fica pendente ou expira com status claro.
- Tela de dispositivos mostra status do comando.

**Sugestão de banco:**

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

---

### TASK 20 — Corrigir bug: alterar código de pareamento e player continuar funcionando

**Prioridade:** P0
**Área:** Backend + Player + Segurança
**Problema:** Ao alterar o código de pareamento, o player antigo continua válido.

**Descrição:**
Quando o código de pareamento for alterado, invalidar sessões antigas do dispositivo.

**Critérios de aceite:**

- Alterar código de pareamento invalida tokens antigos.
- Player antigo precisa parear novamente.
- Backend rejeita requests com sessão antiga.
- Player mostra tela de pareamento quando sessão expira.
- Gerenciador mostra status “necessário parear novamente”.

**Solução sugerida:**

```text
device.pairing_version
device_session.pairing_version
```

Se a versão da sessão for diferente da versão atual do dispositivo, bloquear o player.

---

### TASK 21 — Corrigir bug: ao mexer no gerenciador o player reinicia

**Prioridade:** P0
**Área:** Backend + Player
**Problema:** Qualquer alteração no gerenciador reinicia o player de exibição.

**Descrição:**
Separar atualização de configuração de reinicialização do player.

**Regra esperada:**

- Alterar nome, categoria ou metadado não reinicia player.
- Alterar playlist deve atualizar fila sem reload completo.
- Alterar mídia atual pode trocar no próximo ciclo.
- Reinício só ocorre quando comando explícito for enviado.

**Critérios de aceite:**

- Player não dá refresh completo a cada mudança.
- Player recebe evento de atualização.
- Player recalcula fila sem recarregar a página.
- Reprodução atual não é interrompida sem necessidade.

---

### TASK 22 — Corrigir bug: rádio pausa quando aba fica em segundo plano

**Prioridade:** P0
**Área:** Player Web
**Problema:** Cliente informou que a rádio para quando está em outra aba e volta quando entra na aba do player.

**Descrição:**
Auditar comportamento do player em background no navegador e implementar estratégia para manter áudio ativo.

**Critérios de aceite:**

- Áudio continua tocando com aba em segundo plano.
- Player não depende de foco da aba para avançar música.
- Eventos `visibilitychange`, `pause`, `ended`, `stalled` e `error` são tratados.
- Player tenta recuperar áudio quando detectar travamento.
- Logs mostram motivo da pausa.

**Implementações sugeridas:**

- Usar elemento `<audio>` persistente.
- Não recriar o player a cada música.
- Tratar `document.visibilityState`.
- Criar watchdog de reprodução.
- Usar Wake Lock quando disponível.
- Evitar que o estado da rádio dependa de renderização visual.
- Considerar app Windows/kiosk para operação profissional.

---

### TASK 23 — Corrigir bug: rádio toca música que não está na playlist

**Prioridade:** P0
**Área:** Backend + Player + Cache
**Problema:** Cliente informou que a música tocando não estava na playlist configurada.

**Descrição:**
Garantir que a fila do player seja gerada somente com músicas válidas da playlist/pasta ativa.

**Critérios de aceite:**

- Player limpa fila antiga ao receber nova programação.
- Player não usa cache antigo quando playlist muda.
- Backend envia `playlist_version`.
- Player compara versão local com versão do servidor.
- Se versão mudou, player atualiza fila.
- Tela debug mostra de onde veio cada música.

**Campo sugerido:**

```text
playlist_version
schedule_version
content_hash
```

---

### TASK 24 — Corrigir bug: rádio toca apenas uma música

**Prioridade:** P0
**Área:** Player
**Problema:** Cliente informou que a rádio estava tocando apenas uma música.

**Descrição:**
Auditar avanço automático da fila da rádio.

**Critérios de aceite:**

- Ao terminar uma música, player toca a próxima.
- Se estiver em loop, volta para o início.
- Se estiver em aleatório, escolhe próxima sem repetir indevidamente.
- Se música falhar, pula para próxima.
- Logs mostram índice atual, próxima música e motivo da troca.

---

### TASK 25 — Corrigir bug: áudio pausa, botão play fica sem som, só volta na próxima música

**Prioridade:** P0
**Área:** Player Web
**Problema:** Cliente informou que o áudio para, o player aparenta tocar, mas fica sem som até iniciar outra música.

**Descrição:**
Implementar recuperação de estado de áudio travado.

**Critérios de aceite:**

- Detectar quando `audio.paused = true`.
- Detectar quando `currentTime` não avança.
- Detectar quando volume/mute está incorreto.
- Detectar erro de decode/network.
- Tentar recarregar o áudio atual uma vez.
- Se não recuperar, pular para próxima música.
- Registrar log do erro.

**Watchdog sugerido:**

```text
A cada 5 segundos:
- verificar se deveria estar tocando
- verificar se currentTime avançou
- se não avançou por X segundos, recuperar
```

---

### TASK 26 — Corrigir mídia misturando áudio com rádio

**Prioridade:** P0
**Área:** Player + Scheduler
**Problema:** Cliente informou que mídia está misturando áudio com rádio.

**Descrição:**
Criar regra clara de prioridade entre:

- Campanha de vídeo/imagem
- Rádio ambiente
- Spot
- Áudio de mídia
- Silêncio

**Regra sugerida:**

```text
1. Campanha visual toca no player.
2. Rádio ambiente toca como trilha sonora, se permitido.
3. Se a mídia/campanha tiver áudio próprio, reduzir ou pausar rádio.
4. Spot pode entrar conforme regra: aguardar silêncio ou interromper.
5. Nunca tocar dois áudios principais ao mesmo tempo.
```

**Critérios de aceite:**

- Vídeo com áudio pausa ou reduz rádio.
- Imagem sem áudio permite rádio.
- Spot não toca junto com outro spot.
- Rádio não sobrepõe áudio de mídia.
- Player mostra qual fonte de áudio está ativa.

---

### TASK 27 — Exibir nome da música no canto da tela do player/TV

**Prioridade:** P2
**Área:** Player Frontend
**Problema:** Cliente quer visualizar o nome da música tocando.

**Descrição:**
Adicionar overlay discreto com nome da música atual no player.

**Critérios de aceite:**

- Mostrar nome da faixa atual.
- Mostrar categoria ou artista, se existir.
- Configuração para ativar/desativar.
- Posição configurável: canto inferior esquerdo, inferior direito etc.
- Não atrapalhar campanha visual.
- Atualizar automaticamente quando mudar a música.

---

### TASK 28 — Tratar controle de mídia do navegador/Windows

**Prioridade:** P2
**Área:** Player Web
**Problema:** Na imagem aparece o controle de mídia do navegador/Windows. Isso pode confundir o cliente ou interferir na percepção do player.

**Descrição:**
Configurar corretamente a Media Session API ou neutralizar metadados quando necessário.

**Critérios de aceite:**

- Controle do navegador mostra nome correto da música, se habilitado.
- Botão pause/play do sistema operacional não quebra o player.
- Se o usuário pausar pelo controle do Windows, o player detecta.
- Player consegue retomar ou atualizar estado corretamente.
- Avaliar se deve ocultar/minimizar esse comportamento no modo kiosk.

---

## EPIC 07 — Agenda e Gerenciador

### TASK 29 — Revisar tela de Agenda do gerenciador

**Prioridade:** P2
**Área:** Produto + Frontend
**Problema:** Cliente informou que a Agenda no gerenciador parece desnecessária, pois o agendamento já existe na campanha.

**Descrição:**
Revisar a função da tela Agenda para evitar duplicidade de regra.

**Opções de solução:**

1. Remover a tela Agenda.
2. Manter apenas como visão consolidada.
3. Transformar em calendário de campanhas, mídias, rádio e spots.
4. Bloquear edição direta nela para evitar conflito.

**Critérios de aceite:**

- Não existir agendamento duplicado conflitante.
- Campanha continua sendo a fonte principal de agendamento.
- Agenda, se existir, mostra apenas visão consolidada.
- Interface deixa claro de onde vem cada programação.

---

## EPIC 08 — Prioridade de Mídias e Áudios

### TASK 30 — Documentar e padronizar o campo “prioridade”

**Prioridade:** P1
**Área:** Produto + Backend + Frontend + Player
**Problema:** Cliente perguntou o que significa o número de prioridade nas mídias e áudios.

**Descrição:**
Definir regra oficial para prioridade e aplicar de forma consistente no sistema.

**Explicação sugerida para o cliente:**
O número de prioridade serve para decidir **o que toca primeiro quando existem dois ou mais conteúdos válidos para o mesmo horário**.

Exemplo:

```text
Prioridade 10: mais importante
Prioridade 5: média
Prioridade 1: menor importância
```

Se uma campanha, spot ou mídia estiverem disponíveis ao mesmo tempo, o sistema usa a prioridade para decidir qual tem preferência.

**Regra recomendada:**

```text
Maior número = maior prioridade.
```

**Critérios de aceite:**

- Interface explica o campo prioridade.
- Tooltip disponível no frontend.
- Backend ordena corretamente por prioridade.
- Player respeita prioridade.
- Em caso de empate, usar ordem manual/position.
- Prioridade não deve substituir agendamento; ela só desempata conteúdos válidos.

**Texto de tooltip sugerido:**

```text
Prioridade define qual conteúdo tem preferência quando há mais de um item disponível no mesmo horário. Quanto maior o número, maior a prioridade.
```

---

## EPIC 09 — Cache, Sincronização e Atualização em Tempo Real

### TASK 31 — Criar versionamento de programação do player

**Prioridade:** P0
**Área:** Backend + Player
**Problema:** Cliente precisou limpar cache/reiniciar para o player entender a playlist.

**Descrição:**
Criar controle de versão da programação para que o player saiba quando precisa atualizar a fila.

**Critérios de aceite:**

- Backend gera `schedule_version`.
- Toda alteração relevante incrementa a versão.
- Player consulta versão periodicamente ou recebe via websocket.
- Se versão mudou, player atualiza programação.
- Não precisa limpar cache manualmente.
- Não precisa reiniciar sistema para reconhecer alteração.

**Sugestão:**

```json
{
  "device_id": "...",
  "schedule_version": 42,
  "radio_playlist_version": 18,
  "campaign_version": 9
}
```

---

### TASK 32 — Implementar websocket ou polling confiável para player

**Prioridade:** P0
**Área:** Backend + Player
**Problema:** Player não responde bem ao gerenciador e não recebe comandos de forma confiável.

**Descrição:**
Criar camada de sincronização entre backend e player.

**Opção A — WebSocket:**

```text
Backend envia eventos em tempo real:
- schedule.updated
- device.command
- playlist.updated
- media.replaced
- player.reload_required
```

**Opção B — Polling:**

```text
Player consulta a cada 5 ou 10 segundos:
GET /api/v1/player/sync
```

**Critérios de aceite:**

- Player detecta alteração sem refresh manual.
- Comando do gerenciador chega no player.
- Player confirma status.
- Se websocket cair, fallback para polling.
- Logs mostram última sincronização.

---

### TASK 33 — Criar cache controlado no player

**Prioridade:** P1
**Área:** Player
**Problema:** Cache antigo parece causar playlist errada, rádio travada ou necessidade de limpeza manual.

**Descrição:**
Substituir cache solto por cache versionado.

**Critérios de aceite:**

- Player salva programação local com versão.
- Se versão do servidor mudou, descarta cache antigo.
- Arquivos podem ser cacheados, mas programação não pode ficar obsoleta.
- Botão “Limpar cache do player” no gerenciador envia comando remoto.
- Cache não pode fazer tocar música fora da playlist atual.

---

## EPIC 10 — Observabilidade, Logs e Debug

### TASK 34 — Criar painel de debug do player/dispositivo

**Prioridade:** P0
**Área:** Backend + Frontend + Player
**Problema:** Hoje é difícil entender por que campanha, rádio, pasta ou spot não toca.

**Descrição:**
Criar tela técnica de debug por dispositivo.

**Deve mostrar:**

- Dispositivo online/offline.
- Playlist sonora ativa.
- Campanhas ativas.
- Pasta ativa no momento.
- Música atual.
- Próxima música.
- Spot pendente.
- Último comando recebido.
- Último erro do player.
- Versão da programação.
- Motivo de itens ignorados.

**Critérios de aceite:**

- Suporte consegue diagnosticar sem acessar banco.
- Cliente não precisa limpar cache para testar.
- Logs ajudam a identificar se erro é de agendamento, mídia, player ou cache.

---

### TASK 35 — Padronizar logs da rádio e do player

**Prioridade:** P1
**Área:** Backend + Player
**Problema:** Bugs atuais são difíceis de rastrear.

**Descrição:**
Adicionar logs estruturados nos pontos críticos.

**Eventos obrigatórios:**

```text
radio.playlist.loaded
radio.folder.resolved
radio.track.started
radio.track.ended
radio.track.failed
radio.spot.due
radio.spot.started
radio.spot.finished
player.schedule.updated
player.command.received
player.command.executed
campaign.media.selected
campaign.media.ignored
```

**Critérios de aceite:**

- Cada evento tem `device_id`.
- Cada evento tem `playlist_id`, quando aplicável.
- Cada evento tem `track_id`, quando aplicável.
- Cada erro tem motivo claro.
- Logs podem ser filtrados por dispositivo.

---

# Ordem recomendada de execução

## Sprint 1 — Corrigir o que está quebrando operação

1. **TASK 10** — Corrigir bug de pastas na rota `/radio/playlists`.
2. **TASK 15** — Corrigir campanha não passando no player.
3. **TASK 19** — Corrigir comandos de desligar/reiniciar.
4. **TASK 20** — Invalidar player após alteração do código de pareamento.
5. **TASK 21** — Evitar reinício do player ao mexer no gerenciador.
6. **TASK 22** — Corrigir rádio pausando em aba de segundo plano.
7. **TASK 23** — Corrigir música fora da playlist.
8. **TASK 24** — Corrigir rádio tocando apenas uma música.
9. **TASK 25** — Corrigir áudio sem som até próxima música.
10. **TASK 31** — Criar versionamento de programação.

---

## Sprint 2 — Consolidar rádio, spots e pastas

1. **TASK 03** — Criar pastas de músicas.
2. **TASK 04** — Programar pastas por horário.
3. **TASK 06** — Sequencial/embaralhado.
4. **TASK 07** — Spot a cada X minutos.
5. **TASK 08** — Spot programado não toca.
6. **TASK 09** — Spot não pode substituir playlist.
7. **TASK 11** — Seleção múltipla de áudios.
8. **TASK 32** — Websocket/polling confiável.

---

## Sprint 3 — Melhorias de mídia e campanhas

1. **TASK 13** — Melhorar adição de mídias em campanhas.
2. **TASK 14** — Reordenar mídias.
3. **TASK 16** — Detectar duração automática.
4. **TASK 17** — Período de exibição na mídia.
5. **TASK 18** — Substituir mídia sem perder agendamento.
6. **TASK 26** — Resolver mistura de áudio da rádio com mídia.
7. **TASK 30** — Padronizar prioridade.

---

## Sprint 4 — UX, organização e acabamento

1. **TASK 01** — Upload múltiplo.
2. **TASK 02** — Categorias personalizadas.
3. **TASK 05** — Data início/fim em pastas.
4. **TASK 12** — Melhorar modal de seleção.
5. **TASK 27** — Nome da música no player/TV.
6. **TASK 28** — Controle de mídia do navegador/Windows.
7. **TASK 29** — Revisar Agenda.
8. **TASK 34** — Painel de debug.
9. **TASK 35** — Logs padronizados.

---

# Resumo do problema central

O ponto mais crítico não é só “adicionar botão no frontend”. O sistema precisa de uma engenharia mais forte de **programação resolvida para o player**.

A solução correta é o backend entregar ao player uma estrutura clara dizendo:

```text
Agora deve tocar:
- campanha X
- playlist sonora Y
- pasta Z
- música atual A
- próximo item B
- spot pendente C
- prioridade aplicada
- motivo dos itens ignorados
- versão da programação
```

Sem isso, o player fica dependente de cache, estado antigo, reload manual e comportamento imprevisível do navegador. O núcleo da correção é:

```text
Banco bem relacionado
+ Backend resolvendo agenda corretamente
+ Player com fila própria e watchdog
+ Sincronização por versão/websocket
+ Logs de debug por dispositivo
```

Isso transforma os pedidos do cliente em uma solução robusta, não apenas em remendos de interface.
