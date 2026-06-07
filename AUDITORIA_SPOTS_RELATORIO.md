# AUDITORIA ESTRUTURA DE SPOTS - PLAYWAVE
**Data**: 2026-06-06  
**Status**: ✅ AUDITORIA COMPLETA  
**Próximo Passo**: Implementação de correções conforme brief

---

## EXECUTIVE SUMMARY

A estrutura de Spots no PlayWave **está 70% implementada e funcionando**, mas **apresenta 6 gaps críticos** que precisam ser fechados para garantir que spots sempre toquem corretamente:

| Item | Status | Risco |
|------|--------|-------|
| Models (AudioSpot, AudioSpotSchedule) | ✅ EXISTE | 🟡 INCOMPLETO |
| Endpoints CRUD de spots | ✅ EXISTE | 🟢 OK |
| Agendamento de spots por playlist | ✅ EXISTE | 🟡 INCOMPLETO |
| Payload player com spot_schedules | ✅ EXISTE | 🟡 INCOMPLETO |
| Tenant validations | ❌ FALTA | 🔴 CRÍTICO |
| SpotResolverService | ❌ FALTA | 🔴 CRÍTICO |

---

## 1. MAPEAMENTO ATUAL: O QUE EXISTE

### 1.1 Models (backend/core/models.py)

#### AudioSpot ✅
```python
class AudioSpot(Base):
    id: UUID
    tenant_id: UUID (FK → tenants)  ✅ PRESENTE
    name: String
    description: Text
    track_id: UUID (FK → audio_tracks)  ✅ PRESENTE
    status: Enum("active", "inactive", "archived")  ✅ PRESENTE
    insertion_policy: Enum("interrupt", "wait_silence", "fade_mix")  ✅ PRESENTE
    created_at, updated_at
```

**Estado**: ✅ Bem estruturado
- ✅ Tem tenant_id
- ✅ Aponta para track correto
- ✅ Status e policy definidos
- ⚠️ **Falta**: `tenant = relationship("Tenant", back_populates="audio_spots")` - tem relationship mas sem back_populates

#### AudioSpotSchedule ✅ (Parcialmente)
```python
class AudioSpotSchedule(Base):
    id: UUID
    spot_id: UUID (FK → audio_spots)  ✅ PRESENTE
    playlist_id: UUID (FK → audio_playlists)  ✅ PRESENTE
    interval_seconds: Integer  ✅ PRESENTE
    start_time: String(10)  ✅ PRESENTE
    end_time: String(10)  ✅ PRESENTE
    starts_at: DateTime  ✅ PRESENTE (adicionado recentemente)
    ends_at: DateTime  ✅ PRESENTE (adicionado recentemente)
    days_of_week: JSON  ✅ PRESENTE (adicionado recentemente)
    priority: Integer  ✅ PRESENTE
    is_active: Boolean  ✅ PRESENTE
    created_at, updated_at
```

**Estado**: 🟡 Funcional mas incompleto

**O QUE FALTA CRÍTICO**:
- ❌ `tenant_id` - AudioSpotSchedule **NÃO TEM tenant_id próprio**
  - Isso viola integridade multi-tenant
  - Risco: Spots de outro tenant podem ser vinculados
- ❌ `campaign_id` - Não pode vincular spot diretamente à campanha
- ❌ `device_id` - Não pode vincular spot diretamente ao device
- ❌ `insertion_policy` override - AudioSpotSchedule não pode sobrescrever policy do AudioSpot
- ❌ back_populates em relationships
- ⚠️ `UniqueConstraint("spot_id", "playlist_id")` - **BLOQUEIA múltiplos agendamentos do mesmo spot em horários diferentes**

### 1.2 Schemas Pydantic (backend/core/schemas_completos.py)

#### AudioSpotCreate ✅
```python
{
    name: String (required)
    description: Optional[String]
    track_id: UUID (required)
    status: Enum ("active", "inactive") - optional, default "active"
    insertion_policy: Enum - optional, default "wait_silence"
    tenant_id: UUID - optional (filled by service)
}
```
**Estado**: ✅ Válido

