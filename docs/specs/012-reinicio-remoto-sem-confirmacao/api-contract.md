# SPEC 012 — API Contract

Status: aguardando SPEC 011

## Contrato esperado

Esta SPEC deve usar o contrato real ja existente no projeto sempre que possivel.

## Criar comando

```http
POST /api/v1/devices/{device_id}/command
```

Payload esperado:

```json
{
  "command_type": "restart_app",
  "payload": {},
  "expires_in_seconds": 300
}
```

## Buscar comandos pendentes

Endpoint real a confirmar por auditoria.

```http
GET /api/v1/devices/{device_id}/commands/pending
```

ou equivalente usado pelo player.

## Confirmar recebimento

```http
POST /api/v1/devices/{device_id}/commands/{command_id}/received
```

## Confirmar inicio

```http
POST /api/v1/devices/{device_id}/commands/{command_id}/started
```

## Confirmar resultado

```http
POST /api/v1/devices/{device_id}/commands/{command_id}/ack
```

Payload esperado:

```json
{
  "success": true,
  "result": {
    "command": "restart_app",
    "platform": "electron-windows"
  },
  "error_message": null
}
```

## Erros esperados

- `COMMAND_EXPIRED`
- `COMMAND_ALREADY_EXECUTED`
- `PLATFORM_UNSUPPORTED`
- `RESTART_FAILED`
- `DEVICE_TOKEN_INVALID`

## Compatibilidade

Se os nomes reais forem `completed`/`failed` em vez de `success`/`failed`, preservar o backend atual e atualizar este documento apos auditoria.

