# SPEC 006 — Banco

## Migration: `2026XXXX_osd_config.py`

### Enum

```sql
CREATE TYPE osd_position_enum AS ENUM (
    'top_left', 'top_right', 'bottom_left', 'bottom_right'
);

CREATE TYPE osd_font_size_enum AS ENUM (
    'small', 'medium', 'large'
);
```

### `tenants` — defaults globais (NOT NULL com defaults)

```sql
ALTER TABLE tenants
    ADD COLUMN osd_show_current_audio BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN osd_position osd_position_enum NOT NULL DEFAULT 'top_right',
    ADD COLUMN osd_duration_seconds INTEGER NOT NULL DEFAULT 8 CHECK (osd_duration_seconds BETWEEN 0 AND 3600),
    ADD COLUMN osd_opacity NUMERIC(3,2) NOT NULL DEFAULT 0.6 CHECK (osd_opacity BETWEEN 0 AND 1),
    ADD COLUMN osd_font_size osd_font_size_enum NOT NULL DEFAULT 'medium';
```

### `devices` — override por device (NULL = herda)

```sql
ALTER TABLE devices
    ADD COLUMN osd_show_current_audio BOOLEAN,
    ADD COLUMN osd_position osd_position_enum,
    ADD COLUMN osd_duration_seconds INTEGER CHECK (osd_duration_seconds BETWEEN 0 AND 3600),
    ADD COLUMN osd_opacity NUMERIC(3,2) CHECK (osd_opacity BETWEEN 0 AND 1),
    ADD COLUMN osd_font_size osd_font_size_enum,
    -- Estado atual reportado via heartbeat
    ADD COLUMN current_audio_track_id UUID,
    ADD COLUMN current_audio_track_name VARCHAR(500),
    ADD COLUMN current_audio_track_started_at TIMESTAMP WITH TIME ZONE;
```

### Indices

Sem indices novos. Configs sao lidas junto com o device, sem query separada.

## Downgrade

```sql
ALTER TABLE devices
    DROP COLUMN osd_show_current_audio,
    DROP COLUMN osd_position,
    DROP COLUMN osd_duration_seconds,
    DROP COLUMN osd_opacity,
    DROP COLUMN osd_font_size,
    DROP COLUMN current_audio_track_id,
    DROP COLUMN current_audio_track_name,
    DROP COLUMN current_audio_track_started_at;

ALTER TABLE tenants
    DROP COLUMN osd_show_current_audio,
    DROP COLUMN osd_position,
    DROP COLUMN osd_duration_seconds,
    DROP COLUMN osd_opacity,
    DROP COLUMN osd_font_size;

DROP TYPE osd_font_size_enum;
DROP TYPE osd_position_enum;
```

## Mudanca em models Python

### `Tenant`

```python
class Tenant(Base):
    # ... existing ...
    osd_show_current_audio = Column(Boolean, nullable=False, default=True)
    osd_position = Column(SQLEnum("top_left", "top_right", "bottom_left", "bottom_right",
                                   name="osd_position_enum"),
                         nullable=False, default="top_right")
    osd_duration_seconds = Column(Integer, nullable=False, default=8)
    osd_opacity = Column(Numeric(3, 2), nullable=False, default=0.6)
    osd_font_size = Column(SQLEnum("small", "medium", "large", name="osd_font_size_enum"),
                          nullable=False, default="medium")
```

### `Device`

```python
class Device(Base):
    # ... existing ...
    osd_show_current_audio = Column(Boolean, nullable=True)
    osd_position = Column(SQLEnum("top_left", "top_right", "bottom_left", "bottom_right",
                                   name="osd_position_enum"),
                         nullable=True)
    osd_duration_seconds = Column(Integer, nullable=True)
    osd_opacity = Column(Numeric(3, 2), nullable=True)
    osd_font_size = Column(SQLEnum("small", "medium", "large", name="osd_font_size_enum"),
                          nullable=True)

    # Estado atual (reportado via heartbeat)
    current_audio_track_id = Column(UUID, nullable=True)
    current_audio_track_name = Column(String(500), nullable=True)
    current_audio_track_started_at = Column(DateTime(timezone=True), nullable=True)
```

## Backfill

- Tenants existentes recebem defaults via DDL (`DEFAULT` em `ADD COLUMN NOT NULL`).
- Devices recebem NULL (herdam do tenant).
- `current_audio_track_*` zerados ate proximo heartbeat.

Sem backfill manual necessario.

## Validacoes (no codigo)

- Endpoint `PATCH /devices/{id}/osd-config`:
  - `osd_duration_seconds` int entre 0 e 3600.
  - `osd_opacity` float entre 0.0 e 1.0.
  - Enum values validados pelo Pydantic.
- Endpoint `PATCH /tenants/{id}/osd-config`: mesmas validacoes; NOT NULL para tenant.

## Compatibilidade com dados existentes

- Devices existentes: todos os campos NULL → herdam tenant.
- Tenants existentes: defaults setados via DDL.
- Players que nao reportam `current_audio_track_*` no heartbeat: colunas permanecem NULL/antigas.

Sem necessidade de migracao de dados ou retroativos.
