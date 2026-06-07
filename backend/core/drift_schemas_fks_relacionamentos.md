Sim — olhando o `models.py`, o projeto já tem uma base boa, mas existem **buracos claros de relacionamento, duplicidade de fonte da verdade e risco de schema mismatch entre UI, API, banco e player**. Minha análise abaixo é uma auditoria estática em cima do arquivo enviado.

## Diagnóstico principal

O maior problema não é falta de tabela. O maior problema é que o sistema tem **duas formas de representar a mesma coisa**:

1. Campos JSON legados, como `campaign.device_ids`, `campaign.media_ids`, `campaign.media_order`, `audio_playlist.track_ids`.
2. Tabelas relacionais novas, como `campaign_playlist_items`, `audio_playlist_items`, `audio_folder_tracks`, `audio_spot_schedules`.

Isso gera exatamente o tipo de bug que você está vendo:

> A UI salva em um lugar, o backend lê outro, o player consome outro payload, e o cliente percebe que “spot não toca” ou “campanha não aparece”.

---

# Buracos críticos encontrados

## 1. `Plan` está praticamente órfã

Existe tabela `plans`, mas `Tenant.plan` é apenas um enum/string:

```py
plan = Column(SQLEnum("starter", "pro", "enterprise", name="tenant_plan"), default="starter")
```

Problema: `Tenant` não tem `plan_id = ForeignKey("plans.id")`.

### Risco

Você pode ter planos cadastrados em `plans`, mas o tenant não aponta formalmente para eles. Isso quebra limite de dispositivos, features, permissões e billing.

### Correção recomendada

Trocar para:

```py
plan_id = Column(String(50), ForeignKey("plans.id"), nullable=False, default="starter")
plan = relationship("Plan")
```

Ou remover a tabela `plans` se o plano for somente enum fixo.

---

## 2. Campanha ainda depende de JSON para dispositivos

`Campaign` tem:

```py
device_ids = Column(JSON, nullable=True)
target_groups = Column(JSON, nullable=True)
```

Mas não existe uma tabela relacional tipo:

```txt
campaign_devices
campaign_id
device_id
```

### Risco

Não existe integridade referencial. Um `device_id` pode estar no JSON mesmo se o device não existir mais, pertencer a outro tenant ou estiver bloqueado.

### Correção recomendada

Criar:

```py
class CampaignDevice(Base):
    __tablename__ = "campaign_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
```

E depois tratar `Campaign.device_ids` como legado/cache, não como fonte oficial.

---

## 3. Campanha tem mídia em JSON e também em tabela relacional

`Campaign` tem:

```py
media_ids = Column(JSON, nullable=True)
media_order = Column(JSON, nullable=True)
```

Mas também existe:

```py
CampaignPlaylistItem
```

Essa tabela já resolve melhor:

```py
campaign_id
media_id
order_index
display_duration_seconds
starts_at
ends_at
repeat_count
```

### Risco

A UI pode salvar em `campaign_playlist_items`, mas o player ainda ler `campaign.media_ids`. Ou o contrário.

Esse é um forte candidato para o bug:

> “conteúdo na campanha não passando no player”

### Correção recomendada

Definir uma regra única:

```txt
Fonte oficial da ordem e mídias da campanha = campaign_playlist_items.
campaign.media_ids e campaign.media_order = legado, não usar em novas features.
```

Depois, adaptar endpoint `/devices/{id}/playlist`, `/campaigns`, player e UI para lerem da tabela relacional.

---

## 4. Relação entre campanha e playlist de áudio está ambígua

`Campaign` tem:

```py
audio_playlist_id = ForeignKey("audio_playlists.id")
```

`Device` também tem:

```py
audio_playlist_id = ForeignKey("audio_playlists.id")
```

### Problema

Não está claro quem manda:

1. Playlist de áudio do device?
2. Playlist de áudio da campanha?
3. Default do tenant?
4. Spot schedule da playlist?

Essa ambiguidade pode explicar o problema:

> “Quando coloquei agendamento de Spot, só roda spot e não a playlist.”

### Regra que precisa existir

Sugestão de precedência:

```txt
1. Campaign.audio_playlist_id, se campanha ativa tiver playlist de áudio.
2. Device.audio_playlist_id, se campanha não definir áudio.
3. Tenant.audio_policy_default.
4. Sem áudio.
```

