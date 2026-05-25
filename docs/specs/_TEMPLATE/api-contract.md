# SPEC NNN — Contrato de API

## Headers

{Headers novos ou alterados, se houver.}

## Endpoints existentes (mudancas)

### `METHOD /path`

{Descricao da mudanca.}

**Body atual** (mantido):

```json
{...}
```

**Body estendido** (compatibilidade):

```json
{...}
```

**Response**:

```json
{...}
```

**Validacoes adicionadas:**

- {...}.

## Endpoints novos

### `METHOD /path`

Autenticacao: {admin / device token / publico}.

**Request body**:

```json
{...}
```

**Response**:

```json
{...}
```

**Erros**:

| Status | error_code | Quando |
|---|---|---|
| 400 | ... | ... |

## Schema Pydantic

```python
class ...
```

## Eventos SSE

Canal: `pw:device:{device_id}:events`

### `event_name`

Payload:

```json
{...}
```

## Compatibilidade

- {Clientes antigos: como continuam funcionando}.
- {Cliente novo: o que precisa adaptar}.
