# SKILL.md — PlayWave Aplicativo

## Visão Geral do Projeto

O PlayWave é um sistema de gerenciamento e exibição de mídias para TVs, players e pontos de rádio. O sistema permite cadastrar dispositivos, parear players, criar campanhas, playlists, agendamentos, mídias de vídeo/imagem/áudio, spots e faixas de rádio.

O objetivo principal é garantir que o conteúdo programado no gerenciador seja exibido corretamente nos dispositivos, respeitando agenda, prioridade, status, tipo de mídia e regras específicas de rádio e player.

---

## Stack Principal

### Backend

* FastAPI
* Python
* Banco relacional, preferencialmente PostgreSQL
* SQLAlchemy ou ORM equivalente
* Alembic para migrations
* Redis opcional para cache, filas, locks e estado de player
* Docker / Docker Compose
* JWT ou autenticação por token
* APIs REST versionadas, preferencialmente em `/api/v1`

### Frontend

* React ou Next.js
* TypeScript
* Interface administrativa para campanhas, playlists, dispositivos, rádio e mídias
* Componentes reutilizáveis para upload, ordenação, agendamento e seleção múltipla

### Player

* Aplicação web, desktop ou embarcada responsável por executar o conteúdo
* Deve funcionar de forma resiliente, sem depender da aba estar em foco
* Deve manter heartbeat com o backend
* Deve sincronizar playlist/campanha periodicamente
* Deve tolerar falhas de rede usando cache local

---

## Domínios do Sistema

### Dispositivos

Um dispositivo representa um player ou ponto de exibição cadastrado no sistema.

Regras importantes:

* Um dispositivo pode estar pareado ou não pareado.
* Alterar código de pareamento deve invalidar players antigos, quando aplicável.
* O backend deve registrar último heartbeat.
* O sistema deve permitir desligar, reiniciar ou atualizar player pelo gerenciador.
* O player não deve continuar funcionando se o vínculo for invalidado.

---

### Mídias

Mídias podem ser vídeos, imagens, áudios, spots ou arquivos usados em rádio.

Regras importantes:

* Toda mídia deve possuir status ativo/inativo.
* Toda mídia deve poder ter período de validade: data de início e data de fim.
* Vídeos devem ter duração detectada automaticamente sempre que possível.
* A substituição de mídia deve preservar vínculos com campanhas e playlists.
* Mídias inativas, expiradas ou inválidas não devem entrar na programação do player.

Campos recomendados:

* id
* name
* type
* file_url
* duration
* is_active
* valid_from
* valid_until
* created_at
* updated_at

---

### Campanhas

Campanhas agrupam mídias para exibição em dispositivos.

Regras importantes:

* Campanha precisa estar ativa.
* Campanha deve respeitar dias da semana.
* Campanha deve respeitar horário de início e fim.
* Campanha deve respeitar período de validade.
* Campanha deve estar associada a um ou mais dispositivos.
* A ordem das mídias dentro da campanha deve ser configurável.
* O sistema não deve depender apenas de checkbox para adicionar mídias; deve existir gerenciamento dedicado de itens da campanha.

Campos recomendados:

* id
* name
* status
* start_date
* end_date
* start_time
* end_time
* weekdays
* priority
* device_ids

---

### Playlist

Playlist é uma sequência ordenada de mídias.

Regras importantes:

* Deve permitir reordenar itens.
* Deve permitir adicionar mídia individualmente.
* Deve permitir remover mídia sem excluir o arquivo original.
* Deve permitir modo sequencial ou aleatório.
* Deve separar playlist de vídeo/imagem da lógica de rádio quando necessário.

---

### Rádio

O módulo de rádio controla músicas, spots e faixas de áudio.

Regras importantes:

* Deve permitir upload múltiplo de músicas.
* Deve permitir selecionar múltiplos áudios de uma vez.
* Deve permitir criar categorias, pastas ou módulos de áudio.
* Deve permitir separar músicas por período, como manhã, tarde e noite.
* Deve permitir tocar músicas em sequência ou embaralhadas.
* Spots devem poder ser agendados para tocar a cada X minutos.
* Spot não deve bloquear a playlist principal da rádio.
* Após tocar um spot, a rádio deve retornar para a programação musical.
* O player não deve misturar indevidamente áudio de mídia com rádio, salvo quando isso for explicitamente configurado.

Entidades recomendadas:

* radio_station
* audio_track
* audio_folder
* radio_playlist
* radio_playlist_item
* radio_spot
* radio_spot_schedule

---

## Regras Críticas de Execução do Player

O player deve buscar uma programação resolvida, não montar regras complexas sozinho.

Endpoint recomendado:

```http
GET /api/v1/devices/{device_id}/resolved-schedule
```

Esse endpoint deve retornar apenas o que o player precisa executar agora.

Exemplo de resposta:

```json
{
  "device_id": "abc123",
  "server_time": "2026-06-03T12:00:00-03:00",
  "mode": "campaign",
  "items": [
    {
      "id": "media_1",
      "type": "video",
      "url": "https://cdn.playwave.com/video.mp4",
      "duration": 30,
      "order": 1
    }
  ],
  "radio": {
    "enabled": true,
    "current_playlist_id": "radio_playlist_1",
    "spot_rules": [
      {
        "spot_id": "spot_1",
        "interval_minutes": 15
      }
    ]
  }
}
```

