# API Contracts — Audio Player System

**Version**: 1.0  
**Status**: Definition Phase (Pre-Integration)  
**Last Updated**: 2026-05-23

---

## Table of Contents

1. [Enums & Constants](#enums--constants)
2. [Audio Tracks](#audio-tracks)
3. [Audio Folders](#audio-folders)
4. [Audio Playlists](#audio-playlists)
5. [Folder Schedules](#folder-schedules)
6. [Audio Spots](#audio-spots)
7. [Spot Schedules](#spot-schedules)
8. [Playback Events](#playback-events)
9. [Error Responses](#error-responses)
10. [Timestamps & Timezones](#timestamps--timezones)

---

## Enums & Constants

### PlayMode
Used in: folder schedules, playlists
```
Values: "sequential" | "shuffle" | "loop"
JSON Format: lowercase string
```

### SpotInsertionPolicy
Used in: spot records
```
Values: "interrupt" | "wait_silence" | "fade_mix"
JSON Format: lowercase string
Interrupt: Stop current audio immediately, play spot
Wait Silence: Queue spot, play when current ends naturally
Fade Mix: Reduce background to 30%, play spot on top
```

### SpotStatus
Used in: spot records
```
Values: "draft" | "active" | "archived"
JSON Format: lowercase string
```

### EventType
Used in: playback events
```
Values: "track_started" | "track_ended" | "spot_started" | "spot_ended" | "error"
JSON Format: snake_case string
```

### EventResult
Used in: playback events
```
Values: "success" | "failed"
JSON Format: lowercase string
```

### AudioState (Frontend Only)
Used in: AudioManager state
```
Values: "radio" | "media_audio" | "spot" | "silent"
JSON Format: snake_case string
Backend: Convert to event_type enum
```

### AudioMode (Frontend Only)
Used in: playlist play mode
```
Values: "sequential" | "shuffle" | "loop"
JSON Format: lowercase string
Matches PlayMode enum
```

---

## Audio Tracks

### Upload Multiple Tracks

**Endpoint:** `POST /api/v1/audio/tracks/upload-multiple`

**Content-Type:** `multipart/form-data`

**Request:**
```
Files: files[] (audio/mp3, audio/wav, audio/aac, audio/m4a, video/mp4)
Fields:
  category: string (required) — "background" | "spot" | "jingle"
  description: string (optional)
  is_loopable: boolean (optional, default: false)
```

**Response (200 OK):**
```json
{
  "uploaded": [
    {
      "id": "uuid",
      "name": "track_name.mp3",
      "file_url": "/media/audio/tracks/uuid.mp3",
      "duration_seconds": 180,
      "size_bytes": 5242880,
      "category": "background",
      "description": "optional description",
      "is_loopable": false,
      "created_at": "2026-05-23T14:30:00Z",
      "updated_at": "2026-05-23T14:30:00Z"
    }
  ],
  "errors": []
}
```

**Response (206 Partial):**
```json
{
  "uploaded": [
    { "id": "uuid", "name": "track1.mp3", ... }
  ],
  "errors": [
    {
      "filename": "track2.mp3",
      "error_message": "File exceeds maximum size (100MB)"
    }
  ]
}
```

**Validation:**
- File size: max 100MB per file
- Duration auto-detected via ffprobe
- Supported formats: MP3, WAV, AAC, M4A, MP4 (audio extracted)
- Category required: one of background | spot | jingle

**Notes:**
- Backend generates file_url automatically
- If `errors` is empty, must return `[]` not null
- Duration detection is automatic, do not send from frontend

---

### Get Track

**Endpoint:** `GET /api/v1/audio/tracks/{track_id}`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "track_name.mp3",
  "file_url": "/media/audio/tracks/uuid.mp3",
  "duration_seconds": 180,
  "size_bytes": 5242880,
  "category": "background",
  "description": "optional description",
  "is_loopable": false,
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

---

### List Tracks

**Endpoint:** `GET /api/v1/audio/tracks?category={category}&limit=20&offset=0`

**Query Parameters:**
- `category` (optional): "background" | "spot" | "jingle"
- `limit` (default: 20): max 100
- `offset` (default: 0): pagination

**Response (200 OK):**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "id": "uuid",
      "name": "track_name.mp3",
      "file_url": "/media/audio/tracks/uuid.mp3",
      "duration_seconds": 180,
      "size_bytes": 5242880,
      "category": "background",
      "created_at": "2026-05-23T14:30:00Z"
    }
  ]
}
```

---

## Audio Folders

### Create Folder

**Endpoint:** `POST /api/v1/audio/folders`

**Request:**
```json
{
  "name": "Morning Music",
  "description": "Background music for morning hours",
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Morning Music",
  "description": "Background music for morning hours",
  "is_active": true,
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

**Validation:**
- name: required, max 255 chars
- description: optional, max 1000 chars
- is_active: boolean, default true

---

### Get Folder

**Endpoint:** `GET /api/v1/audio/folders/{folder_id}`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Morning Music",
  "description": "Background music for morning hours",
  "is_active": true,
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z",
  "track_count": 12
}
```

**Note:** `tracks` array is NOT included. See [Get Folder Tracks](#get-folder-tracks) for relationship.

---

### Get Folder Tracks

**Endpoint:** `GET /api/v1/audio/folders/{folder_id}/tracks?limit=50&offset=0`

**Query Parameters:**
- `limit` (default: 50): max 200
- `offset` (default: 0): pagination

**Response (200 OK):**
```json
{
  "folder_id": "uuid",
  "total": 12,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": "uuid",
      "track_id": "uuid",
      "name": "track_name.mp3",
      "file_url": "/media/audio/tracks/uuid.mp3",
      "duration_seconds": 180,
      "category": "background",
      "created_at": "2026-05-23T14:30:00Z"
    }
  ]
}
```

**Lazy Load:** Tracks are NOT included in Get Folder response. Must fetch separately.

---

### Update Folder

**Endpoint:** `PUT /api/v1/audio/folders/{folder_id}`

**Request:**
```json
{
  "name": "Morning Music (Updated)",
  "description": "New description",
  "is_active": true
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Morning Music (Updated)",
  "description": "New description",
  "is_active": true,
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:01Z"
}
```

---

### Add Tracks to Folder

**Endpoint:** `POST /api/v1/audio/folders/{folder_id}/tracks`

**Request:**
```json
{
  "track_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

**Response (200 OK):**
```json
{
  "folder_id": "uuid",
  "added": 3,
  "total_tracks": 15,
  "message": "Successfully added 3 tracks"
}
```

**Validation:**
- track_ids: required, non-empty array, max 100 per request
- Duplicate track_ids in folder: skip silently
- Non-existent track_id: return 400 with details

---

### Remove Track from Folder

**Endpoint:** `DELETE /api/v1/audio/folders/{folder_id}/tracks/{track_id}`

**Response (200 OK):**
```json
{
  "folder_id": "uuid",
  "track_id": "uuid",
  "message": "Track removed from folder",
  "remaining": 14
}
```

---

## Audio Playlists

### Create Playlist

**Endpoint:** `POST /api/v1/audio/playlists`

**Request:**
```json
{
  "name": "Monday Broadcast",
  "description": "Content for Monday broadcasts",
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Monday Broadcast",
  "description": "Content for Monday broadcasts",
  "is_active": true,
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

---

### Get Playlist with Relations

**Endpoint:** `GET /api/v1/audio/playlists/{playlist_id}?include=items,schedules,spots`

**Query Parameters:**
- `include` (optional): comma-separated list of relations to eager-load
  - `items` — playlist items (tracks)
  - `schedules` — folder schedules
  - `spots` — spot schedules
  - `all` — all relations

**Response (200 OK) — Without Include:**
```json
{
  "id": "uuid",
  "name": "Monday Broadcast",
  "description": "Content for Monday broadcasts",
  "is_active": true,
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

**Response (200 OK) — With Include=all:**
```json
{
  "id": "uuid",
  "name": "Monday Broadcast",
  "description": "Content for Monday broadcasts",
  "is_active": true,
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z",
  "items": [
    {
      "id": "uuid",
      "track_id": "uuid",
      "name": "track_name.mp3",
      "file_url": "/media/audio/tracks/uuid.mp3",
      "duration_seconds": 180,
      "position": 1,
      "created_at": "2026-05-23T14:30:00Z"
    }
  ],
  "folder_schedules": [
    {
      "id": "uuid",
      "folder_id": "uuid",
      "start_time": "06:00",
      "end_time": "12:00",
      "play_mode": "sequential",
      "priority": 50,
      "is_active": true,
      "created_at": "2026-05-23T14:30:00Z"
    }
  ],
  "spot_schedules": [
    {
      "id": "uuid",
      "spot_id": "uuid",
      "interval_seconds": 1800,
      "start_time": "06:00",
      "end_time": "22:00",
      "priority": 100,
      "is_active": true,
      "created_at": "2026-05-23T14:30:00Z"
    }
  ]
}
```

**Note:** By default (no include), relationships are not loaded. Frontend must:
1. Load playlist
2. Make separate calls for items, folder_schedules, spot_schedules
OR use `?include=all` for single request

---

### List Playlists

**Endpoint:** `GET /api/v1/audio/playlists?limit=20&offset=0&is_active=true`

**Query Parameters:**
- `limit` (default: 20)
- `offset` (default: 0)
- `is_active` (optional): true | false

**Response (200 OK):**
```json
{
  "total": 5,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "id": "uuid",
      "name": "Monday Broadcast",
      "description": "Content for Monday broadcasts",
      "is_active": true,
      "created_at": "2026-05-23T14:30:00Z"
    }
  ]
}
```

---

## Folder Schedules

### Create Folder Schedule

**Endpoint:** `POST /api/v1/audio/playlists/{playlist_id}/folder-schedules`

**Request (Recurring Daily):**
```json
{
  "folder_id": "uuid",
  "start_time": "06:00",
  "end_time": "12:00",
  "days_of_week": [1, 2, 3, 4, 5],
  "play_mode": "sequential",
  "priority": 50,
  "is_active": true
}
```

**Request (One-Time Schedule):**
```json
{
  "folder_id": "uuid",
  "starts_at": "2026-06-01T06:00:00Z",
  "ends_at": "2026-06-01T12:00:00Z",
  "play_mode": "sequential",
  "priority": 50,
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "playlist_id": "uuid",
  "folder_id": "uuid",
  "start_time": "06:00",
  "end_time": "12:00",
  "days_of_week": [1, 2, 3, 4, 5],
  "starts_at": null,
  "ends_at": null,
  "play_mode": "sequential",
  "priority": 50,
  "is_active": true,
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

**Validation:**
- Either (start_time + end_time + days_of_week) OR (starts_at + ends_at)
- start_time must be < end_time (same day)
- starts_at must be < ends_at (absolute datetime)
- days_of_week: array of 0-6 (0=Sunday, 6=Saturday)
- play_mode: "sequential" | "shuffle" | "loop"
- priority: 0-100
- folder_id must exist
- playlist_id must exist

**Business Logic:**
- If start_time passes (e.g., 06:00 in the past), schedule triggers next occurrence
- If ends_at is in past, schedule is archived automatically
- Multiple schedules on same folder allowed (e.g., morning + afternoon)

---

### Update Folder Schedule

**Endpoint:** `PUT /api/v1/audio/playlists/{playlist_id}/folder-schedules/{schedule_id}`

**Request:**
```json
{
  "start_time": "07:00",
  "end_time": "13:00",
  "play_mode": "shuffle",
  "priority": 75,
  "is_active": true
}
```

**Response (200 OK):** Same as Create response with updated fields

---

### Delete Folder Schedule

**Endpoint:** `DELETE /api/v1/audio/playlists/{playlist_id}/folder-schedules/{schedule_id}`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "message": "Folder schedule deleted",
  "playlist_id": "uuid"
}
```

---

## Audio Spots

### Create Spot

**Endpoint:** `POST /api/v1/audio/spots`

**Request:**
```json
{
  "name": "Coffee Shop Special",
  "description": "30-second promotional spot",
  "track_id": "uuid",
  "status": "active",
  "insertion_policy": "fade_mix"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Coffee Shop Special",
  "description": "30-second promotional spot",
  "track_id": "uuid",
  "status": "active",
  "insertion_policy": "fade_mix",
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

**Validation:**
- name: required, max 255 chars
- track_id: required, must exist
- status: "draft" | "active" | "archived"
- insertion_policy: "interrupt" | "wait_silence" | "fade_mix"

---

### Get Spot

**Endpoint:** `GET /api/v1/audio/spots/{spot_id}`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Coffee Shop Special",
  "description": "30-second promotional spot",
  "track_id": "uuid",
  "status": "active",
  "insertion_policy": "fade_mix",
  "tenant_id": "uuid",
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

---

### List Spots

**Endpoint:** `GET /api/v1/audio/spots?status=active&limit=20&offset=0`

**Query Parameters:**
- `status` (optional): "draft" | "active" | "archived"
- `limit` (default: 20)
- `offset` (default: 0)

**Response (200 OK):**
```json
{
  "total": 8,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "id": "uuid",
      "name": "Coffee Shop Special",
      "description": "30-second promotional spot",
      "track_id": "uuid",
      "status": "active",
      "insertion_policy": "fade_mix",
      "created_at": "2026-05-23T14:30:00Z"
    }
  ]
}
```

---

### Update Spot

**Endpoint:** `PUT /api/v1/audio/spots/{spot_id}`

**Request:**
```json
{
  "name": "Coffee Shop Special (Updated)",
  "status": "active",
  "insertion_policy": "interrupt"
}
```

**Response (200 OK):** Updated spot object

---

## Spot Schedules

### Create Spot Schedule

**Endpoint:** `POST /api/v1/audio/playlists/{playlist_id}/spot-schedules`

**Request:**
```json
{
  "spot_id": "uuid",
  "interval_seconds": 1800,
  "start_time": "06:00",
  "end_time": "22:00",
  "priority": 100,
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "playlist_id": "uuid",
  "spot_id": "uuid",
  "interval_seconds": 1800,
  "start_time": "06:00",
  "end_time": "22:00",
  "priority": 100,
  "is_active": true,
  "created_at": "2026-05-23T14:30:00Z",
  "updated_at": "2026-05-23T14:30:00Z"
}
```

**Validation:**
- spot_id: required, must exist, must be active status
- interval_seconds: required, must be > 0 (e.g., 1800 = 30 minutes)
- start_time < end_time (daily window)
- priority: 0-100 (higher = plays sooner)
- Unique constraint: (spot_id, playlist_id) — cannot schedule same spot twice in same playlist
- If duplicate attempted, return 409 Conflict with message

**Business Logic:**
- Spot plays every `interval_seconds` within `start_time` to `end_time` window
- If current time is outside window, next play is calculated for tomorrow
- If `interval_seconds` = 1800 and window is 6h (6:00-12:00), spots play at: 6:00, 6:30, 7:00, ..., 11:30

---

### Update Spot Schedule

**Endpoint:** `PUT /api/v1/audio/playlists/{playlist_id}/spot-schedules/{schedule_id}`

**Request:**
```json
{
  "interval_seconds": 3600,
  "start_time": "07:00",
  "end_time": "23:00",
  "priority": 75,
  "is_active": true
}
```

**Response (200 OK):** Updated schedule object

---

### Delete Spot Schedule

**Endpoint:** `DELETE /api/v1/audio/playlists/{playlist_id}/spot-schedules/{schedule_id}`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "message": "Spot schedule deleted",
  "playlist_id": "uuid"
}
```

---

## Playback Events

### Log Playback Event

**Endpoint:** `POST /api/v1/audio/events`

**Request (Track Started):**
```json
{
  "device_id": "uuid",
  "playlist_id": "uuid",
  "track_id": "uuid",
  "event_type": "track_started",
  "result": "success",
  "started_at": "2026-05-23T14:30:00Z"
}
```

**Request (Track Ended):**
```json
{
  "device_id": "uuid",
  "playlist_id": "uuid",
  "track_id": "uuid",
  "event_type": "track_ended",
  "result": "success",
  "started_at": "2026-05-23T14:30:00Z",
  "ended_at": "2026-05-23T14:33:00Z",
  "duration_seconds": 180
}
```

**Request (Spot Started):**
```json
{
  "device_id": "uuid",
  "playlist_id": "uuid",
  "spot_id": "uuid",
  "event_type": "spot_started",
  "result": "success",
  "started_at": "2026-05-23T14:33:00Z"
}
```

**Request (Error):**
```json
{
  "device_id": "uuid",
  "playlist_id": "uuid",
  "track_id": "uuid",
  "event_type": "error",
  "result": "failed",
  "error_message": "Failed to load audio file from /media/audio/tracks/xyz.mp3",
  "timestamp": "2026-05-23T14:30:00Z"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "device_id": "uuid",
  "playlist_id": "uuid",
  "track_id": null,
  "spot_id": null,
  "event_type": "track_started",
  "result": "success",
  "started_at": "2026-05-23T14:30:00Z",
  "ended_at": null,
  "duration_seconds": null,
  "error_message": null,
  "metadata": null,
  "created_at": "2026-05-23T14:30:00Z"
}
```

**Validation:**
- device_id: required, UUID format (validation: does device exist?)
- playlist_id: optional (nullable), UUID format if provided
- track_id | spot_id: at least one required
- event_type: "track_started" | "track_ended" | "spot_started" | "spot_ended" | "error"
- result: "success" | "failed"
- started_at: required, ISO 8601 format, must be <= now
- ended_at: optional, must be >= started_at if provided
- duration_seconds: optional, must be > 0 if provided
- For track_ended: duration_seconds should match (ended_at - started_at)

**Frontend Implementation Notes:**
- Always include `started_at` timestamp when logging
- Call logTrackStarted immediately when track begins
- Call logTrackEnded when currentTime reaches duration (from player ended event)
- Batch events every 5 seconds or 10 events (whichever comes first)
- Flush remaining events on page unload (beforeunload)
- Do NOT validate device_id client-side; backend will reject invalid IDs

---

### List Playback Events

**Endpoint:** `GET /api/v1/audio/events?device_id={uuid}&playlist_id={uuid}&limit=100&offset=0`

**Query Parameters:**
- `device_id` (optional): Filter by device
- `playlist_id` (optional): Filter by playlist
- `event_type` (optional): "track_started" | "track_ended" etc.
- `start_date` (optional): ISO 8601 date, filter >= start_date
- `end_date` (optional): ISO 8601 date, filter <= end_date
- `limit` (default: 100, max: 1000)
- `offset` (default: 0)

**Response (200 OK):**
```json
{
  "total": 2847,
  "limit": 100,
  "offset": 0,
  "items": [
    {
      "id": "uuid",
      "device_id": "uuid",
      "playlist_id": "uuid",
      "track_id": "uuid",
      "event_type": "track_started",
      "result": "success",
      "started_at": "2026-05-23T14:30:00Z",
      "ended_at": null,
      "duration_seconds": null,
      "created_at": "2026-05-23T14:30:00Z"
    }
  ]
}
```

---

## Error Responses

### Standard Error Response (400, 404, 409, 422, 500)

```json
{
  "error": "validation_error",
  "message": "Validation failed",
  "details": [
    {
      "field": "start_time",
      "message": "start_time must be before end_time"
    }
  ],
  "request_id": "uuid"
}
```

### Common Error Codes

| Code | Status | Scenario |
|------|--------|----------|
| `validation_error` | 422 | Request body fails schema validation |
| `not_found` | 404 | Resource doesn't exist |
| `conflict` | 409 | Duplicate spot schedule, unique constraint |
| `invalid_state` | 400 | Folder scheduled before track added |
| `access_denied` | 403 | Tenant authorization failed |
| `file_error` | 400 | Audio file upload failed (size, format) |
| `device_not_found` | 404 | Device ID in event doesn't exist |
| `internal_error` | 500 | Unexpected server error |

### Example: Duplicate Spot Schedule

**Request:**
```json
POST /api/v1/audio/playlists/uuid/spot-schedules
{
  "spot_id": "spot-uuid",
  "interval_seconds": 1800,
  "start_time": "06:00",
  "end_time": "22:00"
}
```

**Response (409 Conflict):**
```json
{
  "error": "conflict",
  "message": "Spot already scheduled in this playlist",
  "details": {
    "spot_id": "spot-uuid",
    "playlist_id": "uuid",
    "existing_schedule_id": "schedule-uuid"
  },
  "request_id": "uuid"
}
```

---

## Timestamps & Timezones

### Standard for All Responses

**Format:** ISO 8601 UTC (Zulu time)
```
Example: 2026-05-23T14:30:00Z
         2026-05-23T14:30:00.123Z (with milliseconds)
```

**Timezone:** Always UTC on backend
- Database stores in UTC
- API always returns UTC
- Frontend must convert to local timezone for display
- Frontend sends UTC timestamps (use `new Date().toISOString()`)

### Fields Present on All Resources

```
created_at: ISO 8601, when record created (backend)
updated_at: ISO 8601, last modification (backend, auto-updated)
created_by: UUID (optional, for audit)
```

### Time vs DateTime Distinction

**time fields** (no date, recurring daily):
- Format: "HH:MM" (24-hour)
- Example: "06:00", "14:30", "23:59"
- Used in: start_time, end_time (folder schedules, spot schedules)
- Interpretation: Every day at this time

**datetime fields** (absolute point in time):
- Format: ISO 8601 UTC
- Example: "2026-05-23T14:30:00Z"
- Used in: starts_at, ends_at (one-time schedules), timestamps
- Interpretation: Specific date and time

### Frontend Display Example

```javascript
// Backend returns: "2026-05-23T14:30:00Z"
const utcTime = new Date("2026-05-23T14:30:00Z");
const localTime = utcTime.toLocaleString('pt-BR');
// Display: "23/05/2026 11:30:00" (if in São Paulo timezone)
```

---

## Frontend Integration Checklist

### Initial Load (PlayerAudio Page)

- [ ] GET `/api/v1/audio/playlists/{id}?include=all` — Load playlist with all relations
- [ ] If `include=all` not supported, make 4 separate calls:
  - [ ] GET `/api/v1/audio/playlists/{id}` — Playlist metadata
  - [ ] GET `/api/v1/audio/playlists/{id}/items` — Tracks
  - [ ] GET `/api/v1/audio/playlists/{id}/folder-schedules` — Folder schedules
  - [ ] GET `/api/v1/audio/playlists/{id}/spot-schedules` — Spot schedules
- [ ] Handle 404 if playlist doesn't exist
- [ ] Display loading state during fetch

### Audio Upload

- [ ] POST `/api/v1/audio/tracks/upload-multiple` with FormData
- [ ] Check `errors` array (default to [] not null)
- [ ] Display per-file error messages for failed uploads
- [ ] Add uploaded tracks to folder

### Schedule Management

- [ ] POST `/api/v1/audio/playlists/{id}/folder-schedules` with validation
  - [ ] Either (start_time + end_time + days) OR (starts_at + ends_at)
- [ ] POST `/api/v1/audio/playlists/{id}/spot-schedules`
  - [ ] Catch 409 Conflict for duplicate spot_id
  - [ ] Validate interval_seconds > 0 client-side before submit
- [ ] PUT to update schedules
- [ ] DELETE to remove schedules

### Playback Events

- [ ] Log track_started immediately when audio element plays
- [ ] Log track_ended when audio ended event fires
- [ ] Include started_at timestamp (ISO 8601 UTC)
- [ ] Batch events (5 sec delay or 10 events)
- [ ] Flush on beforeunload
- [ ] Handle network errors gracefully (retry queue)

### Enum Handling

- [ ] Map frontend AUDIO_STATE to backend event_type
- [ ] Ensure AUDIO_MODE matches backend play_mode values
- [ ] Validate enum values before sending (SELECT dropdowns)
- [ ] Handle unexpected enum values in responses (log error, fallback to default)

---

## Known Issues & TODOs

1. **Device State Sync** — No endpoint defined for getting current playback state. Implement:
   - `GET /api/v1/devices/{id}/current-state` — Returns what's currently playing
   - Use WebSocket or polling for real-time updates

2. **Folder Relationship** — Verify `GET /api/v1/audio/folders/{id}` behavior:
   - Should tracks be eager-loaded or lazy?
   - Recommend: Lazy (separate endpoint) for consistency

3. **Unique Constraint Messaging** — Verify 409 response format when duplicate spot schedule attempted

4. **Pagination Consistency** — All list endpoints should follow same format:
   - `{total, limit, offset, items}`
   - Confirm max limits for each endpoint

5. **Error Detail Depth** — Validation errors should include field path for nested objects

6. **Rate Limiting** — Define rate limits for event logging endpoint (prevents event spam)

7. **Batch Event Limits** — POST `/api/v1/audio/events` should accept array or single object?
   - Current spec: single object per request
   - Recommend: Support both `POST /events` (single) and `POST /events/batch` (array)

---

**Document Status:** Ready for Backend Implementation Review  
**Next Step:** Backend team confirms response structures match these contracts, adjust as needed.
