# SPEC 004 — Banco

## Migrations existentes (nao mexer)

- `20260521_0900_device_pairing_token_version.py` — criou `pairing_version`, `token_version`, `requires_repairing` em `devices`.

## Migration nova: `device_pairing_events`

Arquivo: `backend/alembic/versions/2026XXXX_device_pairing_events.py`

### Tabela

```sql
CREATE TABLE device_pairing_events (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id        UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    event_type       VARCHAR(40) NOT NULL,
    previous_token_version    INTEGER,
    new_token_version         INTEGER,
    previous_pairing_version  INTEGER,
    new_pairing_version       INTEGER,
    previous_pairing_code     VARCHAR(40),
    new_pairing_code          VARCHAR(40),
    requested_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    reason           TEXT,
    metadata         JSONB,
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_device_pairing_events_device_id_created_at
  ON device_pairing_events (device_id, created_at DESC);

CREATE INDEX ix_device_pairing_events_event_type
  ON device_pairing_events (event_type);
```

### Valores aceitos em `event_type`

- `paired` — primeiro pareamento bem-sucedido.
- `re_paired` — re-pareamento (apos forceRepair ou regenerate).
- `code_regenerated` — admin gerou novo codigo.
- `force_repair` — admin revogou tokens sem trocar codigo.
- `token_revoked` — admin chamou endpoint legado `revoke_token`.
- `code_expired` — codigo expirou sem confirmacao em 15min.
- `device_blocked` — device foi bloqueado.
- `device_unblocked` — device foi desbloqueado.

### Sem backfill

Historico anterior nao eh reconstrutivel. Tabela inicia vazia e passa a registrar a partir do deploy.

### Downgrade

```sql
DROP TABLE device_pairing_events;
```

## Sem outras alteracoes de schema

`devices` ja tem todas as colunas necessarias (`pairing_version`, `token_version`, `requires_repairing`).

## Mudancas no codigo (CRUDs)

### `crud_device.regenerate_pairing_code` — adicionar audit

Apos as operacoes existentes, inserir row em `device_pairing_events`:

```python
db.add(DevicePairingEvent(
    device_id=device.id,
    tenant_id=device.tenant_id,
    event_type="code_regenerated",
    previous_token_version=old_token_version,
    new_token_version=device.token_version,
    previous_pairing_version=old_pairing_version,
    new_pairing_version=device.pairing_version,
    previous_pairing_code=old_code,
    new_pairing_code=device.pairing_code,
    requested_by=current_user.id,
    reason=request.reason,
    metadata={"revoked_sessions_count": revoked_count},
))
```

### `crud_device.force_repair` — novo metodo

```python
def force_repair(self, db, device, current_user, reason=None):
    old_token_version = device.token_version
    device.device_token = None
    device.token_version += 1
    device.requires_repairing = True
    # NAO mexe em pairing_code nem pairing_version.

    revoked_count = revoke_device_sessions(db, device.id)

    db.add(DevicePairingEvent(
        device_id=device.id,
        tenant_id=device.tenant_id,
        event_type="force_repair",
        previous_token_version=old_token_version,
        new_token_version=device.token_version,
        requested_by=current_user.id,
        reason=reason,
        metadata={"revoked_sessions_count": revoked_count},
    ))

    db.commit()
    return revoked_count
```

### `crud_device.confirm_pairing` — registrar `paired` ou `re_paired`

Quando player confirma pareamento e recebe token, inserir evento:

```python
event_type = "re_paired" if device.pairing_version > 1 else "paired"
db.add(DevicePairingEvent(
    device_id=device.id,
    tenant_id=device.tenant_id,
    event_type=event_type,
    new_token_version=device.token_version,
    new_pairing_version=device.pairing_version,
))
```

## Compatibilidade com dados existentes

- Sem migracao de dados.
- Devices ja pareados continuam funcionando com `pairing_version=1, token_version=1, requires_repairing=false`.
- Primeiro acesso apos deploy registra `paired` event (ou nao — sem importancia historica).