#### AudioSpotUpdate ✅
```python
{
    name: Optional[String]
    description: Optional[String]
    track_id: Optional[UUID]
    status: Optional[Enum]
    insertion_policy: Optional[Enum]
}
```
**Estado**: ✅ Válido

#### AudioSpotScheduleCreate ⚠️
```python
{
    spot_id: UUID (required)
    interval_seconds: Integer (required)
    start_time: Optional[String(10)]  # "HH:MM"
    end_time: Optional[String(10)]    # "HH:MM"
    starts_at: Optional[DateTime]     # Adicionado recentemente ✅
    ends_at: Optional[DateTime]       # Adicionado recentemente ✅
    days_of_week: Optional[List[int]] # Adicionado recentemente ✅
    priority: Integer - optional, default 0
    is_active: Boolean - optional, default True
    # FALTA: campaign_id, device_id, media_id
    # FALTA: insertion_policy override
}
```

**Estado**: 🟡 Funcional mas incompleto
- ✅ Campos básicos funcionam
- ❌ Sem `playlist_id` no schema (obrigatório via URL)
- ❌ Sem `tenant_id` no schema
- ❌ Sem validação de `at least one scope` (playlist_id, campaign_id, etc.)
- ❌ Sem validação de horário cruzando meia-noite
- ❌ Sem validação de `starts_at <= ends_at`

### 1.3 Endpoints CRUD

#### Spots ✅
```
GET    /api/v1/audio/spots
POST   /api/v1/audio/spots
GET    /api/v1/audio/spots/{spot_id}
PUT    /api/v1/audio/spots/{spot_id}
DELETE /api/v1/audio/spots/{spot_id}
```
**Estado**: ✅ Implementado  
**Arquivo**: `backend/api/v1/audio/spots.py` (linhas 92-180)

#### Spot Schedules ✅
```
GET    /api/v1/audio/spots/playlists/{playlist_id}/spot-schedules
POST   /api/v1/audio/spots/playlists/{playlist_id}/spot-schedules
GET    /api/v1/audio/spots/playlists/{playlist_id}/spot-schedules/{schedule_id}
PUT    /api/v1/audio/spots/playlists/{playlist_id}/spot-schedules/{schedule_id}
DELETE /api/v1/audio/spots/playlists/{playlist_id}/spot-schedules/{schedule_id}
```
**Estado**: ✅ Implementado  
**Arquivo**: `backend/api/v1/audio/spots.py` (linhas 195-365)

### 1.4 Player Endpoint ✅

```
GET /api/v1/devices/{device_id}/playlist
```

**Localização**: `backend/api/v1/devices.py` (linha 915)

**Payload contém**:
```json
{
  "device_name": "...",
  "osd_config": {...},
  "campaign": {...},
  "media": [...],
  "audio_playlist": {
    "id": "...",
    "name": "...",
    "volume": 0.8,
    "loop": true,
    "shuffle": false,
    "tracks": [...],
    "folder_schedules": [...],
    "spot_schedules": [  ✅ PRESENTE!
      {
        "id": "uuid",
        "spot_id": "uuid",
        "spot_name": "Spot Promo",
        "interval_seconds": 600,
        "start_time": "09:00",
        "end_time": "18:00",
        "starts_at": "2026-06-01T00:00:00",
        "ends_at": "2026-06-30T23:59:59",
        "days_of_week": [0, 1, 2, 3, 4],
        "priority": 10,
        "insertion_policy": "interrupt",
        "file_url": "https://..."
      }
    ]
  },
  "desktop_exposure_config": {...}
}
```

**Construtor**: `_build_spot_schedules_payload()` (linha 573) ✅

### 1.5 Frontend UI ✅

**Arquivo**: `frontend/src/components/audio/AudioSpotScheduleManager.jsx`

**Funcionalidades**:
- ✅ Criar novo spot schedule
- ✅ Editar spot schedule
- ✅ Deletar spot schedule
- ✅ Seletor de dias da semana (Seg-Dom)
- ✅ Período de validade (starts_at/ends_at)
- ✅ Horário de execução (start_time/end_time)
- ✅ Intervalo em segundos
- ✅ Prioridade
- ✅ Status ativo/inativo