Ou, se rádio for sempre por ponto/device, então campanha não deveria ter `audio_playlist_id`.

Hoje o model permite os dois caminhos, mas não deixa a regra explícita.

---

## 5. Spot está ligado à playlist, não à campanha nem ao device

`AudioSpotSchedule` liga:

```py
spot_id
playlist_id
interval_seconds
start_time
end_time
starts_at
ends_at
days_of_week
```

Isso é bom se a regra for:

> Spot pertence à playlist de rádio.

Mas se a UI quer “adicionar spot no modal da campanha”, então falta uma regra clara:

```txt
Quando adiciono spot na campanha, eu estou criando schedule em qual playlist?
- Na playlist da campanha?
- Na playlist do device?
- Em uma playlist criada automaticamente?
```

### Buraco real

Não existe `campaign_spot_schedules`.

Então, se o produto quer spot por campanha, o model atual não representa isso diretamente.

### Duas opções boas

#### Opção A — manter spot por playlist

Mais simples:

```txt
Campanha seleciona uma AudioPlaylist.
SpotSchedule pertence à AudioPlaylist.
Modal da campanha apenas edita a playlist vinculada.
```

#### Opção B — criar spot por campanha

Mais explícito:

```py
class CampaignAudioSpotSchedule(Base):
    __tablename__ = "campaign_audio_spot_schedules"

    campaign_id = ForeignKey("campaigns.id", ondelete="CASCADE")
    spot_id = ForeignKey("audio_spots.id", ondelete="CASCADE")
    interval_seconds = Column(Integer, nullable=False)
    start_time = Column(String(10), nullable=True)
    end_time = Column(String(10), nullable=True)
    days_of_week = Column(JSON, nullable=True)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
```

Para o seu caso, eu recomendaria **Opção A** se rádio é entidade independente. Recomendaria **Opção B** se spot é comercial/agendamento vinculado à campanha.

---

# Relacionamentos faltando ou fracos

## 6. `Location` não está conectada de verdade com `Device`

Existe tabela:

```py
Location
```

Mas `Device` tem:

```py
location = Column(String(255), nullable=True)
group = Column(String(255), nullable=True)
```

Não existe:

```py
location_id = ForeignKey("locations.id")
```

### Risco

Você tem tabela de locais, mas o device usa texto solto. Isso quebra filtros, relatórios, agrupamento e contagem real.

### Correção

Adicionar:

```py
location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
location_ref = relationship("Location", back_populates="devices")
```

E em `Location`:

```py
devices = relationship("Device", back_populates="location_ref")
```

---

## 7. `Device.current_audio_track_id` não tem ForeignKey

Hoje:

```py
current_audio_track_id = Column(UUID(as_uuid=True), nullable=True)
```

Deveria ser:

```py
current_audio_track_id = Column(UUID(as_uuid=True), ForeignKey("audio_tracks.id"), nullable=True)
current_audio_track = relationship("AudioTrack")
```

### Risco

O device pode apontar para um áudio inexistente.

---

## 8. `Media.created_by`, `updated_by` e `MediaVersion.created_by` têm FK, mas não têm relationship

Hoje existem FKs para `users.id`, mas sem ORM relationship.

### Correção

```py
created_by_user = relationship("User", foreign_keys=[created_by])
updated_by_user = relationship("User", foreign_keys=[updated_by])
```

Em `MediaVersion`:

```py
created_by_user = relationship("User", foreign_keys=[created_by])
```

---

## 9. `UserLog.target_user_id` tem FK, mas não tem relationship

Hoje:

```py
target_user_id = ForeignKey("users.id")
```

Mas falta:

```py
target_user = relationship("User", foreign_keys=[target_user_id])
```

---

## 10. `DeviceSession`, `DevicePairingCode`, `DeviceCommand`, `DevicePairingEvent` não estão totalmente conectados ao `Tenant`

Algumas têm `tenant_id`, mas `Tenant` não tem relationships correspondentes.

Faltam no `Tenant`:

