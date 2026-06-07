Você é um arquiteto backend sênior especialista em FastAPI, SQLAlchemy, PostgreSQL, Alembic, Pydantic, arquitetura multi-tenant e players de mídia.

Você vai trabalhar no projeto PlayWave.

Objetivo principal:
Auditar, corrigir e implementar toda a estrutura de SPOTS no backend, garantindo que dispositivos, campanhas, mídias, playlists, agendas e player reconheçam corretamente os spots.

Contexto do problema:
O projeto possui models relacionados a áudio e spots, incluindo:

- AudioTrack
- AudioSpot
- AudioSpotSchedule
- AudioPlaylist
- AudioPlaylistItem
- AudioPlaylistFolderSchedule
- Device
- Campaign
- Media
- AudioPlaybackEvent

Atualmente, AudioSpot aponta para AudioTrack.
AudioSpotSchedule aponta para AudioSpot e AudioPlaylist.
AudioPlaybackEvent registra spot_id.
Porém, a regra de negócio ainda está incompleta: o backend precisa saber quando, onde e como o spot deve tocar.

Problema real a resolver:
O cliente consegue cadastrar ou agendar spots, mas os spots podem não tocar porque a estrutura pode estar incompleta entre:

- models.py
- schemas Pydantic
- services
- repositories
- endpoints admin
- endpoint do player
- payload enviado ao player
- logs de reprodução
- versionamento/sincronização do player

A tarefa é fazer uma auditoria completa e implementar a regra corretamente.

====================================================================

1. # AUDITORIA INICIAL OBRIGATÓRIA

Antes de implementar qualquer coisa, analise o projeto inteiro e responda:

1. Onde AudioSpot é criado?
2. Onde AudioSpotSchedule é criado?
3. Onde o backend busca spots ativos?
4. Onde o player recebe configuração de áudio?
5. Onde o player recebe playlist, músicas, pastas e spots?
6. Onde são registrados eventos de reprodução?
7. Onde AudioPlaybackEvent é usado para calcular intervalo?
8. Existe endpoint de spots?
9. Existe endpoint de spot schedules?
10. Existe endpoint de campanha que salva spot?
11. Existe endpoint de device que salva spot?
12. Existe endpoint de playlist que salva spot?
13. O frontend salva spots em qual payload?
14. O backend espera spots em qual schema?
15. O player consome spots de qual campo no JSON?
16. Existe schema mismatch entre UI, API, banco e player?

Entregue primeiro um relatório com:

- O que já existe.
- O que está funcionando.
- O que está incompleto.
- O que está duplicado.
- O que está legado.
- O que precisa ser migrado.
- Onde existe risco de salvar em uma tabela e ler de outra.

Não implemente antes de entender essa estrutura.

==================================================================== 2. REGRA DE NEGÓCIO ESPERADA
============================

A regra correta é:

Spot não deve ficar preso diretamente dentro de Device, Campaign ou Media por um campo único spot_id.

A entidade central de vínculo deve ser AudioSpotSchedule.

AudioSpotSchedule deve responder:

- Qual spot vai tocar?
- Onde ele toca?
- Em qual playlist?
- Em qual campanha?
- Em qual dispositivo?
- Em qual mídia, se essa regra existir?
- Em qual tenant?
- Em qual data?
- Em quais dias da semana?
- Em qual horário?
- A cada quantos segundos?
- Com qual política de inserção?
- Com qual prioridade?

Modelo conceitual desejado:

Tenant
├── Device
├── Campaign
├── Media
├── AudioPlaylist
│ ├── AudioPlaylistItem
│ ├── AudioPlaylistFolderSchedule
│ └── AudioSpotSchedule
├── AudioSpot
│ └── AudioTrack
└── AudioPlaybackEvent

Fluxo correto:

Device
→ Campanha ativa
→ Playlist de áudio efetiva
→ Tracks da playlist
→ Folder schedules ativos
→ Spot schedules ativos
→ Player toca
→ AudioPlaybackEvent registra execução

==================================================================== 3. ALTERAÇÕES ESPERADAS NO MODELS.PY
====================================

Audite e implemente, se ainda não existir, os seguintes relacionamentos.

3.1. Tenant deve reconhecer spots e agendas de spots

Adicionar em Tenant:

audio_spots = relationship("AudioSpot", back_populates="tenant")
audio_spot_schedules = relationship("AudioSpotSchedule", back_populates="tenant")

3.2. AudioSpot deve ter tenant com back_populates

Trocar:

tenant = relationship("Tenant")

