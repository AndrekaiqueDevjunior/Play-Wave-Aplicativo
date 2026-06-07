# SPEC 010 — Contrato de API

Base: `/api/v1`. Autenticação: token de usuário (admin ou mesmo tenant do device).

## Listar eventos

```http
GET /devices/{device_id}/desktop-exposure-events
```
Resposta `200`:
```json
{
  "device_id": "abc123",
  "events": [
    { "id": "e1", "name": "Mostrar ERP", "time": "08:00", "duration_seconds": 15, "enabled": true, "weekdays": null },
    { "id": "e2", "name": "Dashboard", "time": "14:00", "duration_seconds": 10, "enabled": true, "weekdays": "1,2,3,4,5" }
  ]
}
```

## Criar evento

```http
POST /devices/{device_id}/desktop-exposure-events
Content-Type: application/json

{ "name": "Mostrar ERP", "time": "08:00", "duration_seconds": 15, "enabled": true }
```
Resposta `201`: objeto do evento criado.
Validações: `time` em `HH:MM`; `duration_seconds` 1–300; `name` 1–120 chars.

## Atualizar evento

```http
PATCH /devices/{device_id}/desktop-exposure-events/{event_id}
Content-Type: application/json

{ "time": "08:30", "enabled": false }
```
Resposta `200`: objeto atualizado. Campos opcionais (partial update).

## Remover evento

```http
DELETE /devices/{device_id}/desktop-exposure-events/{event_id}
```
Resposta `204`.

## Propagação ao Player

- A **playlist response** (`GET /devices/{id}/playlist`) passa a incluir:
```json
"desktop_exposure_events": [ { "id": "e1", "name": "...", "time": "08:00", "duration_seconds": 15, "enabled": true, "weekdays": null } ]
```
- Toda mutação (POST/PATCH/DELETE) chama `_publish_device_playlist_invalidated(device, reason="desktop_exposure_events_updated")` para o Player recarregar via SSE.

## Erros

- `403` — usuário sem permissão (não admin e tenant diferente).
- `404` — device ou event inexistente.
- `422` — payload inválido (time/duration fora do formato/range).
