# SPEC 005 — Banco

## Migration: `2026XXXX_audio_policy.py`

### Enum

```sql
CREATE TYPE audio_policy_enum AS ENUM (
    'auto',
    'radio_only',
    'media_audio_only',
    'mix',
    'muted_video_with_radio'
);
```

### `tenants` — defaults globais

```sql
ALTER TABLE tenants
    ADD COLUMN audio_policy_default audio_policy_enum DEFAULT 'auto',
    ADD COLUMN audio_fade_ms INTEGER DEFAULT 200 CHECK (audio_fade_ms BETWEEN 0 AND 2000);
```

### `devices` — default por device

```sql
ALTER TABLE devices
    ADD COLUMN audio_policy_default audio_policy_enum;  -- NULL = herda do tenant
```

### `campaigns` — politica da campanha

```sql
ALTER TABLE campaigns
    ADD COLUMN audio_policy audio_policy_enum;  -- NULL = herda do device/tenant
```

`campaign.video_muted` permanece (legado) por 2 releases.

### `media` — override por midia + has_audio

```sql
ALTER TABLE media
    ADD COLUMN audio_policy audio_policy_enum,    -- NULL = herda da campaign
    ADD COLUMN has_audio BOOLEAN;                  -- NULL = nao detectado
```

### Indices

Sem indices novos necessarios (politica nao eh filtro de listagem).

## Backfill (mesma migration, em data_upgrade ou script separado)

### `media.has_audio`

```sql
UPDATE media SET has_audio = FALSE WHERE type IN ('image', 'url', 'html');
-- Para videos: deixar NULL e Celery task popular depois via ffprobe.
```

Script Celery `tasks/media.backfill_has_audio.py`:

```python
@celery_app.task
def backfill_has_audio(limit=100):
    medias = db.query(Media).filter(
        Media.type == "video",
        Media.has_audio.is_(None),
    ).limit(limit).all()
    for m in medias:
        try:
            m.has_audio = detect_audio_streams(get_media_path(m))
        except Exception as e:
            logger.warning(f"backfill_has_audio failed for {m.id}: {e}")
    db.commit()
```

Rodar manualmente apos deploy ou via beat schedule diario ate processar tudo.

### `campaigns.audio_policy` (a partir de `video_muted`)

```sql
UPDATE campaigns
SET audio_policy = CASE
    WHEN video_muted = TRUE AND audio_playlist_id IS NOT NULL THEN 'muted_video_with_radio'::audio_policy_enum
    WHEN video_muted = TRUE AND audio_playlist_id IS NULL THEN 'muted_video_with_radio'::audio_policy_enum
    WHEN video_muted = FALSE AND audio_playlist_id IS NOT NULL THEN 'mix'::audio_policy_enum
    WHEN video_muted = FALSE AND audio_playlist_id IS NULL THEN 'auto'::audio_policy_enum
    ELSE 'auto'::audio_policy_enum
END
WHERE audio_policy IS NULL;
```

### `tenants.audio_policy_default`

Ja vem com default `auto` via DDL. Nao precisa backfill.

### `tenants.audio_fade_ms`

Ja vem com default 200. Nao precisa backfill.

## Downgrade

```sql
ALTER TABLE media DROP COLUMN audio_policy, DROP COLUMN has_audio;
ALTER TABLE campaigns DROP COLUMN audio_policy;
ALTER TABLE devices DROP COLUMN audio_policy_default;
ALTER TABLE tenants DROP COLUMN audio_policy_default, DROP COLUMN audio_fade_ms;
DROP TYPE audio_policy_enum;
```

## Mudanca em models Python

### `Tenant`

```python
class Tenant(Base):
    # ...
    audio_policy_default = Column(SQLEnum(AudioPolicy, name="audio_policy_enum"), default=AudioPolicy.AUTO)
    audio_fade_ms = Column(Integer, default=200)
```

### `Device`

```python
class Device(Base):
    # ...
    audio_policy_default = Column(SQLEnum(AudioPolicy, name="audio_policy_enum"), nullable=True)
```

### `Campaign`

```python
class Campaign(Base):
    # ...
    video_muted = Column(Boolean, default=False)  # LEGADO
    audio_policy = Column(SQLEnum(AudioPolicy, name="audio_policy_enum"), nullable=True)
```

### `Media`

```python
class Media(Base):
    # ...
    audio_policy = Column(SQLEnum(AudioPolicy, name="audio_policy_enum"), nullable=True)
    has_audio = Column(Boolean, nullable=True)
```

## Compatibilidade com dados existentes

- Tenants existentes: `audio_policy_default = auto`, `audio_fade_ms = 200` (defaults).
- Devices existentes: `audio_policy_default = NULL` (herda do tenant).
- Campaigns existentes: backfill setado conforme tabela.
- Medias existentes: `audio_policy = NULL`, `has_audio = NULL` para video (Celery preenche), `FALSE` para resto.

`campaign.video_muted` continua presente. Em proxima SPEC de cleanup (apos 2 releases), removeremos.

## Validacoes no codigo

- Setar `audio_policy` para midia tipo `image`/`url`/`html` que nao faz sentido nao eh proibido, mas avisar: midia sem audio sempre tem `videoMuted=true` no resolver, entao `audio_policy=mix` em imagem se comporta como `radio_only`.
- Setar `audio_fade_ms` > 2000 retorna 422 no endpoint admin.