Por:

tenant = relationship("Tenant", back_populates="audio_spots")

3.3. AudioSpotSchedule precisa ter tenant_id

Adicionar:

tenant_id = Column(
UUID(as_uuid=True),
ForeignKey("tenants.id", ondelete="CASCADE"),
nullable=False,
index=True,
)

tenant = relationship("Tenant", back_populates="audio_spot_schedules")

3.4. AudioSpotSchedule deve aceitar escopos opcionais

Adicionar, se a regra do produto exigir:

campaign_id = Column(
UUID(as_uuid=True),
ForeignKey("campaigns.id", ondelete="CASCADE"),
nullable=True,
index=True,
)

device_id = Column(
UUID(as_uuid=True),
ForeignKey("devices.id", ondelete="CASCADE"),
nullable=True,
index=True,
)

media_id = Column(
UUID(as_uuid=True),
ForeignKey("media.id", ondelete="CASCADE"),
nullable=True,
index=True,
)

3.5. AudioSpotSchedule deve manter playlist_id

Manter playlist_id para compatibilidade com a rádio/playlist.

Mas avaliar se playlist_id deve continuar nullable=False ou virar nullable=True.

Regra recomendada:

- playlist_id pode ser nullable=True
- mas pelo menos um escopo deve existir:
  - playlist_id
  - campaign_id
  - device_id
  - media_id

  3.6. AudioSpotSchedule deve permitir override de insertion_policy

Adicionar:

insertion_policy = Column(
SQLEnum(AudioSpotInsertionPolicy, name="audio_spot_insertion_policy", values_callable=enum_values),
nullable=True,
)

Regra de precedência:

1. AudioSpotSchedule.insertion_policy
2. AudioSpot.insertion_policy
3. default: wait_silence

3.7. Campaign deve reconhecer spot_schedules

Adicionar em Campaign:

spot_schedules = relationship(
"AudioSpotSchedule",
back_populates="campaign",
cascade="all, delete-orphan",
)

3.8. Device deve reconhecer spot_schedules

Adicionar em Device:

spot_schedules = relationship(
"AudioSpotSchedule",
back_populates="device",
cascade="all, delete-orphan",
)

3.9. Media deve reconhecer spot_schedules apenas se o produto permitir spot por mídia

Adicionar em Media:

spot_schedules = relationship(
"AudioSpotSchedule",
back_populates="media",
cascade="all, delete-orphan",
)

3.10. AudioSpotSchedule relationships

Adicionar:

campaign = relationship("Campaign", back_populates="spot_schedules")
device = relationship("Device", back_populates="spot_schedules")
media = relationship("Media", back_populates="spot_schedules")

3.11. Revisar UniqueConstraint atual

Se existir:

UniqueConstraint("spot_id", "playlist_id")

Remover ou alterar.

Motivo:
Essa constraint impede criar múltiplas agendas para o mesmo spot e mesma playlist em horários diferentes.

Exemplo que deve ser permitido:

- Spot A na playlist X das 08:00 às 12:00 a cada 10 minutos
- Spot A na playlist X das 13:00 às 18:00 a cada 30 minutos

Criar uma constraint mais flexível ou controlar duplicidade na service layer.

==================================================================== 4. MIGRATIONS ALEMBIC
=====================

Criar migration Alembic segura, sem quebrar dados existentes.

A migration deve:

1. Adicionar tenant_id em audio_spot_schedules.
2. Preencher tenant_id retroativamente usando:
   - AudioSpot.tenant_id
   - ou AudioPlaylist.tenant_id

3. Tornar tenant_id nullable=False apenas depois do backfill.
4. Adicionar campaign_id, device_id e media_id se necessário.
5. Adicionar insertion_policy em audio_spot_schedules.
6. Remover ou alterar a unique constraint antiga.
7. Criar índices para:
   - tenant_id
   - spot_id
   - playlist_id
   - campaign_id
   - device_id
   - media_id
   - is_active
   - starts_at
   - ends_at

8. Garantir downgrade seguro.

A migration precisa ser compatível com PostgreSQL.

==================================================================== 5. SCHEMAS PYDANTIC
===================

Criar ou ajustar schemas:

- AudioSpotCreate
- AudioSpotUpdate
- AudioSpotResponse
- AudioSpotScheduleCreate
- AudioSpotScheduleUpdate
- AudioSpotScheduleResponse
- PlayerSpotScheduleResponse

AudioSpotScheduleCreate deve aceitar:

