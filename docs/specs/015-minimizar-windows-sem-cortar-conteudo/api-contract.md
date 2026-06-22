# SPEC 015 — API Contract

Status: implementada — campos novos aditivos, endpoint existente reaproveitado

## Endpoint (inalterado)

```http
PATCH /api/v1/devices/{device_id}/desktop-exposure-config
```

Nenhuma mudanca de rota, metodo ou semantica geral — apenas campos novos opcionais no corpo da requisicao e na resposta.

## Payload de atualizacao (campos novos)

```json
{
  "enabled": true,
  "interval_seconds": 1800,
  "duration_seconds": 30,
  "restore_fullscreen": true,
  "show_warning": true,
  "warning_seconds_before": 15,
  "warning_text": "Voltamos já",
  "warning_media_id": null
}
```

Validacao (`DeviceDesktopExposureConfigUpdate`):

- `show_warning`: bool opcional.
- `warning_seconds_before`: int opcional, `0 <= valor <= 120`.
- `warning_text`: string opcional, max 255 caracteres.
- `warning_media_id`: string opcional (uuid), sem validacao de existencia (sem FK).

Todos os campos sao `Optional` e atualizados apenas quando presentes no payload (`exclude_unset`), preservando o comportamento de PATCH parcial ja existente.

## Resposta (`desktop_exposure_config`, campos novos)

```json
{
  "id": "device-uuid",
  "desktop_exposure_config": {
    "enabled": true,
    "interval_seconds": 1800,
    "duration_seconds": 30,
    "restore_fullscreen": true,
    "show_warning": true,
    "warning_seconds_before": 15,
    "warning_text": "Voltamos já",
    "warning_media_id": null,
    "updated_at": "2026-06-18T11:00:00"
  }
}
```

Devices criados antes desta SPEC (sem os campos novos no banco) retornam:

```json
{
  "show_warning": false,
  "warning_seconds_before": null,
  "warning_text": null,
  "warning_media_id": null
}
```

(valores default da migration — `show_warning` tem `server_default=false`, os demais `nullable=True`).

## Migration

`backend/alembic/versions/20260618_1100_desktop_exposure_warning.py`:

- `ADD COLUMN desktop_exposure_show_warning BOOLEAN NOT NULL DEFAULT false`
- `ADD COLUMN desktop_exposure_warning_seconds_before INTEGER NULL`
- `ADD COLUMN desktop_exposure_warning_text VARCHAR(255) NULL`
- `ADD COLUMN desktop_exposure_warning_media_id UUID NULL`
- `CHECK ((NOT desktop_exposure_show_warning) OR (desktop_exposure_warning_seconds_before BETWEEN 0 AND 120))`

Migration e puramente aditiva — nenhuma coluna existente e alterada/removida, `downgrade()` reverte limpo.

## Comandos de dispositivo (inalterados)

`minimize_player`, `restore_player`, `show_desktop` continuam com o mesmo contrato (`VALID_COMMANDS`, payload `{duration_seconds, restore_fullscreen}` para `show_desktop`). Esta SPEC nao adiciona comandos novos — a decisao de "esperar o conteudo terminar" e tomada inteiramente no client antes de invocar `show_desktop`, nao no backend.