```py
audio_categories = relationship("AudioCategory", back_populates="tenant")
audio_spots = relationship("AudioSpot", back_populates="tenant")
device_sessions = relationship("DeviceSession", back_populates="tenant")
device_commands = relationship("DeviceCommand", back_populates="tenant")
device_pairing_codes = relationship("DevicePairingCode", back_populates="tenant")
device_pairing_events = relationship("DevicePairingEvent", back_populates="tenant")
```

E nas classes filhas, padronizar `back_populates`.

---

# Problemas de integridade multi-tenant

Esse é um ponto muito importante.

Quase tudo tem `tenant_id`, mas muitos `tenant_id` são `nullable=True`.

Exemplos:

```py
Device.tenant_id nullable=True
Campaign.tenant_id nullable=True
Media.tenant_id nullable=True
AudioTrack.tenant_id nullable=True
AudioPlaylist.tenant_id nullable=True
AudioFolder.tenant_id nullable=True
```

### Risco

Você pode criar:

```txt
Campaign do Tenant A
com Media do Tenant B
tocando no Device do Tenant C
```

O banco não impede isso.

### Correção ideal

Para entidades operacionais, deixar `tenant_id` obrigatório:

```py
tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
```

Principalmente em:

```txt
devices
campaigns
media
audio_tracks
audio_playlists
audio_folders
audio_spots
playback_logs
view_reports
device_events
device_commands
```

Também precisa validação na service layer:

```txt
campaign.tenant_id == media.tenant_id
campaign.tenant_id == device.tenant_id
playlist.tenant_id == track.tenant_id
spot.tenant_id == playlist.tenant_id
folder.tenant_id == playlist.tenant_id
```

---

# Problemas de duplicidade de fonte da verdade

## 11. `AudioPlaylist.track_ids` duplica `AudioPlaylistItem`

`AudioPlaylist` tem:

```py
track_ids = Column(JSON, nullable=True)
track_volumes = Column(JSON, nullable=True)
```

Mas também tem:

```py
AudioPlaylistItem
```

### Recomendação

Fonte oficial:

```txt
audio_playlist_items
```

Campos JSON devem virar legado/cache.

---

## 12. `AudioTrack.category` e `AudioTrack.category_id` duplicam conceito

Existe:

```py
category = Enum(AudioTrackCategory)
category_id = ForeignKey("audio_categories.id")
```

Isso pode fazer sentido se `category` for categoria padrão e `category_id` for categoria customizada. Mas precisa regra explícita.

### Regra recomendada

```txt
category = categoria sistêmica/base.
category_id = categoria customizada opcional do tenant.
```

Ou remover o enum e usar só tabela `audio_categories`.

---

## 13. `Media.duration` e `Media.duration_seconds` duplicam

Existe:

```py
duration
duration_seconds
```

### Risco

Um endpoint atualiza um campo, outro endpoint lê o outro.

### Recomendação

Manter só:

```py
duration_seconds
```

E migrar `duration` como legado.

---

## 14. `Device.current_campaign` e `Device.current_campaign_id` duplicam

Existe:

```py
current_campaign = Column(String)
current_campaign_id = ForeignKey("campaigns.id")
```

### Risco

O nome da campanha pode mudar e `current_campaign` ficar desatualizado.

### Recomendação

Usar `current_campaign_id` como fonte oficial. `current_campaign` deve ser cache ou removido.

---

## 15. `Device.audio_playlist_name` duplica `audio_playlist_id`

Mesmo problema:

```py
audio_playlist_name = Column(String)
audio_playlist_id = ForeignKey("audio_playlists.id")
```

Melhor buscar o nome pela relationship.

---

# Constraints que estão faltando

Hoje existem poucos `UniqueConstraint`. Faltam constraints importantes.

## Recomendo adicionar validações para:

```txt
interval_seconds > 0
volume_default >= 0 and volume_default <= 1
audio_volume >= 0 and audio_volume <= 1
volume_override >= 0 and volume_override <= 1
osd_opacity >= 0 and osd_opacity <= 1
duration_seconds >= 0
display_duration_seconds >= 0
repeat_count >= 1
priority >= 0
starts_at <= ends_at
```

Também precisa validar horários:

```txt
start_time formato HH:MM
end_time formato HH:MM
```

Melhor ainda: trocar `String(10)` por `Time`.

---

# Problema específico em `AudioSpotSchedule`

