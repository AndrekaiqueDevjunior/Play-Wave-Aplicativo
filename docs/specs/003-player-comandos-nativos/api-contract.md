# SPEC 003 — Contrato de API

## Endpoints existentes (sem mudanca de URL)

### Criar comando

`POST /devices/{device_id}/command`

**Body atual** (mantido):

```
{
  "command_type": "shutdown_device",
  "payload": {}
}
```

**Body estendido** (compatibilidade — campos opcionais):

```
{
  "command_type": "shutdown_device",
  "payload": {},
  "expires_in_seconds": 600
}
```

**Validacoes adicionadas:**

- `command_type` deve estar em `VALID_COMMANDS` (mantido).
- Para comandos destrutivos (`restart_app`, `restart_device`, `shutdown_device`, `factory_reset`): `request.user_id` obrigatorio nao nulo (ja eh, mas auditar).
- `expires_in_seconds` quando informado: entre 60 e 3600. Default 600 (10 min).

**Response** (sem mudanca de schema):

```
{
  "id": "uuid",
  "device_id": "uuid",
  "command_type": "shutdown_device",
  "status": "pending",
  "requested_at": "2026-05-22T10:00:00",
  "expires_at": "2026-05-22T10:10:00",
  "is_destructive": true,
  "payload": {},
  "requested_by": "uuid"
}
```

### Listar pendentes (player)

`GET /devices/{device_id}/commands/pending`

**Mudanca:** passa a excluir comandos com `expires_at < now`. Mantem comportamento de marcar como `SENT` apos retorno.

**Response** (sem mudanca de schema, lista de comandos).

### Marcar recebido

`POST /devices/{device_id}/commands/{command_id}/received`

**Sem mudanca.**

### Marcar iniciado

`POST /devices/{device_id}/commands/{command_id}/started`

**Sem mudanca.**

### ACK final

`POST /devices/{device_id}/commands/{command_id}/ack`

**Body** (estendido — campos novos opcionais):

```
{
  "success": true,
  "error_message": null,
  "result": {
    "platform": "electron-linux",
    "command_type": "shutdown_device",
    "completed_at": "2026-05-22T10:01:23",
    "ack_phase": "pre_execution"
  }
}
```

**Campos novos em `result`:**

- `platform`: identificador da plataforma (electron-linux, electron-win32, capacitor-android, web).
- `ack_phase`: `pre_execution` para destrutivos, `post_execution` para os demais (informativo, nao altera lifecycle).
- `platform_unsupported`: boolean, true quando comando nao tem implementacao na plataforma.
- `error_code`: string padronizada (ver tabela abaixo).
- `reason`: contexto livre da falha.

**Tabela de `error_code`:**

| error_code | Significado |
|---|---|
| `DEVICE_OWNER_REQUIRED` | APK precisa de provisionamento como Device Owner |
| `PERMISSION_DENIED` | OS rejeitou o comando (ex: sudoers nao configurado) |
| `COMMAND_NOT_IMPLEMENTED` | Plataforma reconhecida, mas handler ausente |
| `BROWSER_ENVIRONMENT` | Player rodando em web puro, nao suporta |
| `SHUTDOWN_FAILED` | Comando OS executou mas retornou erro |
| `TIMEOUT` | Operacao excedeu tempo |
| `UNKNOWN_COMMAND` | command_type nao reconhecido pelo player |

## Endpoints novos

Nenhum. Toda a SPEC reusa endpoints existentes.

## Schema Pydantic

### `DeviceCommandCreate` (estender)

Adicionar:

- `expires_in_seconds: int | None = None` (validar 60-3600).

### `DeviceCommandResponse` (estender)

Adicionar:

- `is_destructive: bool`.

### `DeviceCommandAck` (estender)

`result` deixa de ser `dict` generico e passa a aceitar opcionalmente campos tipados:

```
class CommandAckResult(BaseModel):
    platform: str | None = None
    command_type: str | None = None
    ack_phase: Literal["pre_execution", "post_execution"] | None = None
    platform_unsupported: bool = False
    error_code: str | None = None
    reason: str | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    # Permitir extras (frontend nao quebra).
    model_config = ConfigDict(extra="allow")
```

`DeviceCommandAck.result` muda de `dict | None` para `CommandAckResult | None`.

## Eventos SSE

Canal: `pw:device:{device_id}:events`

Evento novo: `command:new` publicado quando comando eh criado.

Payload:

```
{
  "event": "command:new",
  "command_id": "uuid",
  "command_type": "shutdown_device",
  "is_destructive": true
}
```

Player escuta e dispara `buscarComandosPendentes` imediatamente em vez de esperar polling 10s.

## Compatibilidade

- Clientes antigos sem `expires_in_seconds` continuam funcionando — usa default.
- Clientes antigos sem `is_destructive` no response: campo simplesmente ignorado.
- ACK com `result` antigo (sem error_code etc) continua aceito porque schema permite `extra="allow"`.
- Player antigo sem suporte a evento SSE `command:new` continua funcionando via polling.