O player deve:

* Manter execução contínua.
* Não depender de foco da aba.
* Evitar reiniciar ao receber pequenas alterações do gerenciador.
* Aplicar atualização de programação de forma controlada.
* Fazer cache local da última programação válida.
* Enviar heartbeat periódico.
* Registrar erros de execução.

---

## Diagnóstico e Logs

Sempre que campanha, rádio ou player falhar, verificar:

### Campanha não aparece

Checklist:

* Campanha está ativa?
* Está dentro da data válida?
* Está dentro do horário válido?
* O dia da semana atual está permitido?
* O dispositivo está vinculado?
* As mídias estão ativas?
* As mídias possuem arquivos válidos?
* A campanha possui itens?

Log recomendado:

```bash
docker logs -f playwave-backend | grep playlist
```

Endpoint recomendado:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/devices/{device_id}/debug
```

---

## Padrões de Backend

### Organização sugerida

```bash
app/
  api/
    v1/
      endpoints/
  core/
  models/
  schemas/
  services/
  repositories/
  workers/
  player/
  radio/
  campaigns/
  media/
```

### Regra

Controllers/endpoints não devem conter regra de negócio complexa.

A lógica deve ficar em services, por exemplo:

```bash
services/
  schedule_resolver.py
  campaign_service.py
  radio_scheduler.py
  player_sync_service.py
```

---

## Serviços Importantes

### Schedule Resolver

Responsável por decidir o que deve tocar agora.

Deve considerar:

* Campanhas ativas
* Prioridade
* Data atual
* Horário atual
* Dia da semana
* Dispositivo
* Status das mídias
* Modo rádio
* Spots programados

### Radio Scheduler

Responsável por controlar:

* Playlist musical
* Pastas por período
* Spots por intervalo
* Modo sequencial ou aleatório
* Retorno para música após spot

### Player Sync Service

Responsável por:

* Heartbeat
* Versão da programação
* Detecção de mudanças
* Comandos remotos
* Pareamento
* Invalidação de sessão

---

## Padrões de Frontend

O frontend deve priorizar clareza operacional para o cliente.

### Funcionalidades essenciais

* Upload múltiplo de mídias
* Upload múltiplo de áudios
* Criação de categoria/pasta/módulo de áudio
* Drawer lateral para criação rápida de categoria
* Seleção múltipla
* Ordenação por drag and drop
* Visualização clara de agenda
* Status visível de campanha, mídia e dispositivo
* Tela de debug do player
* Indicação de último heartbeat
* Indicação do conteúdo atualmente em execução

### Telas recomendadas

* Dashboard
* Dispositivos
* Campanhas
* Playlists
* Mídias
* Rádio
* Spots
* Logs / Diagnóstico
* Configurações do Player

---

## Padrões de Banco de Dados

Evitar campos ambíguos.

Preferir tabelas relacionais explícitas:

```bash
campaigns
campaign_items
campaign_devices
media
devices
radio_stations
audio_tracks
audio_folders
radio_playlist_items
radio_spots
radio_spot_schedules
player_commands
player_heartbeats
```

Toda tabela principal deve ter:

* id
* created_at
* updated_at
* is_active ou status

---

## Cuidados Antes de Alterar Código

Antes de alterar qualquer regra de campanha, player ou rádio:

1. Verificar se a alteração afeta o schedule resolver.
2. Verificar se a alteração afeta o player em execução.
3. Verificar se campanhas antigas continuam funcionando.
4. Verificar se mídias inativas continuam sendo filtradas.
5. Verificar se spots não bloqueiam a rádio.
6. Verificar se o player não reinicia sem necessidade.
7. Verificar se a alteração exige migration.
8. Verificar se o frontend precisa refletir novo campo ou regra.

---

## Critérios de Qualidade

Uma entrega só deve ser considerada pronta se:

* Possui migration quando altera banco.
* Possui validação no backend.
* Possui tratamento de erro no frontend.
* Possui logs úteis.
* Possui teste manual documentado.
* Não quebra players já pareados.
* Não reinicia player sem necessidade.
* Não mistura rádio, spots e mídia de forma incorreta.
* Funciona com múltiplos arquivos.
* Funciona com campanhas, playlists e dispositivos reais.

---

## Prompts Úteis Para Auditoria

### Auditar funcionamento de campanha

Verifique se o sistema possui uma cadeia completa para campanhas: cadastro, vínculo com dispositivos, vínculo com mídias, ordenação, agenda, validação de status, resolução da programação e execução no player. Identifique falhas que possam fazer uma campanha ativa não aparecer no player.

### Auditar funcionamento de rádio

Verifique se o módulo de rádio suporta upload múltiplo, categorias/pastas, playlists por período, modo sequencial/aleatório, spots por intervalo e retorno automático para a música após execução do spot. Identifique riscos de o spot bloquear a playlist principal.

### Auditar player

Verifique se o player depende de foco da aba, se possui heartbeat, cache local, reconexão, comandos remotos, controle de pareamento e atualização incremental da programação sem reiniciar desnecessariamente.

---

## Princípio Principal

O backend deve resolver a programação.
O frontend deve gerenciar com clareza.
O player deve apenas executar de forma resiliente.