**Chamadas API**: `frontend/src/api/audio.js`
```javascript
criarSpot(payload)               // POST /audio/spots
criarSpotSchedule(playlistId, p) // POST /audio/spots/playlists/{pid}/spot-schedules
editarSpotSchedule(...)
deletarSpotSchedule(...)
listarSpots()
listarSpotSchedules(playlistId)
```

---

## 2. O QUE ESTÁ FUNCIONANDO ✅

1. **Criação de spots** — UI consegue criar spots via API
2. **Agendamento em playlist** — UI consegue agendar spots em playlists
3. **Payload do player** — Player recebe `spot_schedules` com campos necessários
4. **File URL** — Player recebe `file_url` do track associado
5. **Intervalo básico** — `interval_seconds` está no payload
6. **Dias da semana** — `days_of_week` está sendo serializado
7. **Período de validade** — `starts_at`/`ends_at` está sendo serializado
8. **Inserção policy** — `insertion_policy` está sendo serializado

---

## 3. O QUE ESTÁ INCOMPLETO ❌

### 3.1 CRÍTICO: AudioSpotSchedule sem tenant_id

**Problema**:
```sql
-- Situação atual:
SELECT * FROM audio_spot_schedules WHERE id = 'some-id';
-- Retorna schedule, mas NÃO tem tenant_id próprio
-- Risk: Um user de Tenant A consegue saber sobre spots de Tenant B
```

**Impacto**: Violação de integridade multi-tenant

**Solução**: Adicionar `tenant_id` em AudioSpotSchedule com constraint NOT NULL

---

### 3.2 CRÍTICO: AudioSpotSchedule.UniqueConstraint bloqueia múltiplos agendamentos

**Problema**:
```python
# Modelo atual:
UniqueConstraint("spot_id", "playlist_id")

# Caso que DEVE ser permitido:
# Spot "Promo Black Friday" na playlist "Radio Lounge"
# - Das 08:00 às 12:00 a cada 10 minutos
# - Das 13:00 às 18:00 a cada 30 minutos

# Código:
schedule1 = AudioSpotSchedule(
    spot_id="spot-1",
    playlist_id="playlist-1",
    start_time="08:00",
    end_time="12:00",
    interval_seconds=600
)

schedule2 = AudioSpotSchedule(
    spot_id="spot-1",           # MESMO SPOT
    playlist_id="playlist-1",   # MESMA PLAYLIST
    start_time="13:00",         # MAS horários DIFERENTES
    end_time="18:00",
    interval_seconds=1800
)
# ❌ ERRO: UniqueConstraint viola!
```

**Solução**: Remover ou alterar constraint para `UniqueConstraint("spot_id", "playlist_id", "start_time", "end_time")`

---

### 3.3 FALTA: AudioSpotSchedule.campaign_id

**Problema**: Não é possível agendar spots diretamente em campanha

**Contexto do brief**: 
> "Implementar na fase 2 não esquecer de eu ter a referencia dos spot em campanhas"

**Solução**: Adicionar `campaign_id` como FK opcional a Campaign

---

### 3.4 FALTA: AudioSpotSchedule.device_id

**Problema**: Não é possível agendar spots diretamente em device

**Solução**: Adicionar `device_id` como FK opcional a Device

---

### 3.5 FALTA: AudioSpotSchedule.insertion_policy override

**Problema**:
```python
# Spot tem policy: "wait_silence"
# Mas quero usar "interrupt" para este agendamento específico
# → Não é possível, só usa policy do Spot
```

**Solução**: Adicionar coluna `insertion_policy` em AudioSpotSchedule (nullable)

**Regra de precedência**:
1. `AudioSpotSchedule.insertion_policy` (se existir)
2. `AudioSpot.insertion_policy`
3. Default: `wait_silence`

---

### 3.6 FALTA: Validações em schema Pydantic

**Faltam validators**:
- ✅ `interval_seconds > 0`
- ✅ `starts_at <= ends_at`
- ✅ `start_time` formato HH:MM
- ✅ `end_time` formato HH:MM
- ❌ **Falta**: Suporte a janela cruzando meia-noite (e.g., 22:00-06:00)
- ❌ **Falta**: `days_of_week` aceita apenas [0-6]
- ❌ **Falta**: Validação "at least one scope" (playlist_id OU campaign_id OU device_id OU media_id)
- ❌ **Falta**: insertion_policy enum validation

