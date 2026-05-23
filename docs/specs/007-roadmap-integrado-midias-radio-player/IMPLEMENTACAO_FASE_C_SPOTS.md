# SPEC 007 — Fase C: Audio Spots (Anúncios)

## Status: ✅ Implementado (2026-05-23)

Implementação completa de **spots de áudio** — anúncios/jingles inseridos em intervalos regulares durante a programação de rádio.

---

## O que foi implementado

### 1. Migrations

#### `audio_spots`
**Arquivo**: `backend/alembic/versions/20260523_1500_audio_spots.py`

Tabela:
- `id`, `tenant_id`, `track_id` (FK)
- `name`, `description`
- `status` (active, inactive, archived)
- `insertion_policy` (interrupt, wait_silence, fade_mix)
- timestamps

Índices: `(tenant_id)`, `(track_id)`, `(status)`

#### `audio_spot_schedules`
Vincula spot → playlist com intervalo de repetição:
- `spot_id`, `playlist_id` (FKs)
- `interval_seconds` (a cada quantos segundos tocar)
- `start_time`, `end_time` (janela de horário)
- `starts_at`, `ends_at` (período de data)
- `priority` (múltiplos spots: qual toca)
- `is_active`

Índices: `(playlist_id)`, `(spot_id)`, `(start_time, end_time)`

### 2. Modelos

**Arquivo**: `backend/core/models.py`

#### Enums
```python
class AudioSpotStatus:
    ACTIVE, INACTIVE, ARCHIVED

class AudioSpotInsertionPolicy:
    INTERRUPT      # Interrompe música (fade out rápido)
    WAIT_SILENCE   # Aguarda pausa natural
    FADE_MIX       # Mix com música (volume reduzido)
```

#### Models
- `AudioSpot` com relacionamentos: `track`, `schedules`
- `AudioSpotSchedule` com relacionamentos: `spot`, `playlist`
- AudioTrack agora tem `.spots` (um track pode ser usado em múltiplos spots)
- AudioPlaylist agora tem `.spot_schedules`

### 3. Schemas Pydantic

**Arquivo**: `backend/core/schemas_completos.py`

- `AudioSpotBase` → Create/Update/Response
- `AudioSpotScheduleBase` → Create/Update/Response
- Validações: `starts_at >= ends_at`, coerção de datas

### 4. CRUDs

- `crud_audio_spot.py`: get_by_tenant, get_by_status, search
- `crud_audio_spot_schedule.py`: 
  - `create(db, obj_in, playlist_id)` — cria com FK automática
  - `get_by_playlist`, `get_by_spot`, `get_active_by_playlist`

### 5. API Endpoints

**Arquivo**: `backend/api/v1/audio/spots.py` (novo arquivo)

#### Spots CRUD
```
GET    /audio/spots/
POST   /audio/spots/
GET    /audio/spots/{spot_id}
PUT    /audio/spots/{spot_id}
DELETE /audio/spots/{spot_id}
```

Query params:
- `search`: busca por name/description
- `status`: filtro
- `tenant_id`: para admins

#### Spot Schedules
```
GET    /audio/spots/playlists/{playlist_id}/spot-schedules
POST   /audio/spots/playlists/{playlist_id}/spot-schedules
GET    /audio/spots/playlists/{playlist_id}/spot-schedules/{schedule_id}
PUT    /audio/spots/playlists/{playlist_id}/spot-schedules/{schedule_id}
DELETE /audio/spots/playlists/{playlist_id}/spot-schedules/{schedule_id}
```

Autorização:
- Admin: acessa tudo
- User: restrito ao seu tenant
- Cache invalidation automática em Redis

### 6. Resolver de Spots

**Arquivo**: `backend/services/audio_spot_scheduler.py`

Funções principais:

#### `get_eligible_spots(db, playlist_id, now=None) → List[Tuple[AudioSpot, AudioSpotSchedule]]`
Retorna todos os spots que podem tocar **agora**, em ordem de prioridade.

Critérios:
1. Agendamento ativo
2. Dentro do período (starts_at/ends_at)
3. Dentro do horário (start_time/end_time)
4. Retorna em ordem de prioridade decrescente

