# SPEC 003 — Banco

## Migrations existentes (nao mexer)

- `002_add_device_commands.py` — criou `device_commands` original.
- `20260521_0915_device_command_lifecycle.py` — adicionou `received_at`, `started_at`, `expires_at`, `result` (JSON) e enum values `received`, `executing`, `completed`, `expired`.

Esses dois ja cobrem a estrutura necessaria para o lifecycle desta SPEC.

## Migration nova: defaults e indices

Arquivo: `backend/alembic/versions/2026XXXX_command_defaults_and_index.py`

### Alteracoes

1. Aplicar default `expires_at = NOW() + interval '10 minutes'` para novos comandos via codigo do CRUD (nao no banco — facilita ajustar por tipo de comando).

2. Criar indice composto para query de pendentes:

```
CREATE INDEX ix_device_commands_device_status_expires
  ON device_commands (device_id, status, expires_at)
  WHERE status IN ('pending', 'sent', 'received', 'executing');
```

Justificativa: query `/commands/pending` filtra por `device_id`, `status` e `expires_at > now`. Indice parcial reduz tamanho.

3. Adicionar coluna `is_destructive` (boolean, default false) em `device_commands`:

```
ALTER TABLE device_commands
  ADD COLUMN is_destructive BOOLEAN NOT NULL DEFAULT FALSE;
```

Setar `true` em criacao quando `command_type IN ('restart_app','restart_device','shutdown_device','factory_reset')`. UI usa para mostrar badge especial.

### Backfill

```
UPDATE device_commands
SET is_destructive = TRUE
WHERE command_type IN ('restart_app','restart_device','shutdown_device','factory_reset','reboot');
```

### Downgrade

Drop indice + drop coluna `is_destructive`.

## Sem novas tabelas

Esta SPEC nao cria tabelas novas. Apenas indice + coluna `is_destructive` + uso correto dos campos ja existentes.

## Validacoes no codigo (nao no banco)

### `crud_device_command.create`

- Setar `expires_at = now + 10 minutos` se nao informado.
- Setar `is_destructive = True` para `command_type` destrutivos.
- Validar `requested_by` nao nulo para destrutivos.

### `crud_device_command.get_pending`

- Filtrar `status = PENDING`.
- Filtrar `expires_at IS NULL OR expires_at > now`.
- Order by `requested_at ASC`.
- Limit configuravel (default 20).

### `crud_device_command.mark_expired_batch`

- Receber lista de IDs ou rodar query global.
- Atualizar `status = EXPIRED`, `error_message = "Comando expirou sem ACK do player"`.
- Retornar contagem.

## Compatibilidade com dados existentes

- Comandos antigos com `expires_at = NULL` continuam funcionando (filtro `IS NULL OR > now`).
- Comandos antigos com status `EXECUTED` continuam validos como alias de `COMPLETED`.
- `is_destructive = FALSE` por default e backfill cuida do historico.