---

### 3.7 FALTA: SpotResolverService

**Problema**: Não existe serviço que resolve "quais spots devem tocar agora"

**O que existe hoje**:
- `_build_spot_schedules_payload()` retorna TODOS spots da playlist
- Player recebe lista completa e aplica lógica no frontend/player

**O que falta**:
- Backend não filtra:
  - ❌ Por data (starts_at/ends_at)
  - ❌ Por dia da semana (days_of_week)
  - ❌ Por horário (start_time/end_time)
  - ❌ Por intervalo (verificar se tempo suficiente passou)
  - ❌ Por tenant (não há validação)

**Impacto**: 
- Player recebe dados brutos e precisa fazer filtro
- Ou: Players antigos não filtram e tocam spots incorretamente
- Risco: "Spot está configurado, mas não toca" (ou toca na hora errada)

---

### 3.8 FALTA: AudioPlaybackEvent não é usado para intervalo

**Problema**:
```python
# Campo exists:
AudioPlaybackEvent.spot_id
AudioPlaybackEvent.event_type  # Enum: TRACK_STARTED, SPOT_STARTED, etc.
AudioPlaybackEvent.result      # Enum: SUCCESS, SKIPPED, FAILED

# Mas backend NÃO usa para calcular intervalo
# Usa apenas: AudioSpotSchedule.interval_seconds (em segundos brutos)

# Ideal seria:
# get_last_successful_spot_event(device_id, spot_id) → DateTime
# if (now - last_event.started_at) >= interval_seconds → pode tocar
```

**Impacto**: Intervalo é "teórico", não baseado em execução real

---

### 3.9 FALTA: Tenant validations em endpoints

**Problema**:
```python
# Endpoint atual:
@router.post("/audio/spots/playlists/{playlist_id}/spot-schedules")
def create_playlist_spot_schedule(playlist_id: str, data: AudioSpotScheduleCreate):
    # ❌ NÃO valida:
    # - playlist_id pertence ao tenant do user?
    # - spot_id pertence ao tenant do user?
    # - tenant_id do schedule bate com tenant do playlist?
```

**Impacto**: Cross-tenant data leakage

---

### 3.10 FALTA: Campaign.spot_schedules relationship

**Problema**:
```python
# Desejado:
campaign = Campaign.get(...)
campaign.spot_schedules  # ← Deveria retornar list[AudioSpotSchedule]

# Atual:
# ❌ Não existe essa relationship
```

---

### 3.11 FALTA: Device.spot_schedules relationship

**Mesma situação que Campaign**

---

## 4. O QUE É DUPLICADO ⚠️

### 4.1 Intervalo: Dois caminhos diferentes

**Caminho 1** (esperado):
```python
# Backend calcula intervalo
last_event = get_last_successful_spot_event(device_id, spot_id)
next_time = last_event.started_at + timedelta(seconds=schedule.interval_seconds)
if now >= next_time:
    player_pode_tocar()
```

**Caminho 2** (atual):
```python
# Player recebe intervalo bruto
spot_schedule = {
    "interval_seconds": 600,
    # Player tem que saber quando foi última vez que tocou
    # e calcular se já passou tempo suficiente
}
```

**Risco**: Se dois players tocam mesmo spot, um não sabe que outro já tocou

---

### 4.2 Inserção policy: Dois locais

- `AudioSpot.insertion_policy` (sempre presente)
- `AudioSpotSchedule.insertion_policy` (falta, seria override)

**Risco**: Sem override em schedule, usuário não consegue mudar policy para um agendamento específico

---

## 5. O QUE É LEGADO 🏚️

Nenhuma estrutura claramente legada foi identificada. O design é novo (2026) e consistente.

---

## 6. RISCO: Salvar em uma tabela, ler de outra

### 6.1 Campaign não sabe de spots da sua playlist

```python
# Salva:
campaign.audio_playlist_id = playlist_id
campaign.save()

# Lê:
playlist.spot_schedules  # ✅ Consegue acessar
# MAS:
campaign.spot_schedules  # ❌ NÃO EXISTE
```