#### `get_next_spot_time(db, playlist_id, current_track_started_at=None, now=None) → Optional[Tuple[datetime, AudioSpot, AudioSpotSchedule]]`
Calcula QUANDO o próximo spot deve tocar.

Baseado em `interval_seconds`: se track começou há 10s e intervalo é 30s, spot toca em +20s.

Útil para o player saber quando preparar o spot.

#### `should_retry_spot_with_fallback(db, playlist_id, now=None, attempt=0) → Optional[Tuple[AudioSpot, AudioSpotSchedule]]`
Fallback para tentar próximo spot se o primeiro falhar.

---

## Uso

### Criar spot

```python
POST /audio/spots
{
  "name": "Anúncio Matinal",
  "description": "Jingle de bom dia",
  "track_id": "uuid-jingle-track",
  "status": "active",
  "insertion_policy": "wait_silence"
}
```

### Criar agendamento

```python
POST /audio/spots/playlists/{playlist_id}/spot-schedules
{
  "spot_id": "uuid-spot",
  "interval_seconds": 1800,  # A cada 30 min
  "start_time": "06:00",     # De 6h
  "end_time": "22:00",       # Até 22h
  "priority": 5,
  "is_active": true
}
```

### Usar no player

```python
from services.audio_spot_scheduler import get_next_spot_time, get_eligible_spots

# Saber quais spots podem tocar agora
eligible_spots = get_eligible_spots(db, playlist_id="uuid")
if eligible_spots:
    spot, schedule = eligible_spots[0]  # Maior prioridade
    # Tocar `spot.track`

# Saber quando tocar o próximo
next_spot_info = get_next_spot_time(
    db,
    playlist_id="uuid",
    current_track_started_at=datetime.utcnow()
)
if next_spot_info:
    spot_time, spot, schedule = next_spot_info
    # Agendar para tocar em `spot_time`
```

---

## Insertion Policies (como inserir)

### 1. **INTERRUPT** (Interrompe)
- Fade out da música atual (200ms)
- Toca spot
- Fade in da música (resume)
- Agressivo, mas garante que spot toca

### 2. **WAIT_SILENCE** (Aguarda silêncio)
- Monitora fim natural da track
- Quando silêncio detectado, toca spot
- Menos agressivo, mas pode atrasar

### 3. **FADE_MIX** (Mix)
- Reduz volume da música para 30%
- Spot toca por cima
- Sobe volume da música de novo
- Menos perceptível, mas ambíguo

**Padrão**: `wait_silence`

---

## Cenários de Uso

### Rádio com anúncio a cada 30 min
```
08:00-22:00: Música (pasta Morning)
Spot: "Ouça a Rádio XYZ!" a cada 1800s (30min)
```

### Múltiplos spots em conflito
```
Spot 1: Anúncio (priority=10, interval=1800s)
Spot 2: Previsão do tempo (priority=5, interval=3600s)

→ Se ambos elegíveis: Spot 1 toca (maior prioridade)
→ Próximo: Spot 2
```

### Spot só em horário específico
```
Spot: "Promoção Flash" (18:00-21:00)
Playlist: Rádio com folder schedule

→ Spot só soa entre 18h-21h
```

---

## Testes (próximo passo)

Será implementado teste em `backend/tests/test_audio_spot_schedules_007.py`:

- ✅ Criar spot e agendamento
- ✅ Resolver por horário/período
- ✅ Próximo spot por intervalo
- ✅ Prioridade em conflito
- ✅ Fallback para spot alternativo

---

## Próximos passos (Fase C finalização)

- [ ] **Audio Playback Events** — log de spots tocados
- [ ] **Upload Múltiplo** — `POST /audio/tracks/upload-multiple`
- [ ] **FFprobe Backend** — duração automática

---

## Notas de design

1. **Um track pode ser spot e item de playlist**: reúso de audio.
2. **Sem sobreposição forçada**: resolver retorna lista em prioridade, player escolhe.
3. **Intervalo em segundos**: absoluto, não "a cada N tracks".
4. **Insertion policy é hint**: player pode ignorar e wait_silence sempre é seguro.
5. **Tenant isolation**: cada tenant só vê seus spots.
