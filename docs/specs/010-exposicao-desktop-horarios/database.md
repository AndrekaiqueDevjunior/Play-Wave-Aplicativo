# SPEC 010 — Banco de Dados

## Nova tabela: `device_desktop_exposure_events`

Relação 1:N com `devices`. Cada linha = um evento de exposição por horário.

| Coluna | Tipo | Nulo | Default | Notas |
|--------|------|------|---------|-------|
| `id` | UUID / Integer PK | não | — | PK |
| `device_id` | FK → devices.id | não | — | ON DELETE CASCADE |
| `name` | varchar(120) | não | — | ex.: "Mostrar ERP" |
| `time` | varchar(5) | não | — | formato `HH:MM` (00:00–23:59) |
| `duration_seconds` | integer | não | — | 1–300 |
| `enabled` | boolean | não | `true` | evento ativo |
| `weekdays` | varchar(20) | sim | `null` | opcional (CSV `0..6`); `null` = todos os dias |
| `created_at` | timestamp | não | now() | |
| `updated_at` | timestamp | não | now() | |

### Índices / Constraints

- `ix_dee_device_id` em `device_id`.
- `ck_dee_duration` CHECK `duration_seconds BETWEEN 1 AND 300`.
- `ck_dee_time_format` CHECK `time ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'` (Postgres regex).

## Migration

Arquivo: `backend/alembic/versions/2026XXXX_device_desktop_exposure_events.py`

- `op.create_table("device_desktop_exposure_events", ...)` com colunas acima.
- FK para `devices.id` com `ondelete="CASCADE"`.
- Índice em `device_id`.
- Sem backfill (tabela nasce vazia; dispositivos antigos = nenhum evento).

## Observação

A tabela é **independente** das colunas `desktop_exposure_*` em `devices` (SPEC 009 / intervalo),
que permanecem inalteradas.
