# SPEC 009 - API Contract

## Comandos novos

Endpoint existente:

`POST /devices/{device_id}/command`

Adicionar `command_type` validos:

- `minimize_player`;
- `restore_player`;
- `show_desktop`.

### minimize_player

Payload:

```json
{}
```

Resultado esperado no ACK:

```json
{
  "platform": "electron",
  "command_type": "minimize_player",
  "completed_at": "2026-06-01T00:00:00.000Z"
}
```

### restore_player

Payload opcional:

```json
{
  "restore_fullscreen": true
}
```

### show_desktop

Payload:

```json
{
  "duration_seconds": 5,
  "restore_fullscreen": true
}
```

Validacoes:

- `duration_seconds`: 1 a 300;
- default: 5 se ausente.

## Configuracao por dispositivo

Novo endpoint:

`PATCH /devices/{device_id}/desktop-exposure-config`

Request:

```json
{
  "enabled": true,
  "interval_seconds": 20,
  "duration_seconds": 5,
  "restore_fullscreen": true
}
```

Response:

```json
{
  "id": "device-uuid",
  "desktop_exposure_config": {
    "enabled": true,
    "interval_seconds": 20,
    "duration_seconds": 5,
    "restore_fullscreen": true,
    "updated_at": "2026-06-01T00:00:00"
  }
}
```

## Entrega da config ao Player

Opcao recomendada no PR 2:

Incluir em `GET /devices/{device_id}/playlist`:

```json
{
  "desktop_exposure_config": {
    "enabled": false,
    "interval_seconds": null,
    "duration_seconds": null,
    "restore_fullscreen": true,
    "updated_at": null
  }
}
```

## SSE

Ao alterar config:

```text
event: config:desktop_exposure_updated
data: {"type":"config:desktop_exposure_updated","device_id":"...","data":{"desktop_exposure_config":{...}}}
```

Player deve aplicar config recebida. Se payload vier incompleto, deve recarregar playlist/config.

## Erros

`400`:

- comando invalido;
- payload `duration_seconds` fora do range.

`403`:

- usuario sem permissao no device;
- token do player nao corresponde ao device.

`404`:

- device inexistente.

ACK de plataforma nao suportada:

```json
{
  "success": false,
  "error_message": "show_desktop nao suportado na plataforma web",
  "result": {
    "platform": "web",
    "command_type": "show_desktop",
    "platform_unsupported": true,
    "error_code": "BROWSER_ENVIRONMENT",
    "failed_at": "2026-06-01T00:00:00.000Z"
  }
}
```