- spot_id
- playlist_id opcional
- campaign_id opcional
- device_id opcional
- media_id opcional
- interval_seconds
- start_time
- end_time
- starts_at
- ends_at
- days_of_week
- insertion_policy
- priority
- is_active

Validações obrigatórias:

1. interval_seconds > 0
2. starts_at não pode ser maior que ends_at
3. start_time e end_time devem estar no formato HH:MM
4. days_of_week deve aceitar apenas:
   - mon
   - tue
   - wed
   - thu
   - fri
   - sat
   - sun

5. Pelo menos um escopo deve existir:
   - playlist_id
   - campaign_id
   - device_id
   - media_id

6. insertion_policy deve aceitar apenas:
   - interrupt
   - wait_silence
   - fade_mix

==================================================================== 6. SERVICES OBRIGATÓRIOS
========================

Criar ou ajustar os seguintes services.

---

## 6.1. AudioSpotService

Responsável por:

- criar spot
- editar spot
- arquivar spot
- validar tenant
- validar AudioTrack
- garantir que o track pertence ao mesmo tenant
- listar spots por tenant
- impedir uso de track inexistente
- impedir uso de track de outro tenant

---

## 6.2. AudioSpotScheduleService

Responsável por:

- criar agenda de spot
- editar agenda de spot
- remover/desativar agenda
- validar tenant
- validar playlist/campaign/device/media
- validar que todos pertencem ao mesmo tenant
- validar interval_seconds
- validar data
- validar dia da semana
- validar horário
- disparar bump de versão/sync quando agenda mudar

Regra obrigatória:

Ao criar ou editar uma agenda de spot, chamar:

validate_same_tenant(...)

E depois:

bump_related_versions(schedule)

---

## 6.3. SpotResolverService

Esse é o cérebro da regra.

Criar função principal:

resolve_for_device(
tenant_id,
device_id,
now,
campaign_id=None,
playlist_id=None,
media_id=None,
)

Essa função deve:

1. Buscar schedules candidatos.
2. Filtrar por tenant.
3. Filtrar por escopo:
   - playlist
   - campaign
   - device
   - media

4. Filtrar por status do spot.
5. Filtrar por is_active da schedule.
6. Filtrar por starts_at/ends_at.
7. Filtrar por days_of_week.
8. Filtrar por start_time/end_time.
9. Validar interval_seconds.
10. Buscar último AudioPlaybackEvent do spot naquele device.
11. Verificar se o intervalo já passou.
12. Resolver insertion_policy.
13. Ordenar por priority.
14. Retornar payload limpo para o player.

Implementar funções auxiliares:

- is_schedule_active(schedule, now)
- is_within_date_range(schedule, now)
- is_within_day_of_week(schedule, now)
- is_within_time_window(schedule, now)
- has_interval_elapsed(schedule, device_id, now)
- resolve_insertion_policy(schedule)
- to_player_payload(schedule)

---

## 6.4. PlayerConfigService

Localizar o service/função que monta o payload do player.

Ajustar para incluir:

- audio_playlist
- tracks
- folder_schedules
- spot_schedules

A função deve chamar:

SpotResolverService.resolve_for_device(...)

E incluir no payload do player:

spot_schedules: [
{
id,
spot_id,
spot_name,
track_id,
file_url,
duration_seconds,
interval_seconds,
starts_at,
ends_at,
days_of_week,
start_time,
end_time,
insertion_policy,
priority,
is_active
}
]

---

## 6.5. AudioPlaybackEventService

Criar ou ajustar funções:

- register_track_started
- register_track_ended
- register_spot_started
- register_spot_ended
- register_spot_failed
- get_last_successful_spot_event

get_last_successful_spot_event deve buscar:

- device_id
- spot_id
- event_type = spot_started
- result = success

Ordenar por started_at desc e retornar o último.

Essa função é obrigatória para o interval_seconds funcionar.

---

## 6.6. Sync/Version Service

Quando um spot ou agenda mudar, incrementar versão para o player sincronizar.

Se o schedule tem playlist_id:

- incrementar AudioPlaylist.version

Se tem campaign_id:

- incrementar Campaign.campaign_version

Se tem device_id:

- incrementar Device.schedule_version

Se for uma playlist usada por dispositivos:

- garantir que os devices recebam nova configuração

Criar função:

on_spot_schedule_changed(schedule)

==================================================================== 7. REPOSITORIES
===============

Criar ou ajustar AudioSpotRepository.

Funções esperadas:

