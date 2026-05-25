# SPEC 007 — Contratos de API

## Existentes a preservar

### Midia

- `GET /media`
- `POST /media/upload`
- `POST /media/{id}/replace-file`
- `GET /media/{id}/usage`
- `GET /media/{id}/versions`
- `POST /media/{id}/recompute-audio-detection`

### Campanha

- `GET /campaigns/{id}/items`
- `POST /campaigns/{id}/items`
- `PUT /campaigns/{id}/items/{item_id}`
- `DELETE /campaigns/{id}/items/{item_id}`
- `PATCH /campaigns/{id}/items/reorder`

### Audio atual

- `GET /audio/tracks`
- `POST /audio/tracks/upload`
- `GET /audio/playlists`
- `POST /audio/playlists`
- `PUT /audio/playlists/{id}`
- `GET /audio/devices/{id}/playlist`

### Player

- `GET /devices/{id}/playlist`
- `GET /devices/{id}/commands/pending`
- `POST /devices/{id}/commands/{command_id}/received`
- `POST /devices/{id}/commands/{command_id}/started`
- `POST /devices/{id}/commands/{command_id}/ack`
- `POST /devices/{id}/heartbeat`

## Novos endpoints propostos

### Upload multiplo de audio

`POST /audio/tracks/upload-multiple`

Multipart:

- `files[]`
- `category?`
- `status?`
- `dedupe?`

Resposta:

```json
{
  "created": [
    { "file_name": "musica.mp3", "track": { "id": "...", "name": "musica" } }
  ],
  "failed": [
    { "file_name": "erro.txt", "error_code": "UNSUPPORTED_TYPE", "message": "Formato nao suportado" }
  ],
  "duplicates": [
    { "file_name": "igual.mp3", "existing_track_id": "..." }
  ]
}
```

### Itens de playlist de audio

- `GET /audio/playlists/{playlist_id}/items`
- `POST /audio/playlists/{playlist_id}/items`
- `PUT /audio/playlists/{playlist_id}/items/{item_id}`
- `DELETE /audio/playlists/{playlist_id}/items/{item_id}`
- `PATCH /audio/playlists/{playlist_id}/items/reorder`

### Pastas de audio

- `GET /audio/folders`
- `POST /audio/folders`
- `GET /audio/folders/{id}`
- `PUT /audio/folders/{id}`
- `DELETE /audio/folders/{id}`
- `POST /audio/folders/{id}/tracks`
- `DELETE /audio/folders/{id}/tracks/{track_id}`
- `PATCH /audio/folders/{id}/tracks/reorder`

### Agenda de pastas

- `GET /audio/playlists/{playlist_id}/folder-schedules`
- `POST /audio/playlists/{playlist_id}/folder-schedules`
- `PUT /audio/playlists/{playlist_id}/folder-schedules/{schedule_id}`
- `DELETE /audio/playlists/{playlist_id}/folder-schedules/{schedule_id}`
- `POST /audio/playlists/{playlist_id}/folder-schedules/validate`

### Spots

- `GET /audio/spots`
- `POST /audio/spots`
- `PUT /audio/spots/{id}`
- `DELETE /audio/spots/{id}`
- `GET /audio/spots/schedules`
- `POST /audio/spots/schedules`
- `PUT /audio/spots/schedules/{id}`
- `DELETE /audio/spots/schedules/{id}`

### Payload novo do player para radio v2

`GET /devices/{id}/playlist` deve evoluir para:

```json
{
  "audio_playlist": {
    "playlist_id": "...",
    "name": "Radio Loja",
    "volume": 0.7,
    "loop": true,
    "play_mode": "sequential",
    "active_folder": {
      "id": "...",
      "name": "Manha",
      "play_mode": "shuffle"
    },
    "tracks": [
      {
        "id": "...",
        "name": "Faixa 1",
        "file_url": "/uploads/audio/tracks/a.mp3",
        "duration_seconds": 180,
        "order_index": 10,
        "volume": 0.7
      }
    ],
    "spots": [
      {
        "id": "...",
        "track_id": "...",
        "interval_seconds": 1800,
        "insertion_policy": "after_current_track"
      }
    ]
  }
}
```

Compatibilidade:

- enquanto `items` nao existir, player usa `tracks` construidos de `track_ids`.