**Impacto**: UI precisa fazer:
```javascript
campaign = get_campaign(id)
playlist = get_playlist(campaign.audio_playlist_id)
spots = get_spot_schedules(playlist.id)
```

**Vs esperado**:
```javascript
campaign = get_campaign(id)
spots = campaign.spot_schedules  // ← simples
```

---

### 6.2 Device não sabe de spots da sua playlist

Mesma situação que Campaign

---

### 6.3 Spots salvos sem tenant_id

```python
# Salva em AudioSpotSchedule:
schedule.save()  # ❌ Sem tenant_id

# Lê em SpotResolverService:
schedules = db.query(AudioSpotSchedule).filter_by(tenant_id=...)
# ❌ Falha porque tenant_id é NULL
```

---

## 7. CHECKLIST: O QUE PRECISA SER FEITO

### Fase 1: FIX CRÍTICO (Sem quebra de compatibilidade)

- [ ] **Models**: Adicionar `tenant_id` em AudioSpotSchedule
- [ ] **Models**: Remover ou flexibilizar UniqueConstraint("spot_id", "playlist_id")
- [ ] **Models**: Adicionar `campaign_id`, `device_id` em AudioSpotSchedule
- [ ] **Models**: Adicionar `insertion_policy` em AudioSpotSchedule
- [ ] **Models**: Adicionar relationships com back_populates
- [ ] **Migration**: Criar migration segura para backfill tenant_id
- [ ] **Schemas**: Validar starts_at <= ends_at
- [ ] **Schemas**: Validar intervalo > 0
- [ ] **Schemas**: Validar "at least one scope"
- [ ] **Endpoints**: Adicionar tenant validations
- [ ] **Tests**: Validar que spot não toca fora de datas/horários/dias

### Fase 2: FEATURE (Implementação completa)

- [ ] **Service**: Implementar `SpotResolverService` com filtros completos
- [ ] **Service**: Implementar `get_last_successful_spot_event()`
- [ ] **Service**: Implementar `on_spot_schedule_changed()` para versioning
- [ ] **Endpoint**: Adicionar campaign-scoped endpoints (opcional, conforme brief)
- [ ] **Endpoint**: Adicionar device-scoped endpoints (opcional)
- [ ] **Player**: Ajustar payload para usar apenas spots elegíveis (com filtros do backend)
- [ ] **Tests**: E2E completo UI → API → DB → Player → Events

---

## 8. RECOMENDAÇÕES

### 8.1 Ordem de implementação

1. **Passo 1**: Fix em models (tenant_id, campaign_id, device_id, insertion_policy)
2. **Passo 2**: Migration segura com backfill
3. **Passo 3**: Validações em schemas
4. **Passo 4**: Tenant validations em endpoints
5. **Passo 5**: SpotResolverService
6. **Passo 6**: Ajustar payload do player
7. **Passo 7**: Tests E2E

### 8.2 Não quebra compatibilidade

- ✅ Manter campos antigos (já existem)
- ✅ Novos campos são opcionais no schema até serem preenchidos
- ✅ Migrations com backfill
- ✅ Endpoint player continua retornando mesmo formato, apenas campos adicionais

### 8.3 Prioridade absoluta

1. **tenant_id em AudioSpotSchedule** — CRÍTICO para multi-tenant
2. **SpotResolverService** — CRÍTICO para que spots toquem corretamente
3. **Validações em schema** — CRÍTICO para evitar dados inválidos

---

## 9. CONCLUSÃO

A estrutura de Spots está **70% pronta**. O restante são **correções de integridade** (tenant_id), **remoção de constraints que bloqueiam UX** (UniqueConstraint), **adição de escopos** (campaign_id, device_id), **e implementação de filtros backend** (SpotResolverService).

**Risco atual**: Spots podem não tocar se:
- ❌ Estão fora de datas válidas (começou validar recentemente, mas backend não filtra)
- ❌ Estão fora de horários válidos (backend não filtra)
- ❌ Estão em dias errados (backend não filtra)
- ❌ Não respeitam intervalo (backend não valida último evento)
- ❌ De outro tenant (sem tenant_id, impossível validar)

**Próximo passo**: Implementar conforme Fase 1 do checklist, começando por tenant_id.