- get_spot_by_id(tenant_id, spot_id)
- list_spots(tenant_id)
- create_spot(data)
- update_spot(spot, data)
- list_candidate_schedules(tenant_id, playlist_id=None, campaign_id=None, device_id=None, media_id=None)
- get_schedule_by_id(tenant_id, schedule_id)
- get_last_successful_spot_event(device_id, spot_id)

A query de list_candidate_schedules deve carregar:

- AudioSpotSchedule
- AudioSpot
- AudioTrack
- AudioPlaylist, se houver
- Campaign, se houver
- Device, se houver
- Media, se houver

Usar joinedload/selectinload para evitar N+1.

==================================================================== 8. ENDPOINTS ADMIN
==================

Criar ou ajustar endpoints:

POST /api/v1/audio/spots
GET /api/v1/audio/spots
GET /api/v1/audio/spots/{spot_id}
PUT /api/v1/audio/spots/{spot_id}
DELETE /api/v1/audio/spots/{spot_id}

POST /api/v1/audio/spot-schedules
GET /api/v1/audio/spot-schedules
GET /api/v1/audio/spot-schedules/{schedule_id}
PUT /api/v1/audio/spot-schedules/{schedule_id}
DELETE /api/v1/audio/spot-schedules/{schedule_id}

Se o produto usa spot dentro da campanha, criar também:

POST /api/v1/campaigns/{campaign_id}/spots
GET /api/v1/campaigns/{campaign_id}/spots
PUT /api/v1/campaigns/{campaign_id}/spots/{schedule_id}
DELETE /api/v1/campaigns/{campaign_id}/spots/{schedule_id}

Se o produto usa spot dentro do device, criar também:

POST /api/v1/devices/{device_id}/spots
GET /api/v1/devices/{device_id}/spots
PUT /api/v1/devices/{device_id}/spots/{schedule_id}
DELETE /api/v1/devices/{device_id}/spots/{schedule_id}

Todos devem validar tenant.

==================================================================== 9. ENDPOINT DO PLAYER
=====================

Localizar o endpoint usado pelo player, por exemplo:

GET /api/v1/devices/{device_id}/playlist
GET /api/v1/devices/{device_id}/config
GET /api/v1/player/config
GET /api/v1/sync

Ajustar para incluir spot_schedules.

O payload final precisa conter:

{
"audio_playlist": {
"id": "...",
"tracks": [],
"folder_schedules": [],
"spot_schedules": [
{
"id": "...",
"spot_id": "...",
"spot_name": "...",
"track_id": "...",
"file_url": "...",
"duration_seconds": 30,
"interval_seconds": 600,
"starts_at": "2026-06-01T00:00:00",
"ends_at": "2026-06-30T23:59:59",
"days_of_week": ["mon", "tue", "wed", "thu", "fri"],
"start_time": "08:00",
"end_time": "18:00",
"insertion_policy": "wait_silence",
"priority": 10,
"is_active": true
}
]
}
}

==================================================================== 10. REGRA DE FILTRO DO SPOT
===========================

Implementar exatamente esta lógica:

Um spot só pode tocar se:

1. AudioSpot.status == active
2. AudioSpotSchedule.is_active == true
3. tenant_id bate com o tenant do device
4. now >= starts_at, se starts_at existir
5. now <= ends_at, se ends_at existir
6. dia atual está em days_of_week, se days_of_week existir
7. hora atual está entre start_time e end_time, se ambos existirem
8. interval_seconds > 0
9. já passou interval_seconds desde o último SPOT_STARTED com sucesso no mesmo device
10. o escopo bate com playlist/campaign/device/media

A função de horário deve suportar janela cruzando meia-noite.

Exemplo:

start_time = 22:00
end_time = 06:00

Nesse caso, 23:00 é válido e 02:00 também é válido.

==================================================================== 11. POLÍTICA DE INSERÇÃO
========================

Implementar suporte para:

interrupt:

- interrompe a música atual e toca o spot imediatamente.

wait_silence:

- espera a música atual terminar e toca o spot antes da próxima faixa.

fade_mix:

- reduz o volume da música/radio, toca o spot e depois restaura o volume.

O backend deve enviar a política no payload.
O player deve aplicar a política.

Regra de precedência:

1. schedule.insertion_policy
2. spot.insertion_policy
3. wait_silence

==================================================================== 12. TESTES OBRIGATÓRIOS
=======================

Criar testes unitários e E2E.

Testes de model/migration:

