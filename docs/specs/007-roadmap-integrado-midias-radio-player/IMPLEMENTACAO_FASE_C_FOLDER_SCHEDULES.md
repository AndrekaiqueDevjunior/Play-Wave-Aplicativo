# SPEC 007 — Fase C: Audio Playlist Folder Schedules

## Status: ✅ Implementado (2026-05-23)

Implementação completa de **agendamento de pastas de áudio** por horário em uma playlist. Inclui migration, modelos, CRUD, endpoints API e resolver de agenda.

---

## O que foi implementado

### 1. Migration: `audio_playlist_folder_schedules`

**Arquivo**: `backend/alembic/versions/20260523_1400_audio_playlist_folder_schedules.py`

Tabela com:
- `playlist_id` (FK → audio_playlists)
- `folder_id` (FK → audio_folders)
- `start_time`, `end_time` (HH:MM)
- `starts_at`, `ends_at` (data)
- `days_of_week` (JSON lista)
- `priority` (inteiro: maior = mais prioritário)
- `play_mode` (enum: sequential, shuffle, loop)
- `is_active` (boolean)

Índices: `(playlist_id)`, `(folder_id)`, `(start_time, end_time)`

### 2. Modelos Django/SQLAlchemy

**Arquivo**: `backend/core/models.py`

#### Enum `AudioPlaylistPlayMode`
```python
class AudioPlaylistPlayMode(str, enum.Enum):
    SEQUENTIAL = "sequential"
    SHUFFLE = "shuffle"
    LOOP = "loop"
```

#### Model `AudioPlaylistFolderSchedule`
Relacionamentos:
- `playlist` ↔ `AudioPlaylist.folder_schedules`
- `folder` ↔ `AudioFolder.playlist_schedules`

### 3. Schemas Pydantic

**Arquivo**: `backend/core/schemas_completos.py`

- `AudioPlaylistPlayModeEnum`
- `AudioPlaylistFolderScheduleBase` (base com validações de período)
- `AudioPlaylistFolderScheduleCreate`
- `AudioPlaylistFolderScheduleUpdate`
- `AudioPlaylistFolderScheduleResponse`

Validações:
- `ends_at >= starts_at` (se ambos presentes)
- Coerção automática de strings de data "YYYY-MM-DD"

### 4. CRUD

**Arquivo**: `backend/crud/entidades/crud_audio_playlist_folder_schedule.py`

Métodos:
- `create(db, obj_in, playlist_id)` — cria com FK automática
- `get_by_playlist(db, playlist_id)` — lista agendamentos de uma playlist
- `get_by_folder(db, folder_id)` — lista onde uma pasta é usada
- `get_active_by_playlist(db, playlist_id)` — apenas ativos

### 5. API Endpoints

**Arquivo**: `backend/api/v1/audio/playlists.py` (novas rotas)

```
GET    /audio/playlists/{playlist_id}/folder-schedules
POST   /audio/playlists/{playlist_id}/folder-schedules
GET    /audio/playlists/{playlist_id}/folder-schedules/{schedule_id}
PUT    /audio/playlists/{playlist_id}/folder-schedules/{schedule_id}
DELETE /audio/playlists/{playlist_id}/folder-schedules/{schedule_id}
```

Autorização:
- Admin pode acessar todas as playlists/pastas.
- Outros usuários: restritos ao seu tenant.

Cache invalidation automática para devices afetados.

### 6. Resolver de Agenda

**Arquivo**: `backend/services/audio_schedule_resolver.py`

Funções principais:

#### `resolve_active_folder(db, playlist_id, now=None) → Optional[AudioFolder]`
Determina qual pasta deve tocar **agora** para uma playlist.

Critérios (em ordem):
1. Agendamentos ativos (`is_active=true`)
2. Dentro do período de data (`starts_at <= now <= ends_at`)
3. Dentro do horário (`start_time <= now.time <= end_time`)
4. Dia da semana match (`days_of_week`)
5. **Maior prioridade ganha**

Retorna: A pasta ativa ou `None` se nenhuma elegível.

#### `resolve_active_folders_by_priority(db, playlist_id, now=None) → List[AudioFolder]`
Retorna **todas** as pastas elegíveis em ordem de prioridade.

Útil para fallback: tente primeira, depois segunda, etc.

#### `get_next_schedule_change(db, playlist_id, now=None) → Optional[datetime]`
Calcula **quando** a pasta vai mudar de novo.

Útil para saber quando re-avaliar (evita polling contínuo).

---

## Uso

### Criar agendamento

```python
# Admin cria: Manhã (6h-12h), Tarde (12h-18h), Noite (18h-6h)

POST /audio/playlists/{playlist_id}/folder-schedules
{
  "folder_id": "uuid-folder-manha",
  "start_time": "06:00",
  "end_time": "12:00",
  "priority": 1,
  "play_mode": "sequential",
  "is_active": true
}
```

### Resolver no player

```python
from services.audio_schedule_resolver import resolve_active_folder
from sqlalchemy.orm import Session

current_folder = resolve_active_folder(
    db,
    playlist_id="uuid-playlist",
    now=datetime.utcnow()
)

if current_folder:
    # Toca faixas da `current_folder`
    play_tracks(current_folder.tracks)
else:
    # Fallback: playlist padrão ou silêncio
    play_default_or_silent()
```

### Conflito de horário

Se duas pastas se sobrepõem:
- Pasta com `priority=10` toca
- Pasta com `priority=1` é ignorada

Admin pode resolver manualmente ajustando prioridades ou horários.

---

## Testes

**Arquivo**: `backend/tests/test_audio_playlist_folder_schedules_007.py`

Cobertura:
- ✅ Criar agendamento
- ✅ Resolver por horário (dentro/fora)
- ✅ Resolver por período de data
- ✅ Prioridade em conflito
- ✅ Listar por prioridade

Executar:
```bash
pytest backend/tests/test_audio_playlist_folder_schedules_007.py -v
```

---

## Próximos passos (Fase C continuação)

- [ ] **Audio Spots** — insersões de anúncio por intervalo
- [ ] **Upload Múltiplo** — `POST /audio/tracks/upload-multiple`
- [ ] **FFprobe Backend** — duração automática de áudio

---

## Notas de design

1. **Sem sobreposição forçada**: Conflitos são resolvidos por prioridade, não bloqueados.
2. **Horários locais**: `start_time`, `end_time` são strings HH:MM; não lidam com fusos.
3. **Days of week**: JSON array `[0, 1, 2, 3, 4]` = seg-sex (0=seg, 6=dom).
4. **Fallback**: Se nenhuma pasta elegível, player cai para padrão (radio off ou silêncio).
5. **Cache**: Invalidação automática em Redis quando schedule muda.