Hoje existe:

```py
UniqueConstraint("spot_id", "playlist_id")
```

Isso impede o mesmo spot de ter mais de um agendamento dentro da mesma playlist.

### Exemplo que quebra

```txt
Spot X na Playlist Y
- tocar de manhã a cada 10 min
- tocar à tarde a cada 20 min
```

O banco não deixa, porque `spot_id + playlist_id` já existe.

### Correção

Trocar para uma constraint mais flexível ou remover.

Sugestão:

```py
UniqueConstraint(
    "spot_id",
    "playlist_id",
    "start_time",
    "end_time",
    "starts_at",
    "ends_at",
    name="uq_audio_spot_schedule_window"
)
```

Ou permitir múltiplos schedules e controlar conflito por service.

---

# Falhas de relacionamento ORM

Alguns relacionamentos têm `back_populates` de um lado, mas não do outro.

Exemplo:

```py
Device.campaign = relationship(..., back_populates="devices")
Campaign.devices = relationship(...)
```

O ideal seria:

```py
Campaign.devices = relationship(
    "Device",
    foreign_keys=[Device.current_campaign_id],
    back_populates="campaign"
)
```

Outro exemplo:

```py
Device.audio_playlist = relationship(..., back_populates="devices")
AudioPlaylist.devices = relationship(...)
```

Melhor:

```py
AudioPlaylist.devices = relationship(
    "Device",
    foreign_keys=[Device.audio_playlist_id],
    back_populates="audio_playlist"
)
```

---

# Problema de eventos não registrados

Dentro de `Device` existem:

```py
before_insert
before_update
```

Mas no arquivo não aparece registro com:

```py
event.listen(Device, "before_insert", Device.before_insert)
event.listen(Device, "before_update", Device.before_update)
```

### Risco

Esses métodos podem nunca executar.

Se eles estão registrados em outro arquivo, ok. Se não estiverem, eles são código morto.

---

# Resumo dos principais ajustes por prioridade

## Prioridade 1 — Corrigir fonte da verdade

Definir oficialmente:

```txt
Campanha -> mídias:
usar campaign_playlist_items.

Campanha -> devices:
criar campaign_devices.

Playlist de áudio -> músicas:
usar audio_playlist_items.

Pastas de áudio -> músicas:
usar audio_folder_tracks.

Spots:
usar audio_spot_schedules, mas definir se pertence à playlist ou à campanha.
```

## Prioridade 2 — Corrigir relações faltantes

Adicionar ou padronizar:

```txt
Tenant -> AudioCategory
Tenant -> AudioSpot
Tenant -> DeviceSession
Tenant -> DeviceCommand
Tenant -> DevicePairingCode
Tenant -> DevicePairingEvent

Device -> Location
Device -> current_audio_track

User -> Media.created_by
User -> Media.updated_by
User -> MediaVersion.created_by
User -> UserLog.target_user
```

## Prioridade 3 — Remover ambiguidade de rádio/spot

Definir a arquitetura:

```txt
Rádio é por device?
Rádio é por campanha?
Rádio é por tenant?
Spot é da playlist ou da campanha?
```

Sem essa decisão, qualquer correção vira gambiarra.

Minha recomendação para PlayWave:

```txt
AudioPlaylist = rádio.
AudioFolder = bloco/faixa por horário.
AudioPlaylistFolderSchedule = agenda de pastas.
AudioSpot = vinheta/propaganda.
AudioSpotSchedule = regra de inserção do spot na rádio.
Campaign = vídeo/imagem/mídia visual.
Campaign.audio_playlist_id = opcional, só se a campanha quiser sobrescrever a rádio do device.
```

---

# Metodologia para validar esse model de verdade

## 1. Criar uma matriz de fonte da verdade

Tabela simples:

| Domínio             | Fonte oficial                     | Campo legado                                 |
| ------------------- | --------------------------------- | -------------------------------------------- |
| Mídias da campanha  | `campaign_playlist_items`         | `campaign.media_ids`, `campaign.media_order` |
| Devices da campanha | `campaign_devices`                | `campaign.device_ids`                        |
| Músicas da playlist | `audio_playlist_items`            | `audio_playlist.track_ids`                   |
| Pastas da playlist  | `audio_playlist_folder_schedules` | nenhum                                       |
| Spots               | `audio_spot_schedules`            | nenhum                                       |
| Local do device     | `device.location_id`              | `device.location` string                     |