1. AudioSpotSchedule tem tenant_id.
2. AudioSpotSchedule aceita campaign_id.
3. AudioSpotSchedule aceita device_id.
4. AudioSpotSchedule aceita media_id, se implementado.
5. AudioSpotSchedule aceita playlist_id.
6. Não quebra dados legados.
7. Unique antiga não bloqueia múltiplas agendas válidas.

Testes de service:

1. Spot não toca antes de starts_at.
2. Spot não toca depois de ends_at.
3. Spot toca dentro do intervalo de datas.
4. Spot só toca no dia correto.
5. Spot não toca em dia fora de days_of_week.
6. Spot só toca dentro do horário.
7. Spot toca em janela cruzando meia-noite.
8. Spot respeita interval_seconds.
9. Spot toca se nunca houve AudioPlaybackEvent anterior.
10. Spot não toca se último evento foi recente.
11. Spot toca se intervalo já passou.
12. insertion_policy usa override da schedule.
13. insertion_policy cai para valor do spot.
14. insertion_policy cai para wait_silence como default.
15. Spot de outro tenant é bloqueado.
16. Playlist de outro tenant é bloqueada.
17. Campaign de outro tenant é bloqueada.
18. Device de outro tenant é bloqueado.
19. Media de outro tenant é bloqueada.

Testes do endpoint do player:

1. Player recebe spot_schedules.
2. Player recebe file_url do AudioTrack.
3. Player recebe interval_seconds.
4. Player recebe days_of_week.
5. Player recebe start_time/end_time.
6. Player recebe starts_at/ends_at.
7. Player recebe insertion_policy.
8. Player não recebe spots inativos.
9. Player não recebe spots fora da janela.
10. Player recebe spots ordenados por priority.

Testes de eventos:

1. register_spot_started cria AudioPlaybackEvent com event_type=spot_started.
2. register_spot_ended cria AudioPlaybackEvent com event_type=spot_ended.
3. get_last_successful_spot_event retorna último evento correto.
4. Eventos failed/skipped não contam como execução bem-sucedida para interval_seconds, salvo regra contrária.

==================================================================== 13. CRITÉRIOS DE ACEITE
=======================

A implementação só está correta se:

1. A UI conseguir criar um spot.
2. A UI conseguir agendar um spot em uma playlist.
3. A UI conseguir agendar um spot em uma campanha, se essa feature existir.
4. A UI conseguir agendar um spot em um device, se essa feature existir.
5. O backend validar tenant em todos os vínculos.
6. O backend impedir interval_seconds inválido.
7. O backend impedir data inicial maior que data final.
8. O backend impedir days_of_week inválido.
9. O endpoint do player retornar spot_schedules.
10. O player conseguir saber qual arquivo tocar.
11. O player receber insertion_policy.
12. O player ou backend respeitar interval_seconds.
13. AudioPlaybackEvent registrar SPOT_STARTED.
14. AudioPlaybackEvent registrar SPOT_ENDED.
15. O próximo cálculo de intervalo usar o último evento registrado.
16. Alterar uma agenda de spot força ressincronização do player.
17. Não existe schema mismatch entre frontend, API, banco e player.

==================================================================== 14. ENTREGÁVEIS
===============

Entregar:

1. Relatório de auditoria da estrutura atual.
2. Lista de arquivos alterados.
3. Alterações em models.py.
4. Migration Alembic.
5. Schemas Pydantic.
6. Services.
7. Repositories.
8. Endpoints admin.
9. Ajuste no endpoint do player.
10. Ajuste no payload do player.
11. Testes unitários.
12. Testes E2E.
13. Checklist final UI → API → DB → Player → Logs.

==================================================================== 15. IMPORTANTE
==============

Não fazer implementação quebrando compatibilidade.

Se existirem campos legados, manter funcionando e criar migração gradual.

Não remover JSONs ou campos antigos sem verificar onde são usados.

Não mudar contrato do player sem ajustar o frontend/player correspondente.

Não criar spot_id diretamente em devices, campaigns ou media como relação única.

A tabela central de vínculo deve ser AudioSpotSchedule.

O objetivo final é eliminar o bug:

“Spot está configurado, mas não toca.”

A causa provável desse bug é uma ou mais destas:

- UI salva em um lugar e player lê outro.
- AudioSpotSchedule não chega no payload do player.
- Player não aplica interval_seconds.
- Backend não filtra por data/dia/horário.
- Backend não registra AudioPlaybackEvent.
- Backend não incrementa version/sync.
- Tenant ou FK não estão corretamente relacionados.
- Campaign/Device/Playlist não reconhecem spot no service.