---

## 2. Fazer validação E2E por fluxo

Para cada feature, validar:

```txt
UI salva payload
API recebe schema correto
Service grava nas tabelas certas
Banco mantém FK válida
Endpoint do player retorna o mesmo dado
Player executa
Log confirma execução
```

Exemplo para spot:

```txt
Criar música
Criar playlist
Adicionar música na playlist
Criar spot
Criar schedule do spot a cada X minutos
Associar playlist ao device/campanha
Buscar config do player
Verificar se payload contém:
- tracks
- folders
- spot_schedules
- interval_seconds
- start_time/end_time
- days_of_week
```

---

## 3. Criar testes de integridade relacional

Casos obrigatórios:

```txt
Não permitir campaign com media de outro tenant.
Não permitir campaign com device de outro tenant.
Não permitir playlist com track de outro tenant.
Não permitir spot com track de outro tenant.
Não permitir spot_schedule com spot e playlist de tenants diferentes.
Não permitir interval_seconds <= 0.
Não permitir volume fora de 0..1.
Não permitir starts_at maior que ends_at.
```

---

## 4. Criar auditoria SQL para dados existentes

Rodar queries para descobrir sujeira no banco:

```sql
-- Campaign com media_ids JSON legado
SELECT id, name, media_ids, media_order
FROM campaigns
WHERE media_ids IS NOT NULL OR media_order IS NOT NULL;

-- Playlist usando track_ids legado
SELECT id, name, track_ids
FROM audio_playlists
WHERE track_ids IS NOT NULL;

-- Device com current_audio_track_id sem FK real
SELECT id, name, current_audio_track_id
FROM devices
WHERE current_audio_track_id IS NOT NULL;

-- Devices com location string mas sem location_id futuro
SELECT id, name, location
FROM devices
WHERE location IS NOT NULL;
```

---

# Prompt pronto para mandar para IA/Codex

```txt
Você é um arquiteto backend especialista em FastAPI, SQLAlchemy, PostgreSQL, Alembic e modelagem multi-tenant.

Audite o arquivo de models SQLAlchemy do projeto PlayWave e faça uma validação completa de:

1. Relacionamentos ausentes entre tabelas.
2. ForeignKeys existentes sem relationship ORM.
3. Relationships sem back_populates correspondente.
4. Campos JSON que duplicam tabelas normalizadas.
5. Tabelas órfãs ou subutilizadas.
6. Riscos de inconsistência multi-tenant.
7. Campos duplicados que podem virar fontes diferentes da verdade.
8. Constraints ausentes.
9. Cascades/ondelete inconsistentes.
10. Impacto específico nas features:
   - Campanha com mídias ordenadas.
   - Campanha associada a devices.
   - Rádio por playlist.
   - Pastas de áudio por horário.
   - Spots a cada X minutos.
   - Spot não tocando.
   - Player consumindo config de campanha/rádio.

Regras do trabalho:

- Não faça refatoração destrutiva sem plano de migração.
- Preserve compatibilidade com dados legados.
- Proponha migrations Alembic.
- Proponha testes unitários e E2E.
- Defina uma fonte da verdade para cada domínio.
- Aponte exatamente quais models precisam ser alterados.
- Gere uma checklist final de validação UI -> API -> DB -> Player.

Entregue em formato SPEC DRIVEN DEVELOPMENT com:

1. Problema.
2. Estado atual.
3. Estado desejado.
4. Invariantes de banco.
5. Alterações nos models.
6. Migrations necessárias.
7. Alterações nos schemas Pydantic.
8. Alterações nos services.
9. Alterações nos endpoints.
10. Testes obrigatórios.
11. Critérios de aceite.
```

---

Minha conclusão: **o model está no meio de uma migração de arquitetura**, com partes novas bem melhores, mas ainda convivendo com campos legados. Antes de tentar resolver “spot não toca” só no frontend ou só no player, eu corrigiria a fonte da verdade de campanha, playlist, spot e device. Isso provavelmente elimina a maior parte dos bugs intermitentes.
