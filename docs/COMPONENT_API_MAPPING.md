# Component-to-API Mapping

**Purpose:** Quick reference showing which frontend components depend on which API endpoints.

---

## PlayerAudio Page

**File:** `frontend/src/pages/PlayerAudio.jsx`

**Load Order:**
1. **Fetch playlist** — `GET /api/v1/audio/playlists/{id}?include=all`
   - Expected response: Full playlist with items, folder_schedules, spot_schedules
   - Fallback: Make 4 separate requests if include parameter not supported
   - Mock data location: lines 53-103

2. **Initialize AudioManager** — `initPlayers(radioRef, mediaRef, spotRef)`
   - No API call, internal state management
   - Creates singleton manager with 3 audio elements

3. **Start playback** — `playRadio()` via AudioManager
   - No API call, plays first track from loaded queue
   - Uses mock tracks from playlist.items

**Event Logging:**
- `logTrackStarted()` → `POST /api/v1/audio/events`
- `logSpotStarted()` → `POST /api/v1/audio/events`
- Batch interval: 5000ms
- Batch size: 10 events

**State Display:**
- Renders current state from `state.current` (AUDIO_STATE enum)
- Renders volume from `state.volume` (0-1 range)
- Renders playlist items in queue

**Critical Issue:** 
- Uses mock playlist structure, not real API
- Schedule resolvers (folder + spot) are stubbed (lines 157-179)
- **NEEDS:** Actual API integration for real playlists

---

## AudioControlPanel Component

**File:** `frontend/src/components/audio/AudioControlPanel.jsx`

**Dependencies:**
- `useAudioManager()` hook — Gets current state from singleton
- No API calls (UI only)
- Displays state from manager

**State Expected from AudioManager:**
- `current`: AUDIO_STATE enum value ("radio" | "media_audio" | "spot" | "silent")
- `isPlaying`: boolean
- `currentTime`: number (seconds)
- `duration`: number (seconds)
- `radioMode`: AUDIO_MODE enum value ("sequential" | "shuffle" | "loop")

**Actions:**
- `pause()` → no API, internal
- `resume()` → no API, internal
- `previousTrack()` → no API, internal (modifies queue index)
- `nextTrack()` → no API, internal (modifies queue index)
- `setRadioMode(mode)` → no API, internal (updates radioMode state)
- `setVolume(v)` → no API, internal (applies to all 3 audio elements)

**Validation:**
- All state transformations happen client-side
- No schema validation needed (manager controls types)

---

## MultiAudioUploadDialog Component

**File:** `frontend/src/components/audio/MultiAudioUploadDialog.jsx` (assumed)

**Endpoint:**
- `POST /api/v1/audio/tracks/upload-multiple`

**Request Format:**
- FormData with:
  - `files[]`: File objects (audio/mp3, audio/wav, video/mp4, etc.)
  - `category`: string ("background" | "spot" | "jingle")
  - `description`: string (optional)

**Expected Response:**
```javascript
{
  uploaded: [
    {
      id: "uuid",
      name: "filename.mp3",
      file_url: "/media/audio/tracks/uuid.mp3",
      duration_seconds: 180,
      category: "background",
      created_at: "2026-05-23T14:30:00Z",
      // ... other fields
    }
  ],
  errors: [] // MUST be array, never null
}
```

**Error Handling:**
- If `errors` array is empty: All files uploaded successfully
- If `errors` has items: Partial success, display per-file error messages
- Handle both (206 Partial Content) and (200 OK) responses

**Parent Component Hook:**
- `onSuccess(response)` callback with `{uploaded, errors}`

**Validation:**
- File size validation (max 100MB per file, backend enforced)
- File type validation (MIME type, backend enforced)
- Duration auto-detected by backend (ffprobe)
- Do NOT send duration from frontend

---

## AudioFolderManager Component

**File:** `frontend/src/components/audio/AudioFolderManager.jsx` (assumed)

**Endpoints:**

### List Folders
- `GET /api/v1/audio/folders?limit=50&offset=0`
- Response: `{total, limit, offset, items: [{id, name, description, is_active, track_count}]}`

### Create Folder
- `POST /api/v1/audio/folders`
- Request: `{name, description, is_active}`
- Response: Full folder object with id

### Update Folder
- `PUT /api/v1/audio/folders/{id}`
- Request: `{name, description, is_active}`
- Response: Updated folder

### Get Folder
- `GET /api/v1/audio/folders/{id}`
- Response: Folder object (WITHOUT tracks array, see below)

### Get Folder Tracks
- `GET /api/v1/audio/folders/{id}/tracks?limit=50&offset=0`
- Response: `{folder_id, total, limit, offset, items: [{id, track_id, name, file_url, duration_seconds}]}`

### Add Tracks to Folder
- `POST /api/v1/audio/folders/{id}/tracks`
- Request: `{track_ids: ["uuid-1", "uuid-2"]}`
- Response: `{folder_id, added: 3, total_tracks: 15}`

### Remove Track from Folder
- `DELETE /api/v1/audio/folders/{id}/tracks/{track_id}`
- Response: `{folder_id, track_id, remaining: 14}`

**Critical Mismatch:**
- Component likely assumes `folder.tracks` is populated array
- **ACTUAL:** Must fetch separately via `GET /api/v1/audio/folders/{id}/tracks`
- **FIX:** After getting folder, immediately fetch its tracks

**Expected Data Flow:**
```javascript
// WRONG:
const folder = await GET(`/audio/folders/${id}`);
console.log(folder.tracks); // undefined!

// CORRECT:
const folder = await GET(`/audio/folders/${id}`);
const tracks = await GET(`/audio/folders/${id}/tracks`);
console.log(tracks.items); // [{...}, {...}]
```

---

## AudioScheduleBuilder Component

**File:** `frontend/src/components/audio/AudioScheduleBuilder.jsx` (assumed)

**Endpoint:**
- `POST /api/v1/audio/playlists/{playlist_id}/folder-schedules`

**Request Format (Current UI):**
```javascript
{
  folder_id: "uuid",
  start_time: "06:00",
  end_time: "12:00",
  priority: 50,
  play_mode: "sequential",
  is_active: true
}
```

**Backend Expects (Either/Or):**

**Option A — Recurring (Daily):**
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

**Option B — One-Time:**
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

**Current Mismatch:**
- Component sends only start_time + end_time (missing days_of_week)
- Backend expects either complete recurring OR complete one-time config
- Missing required field will cause 422 validation error

**FIX Options:**
1. Add `days_of_week` selector to component (recurring daily)
2. Add date picker for starts_at + ends_at (one-time)
3. Have radio button: "Daily" vs "One-Time"

**Update Endpoint:**
- `PUT /api/v1/audio/playlists/{playlist_id}/folder-schedules/{schedule_id}`
- Same request format as create

**Delete Endpoint:**
- `DELETE /api/v1/audio/playlists/{playlist_id}/folder-schedules/{schedule_id}`

---

## AudioSpotScheduleManager Component

**File:** `frontend/src/components/audio/AudioSpotScheduleManager.jsx` (assumed)

**Tabs: Spots Management & Schedule Management**

### Spots Tab

#### List Spots
- `GET /api/v1/audio/spots?status=active&limit=20&offset=0`
- Response: `{total, limit, offset, items: [{id, name, description, track_id, status, insertion_policy}]}`

#### Create Spot
- `POST /api/v1/audio/spots`
- Request: `{name, description, track_id, status, insertion_policy}`
- Response: Full spot object

#### Update Spot
- `PUT /api/v1/audio/spots/{id}`
- Request: `{name, description, status, insertion_policy}`

#### Delete Spot
- `DELETE /api/v1/audio/spots/{id}`

**Expected Data from Response:**
```javascript
{
  id: "uuid",
  name: "Coffee Special",
  description: "30-sec promo",
  track_id: "uuid",
  status: "active", // enum: draft | active | archived
  insertion_policy: "fade_mix", // enum: interrupt | wait_silence | fade_mix
  created_at: "2026-05-23T14:30:00Z"
}
```

### Schedule Tab

#### List Spot Schedules
- `GET /api/v1/audio/playlists/{playlist_id}/spot-schedules?limit=20&offset=0`
- Response: `{total, limit, offset, items: [{id, spot_id, interval_seconds, start_time, end_time, priority, is_active}]}`

#### Create Spot Schedule
- `POST /api/v1/audio/playlists/{playlist_id}/spot-schedules`
- Request:
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

**Validation Required:**
- `interval_seconds` > 0 (e.g., 1800 = 30 min)
- `start_time` < `end_time`
- `spot_id` must be active status
- Unique constraint: (spot_id, playlist_id)

**Error Scenario:**
- If user tries to add same spot twice to same playlist:
  - Backend returns: **409 Conflict**
  - Response:
```json
{
  "error": "conflict",
  "message": "Spot already scheduled in this playlist",
  "details": {
    "spot_id": "uuid",
    "existing_schedule_id": "uuid"
  }
}
```
  - **UI Must:** Prevent duplicate submission or handle 409 gracefully

#### Update Spot Schedule
- `PUT /api/v1/audio/playlists/{playlist_id}/spot-schedules/{schedule_id}`

#### Delete Spot Schedule
- `DELETE /api/v1/audio/playlists/{playlist_id}/spot-schedules/{schedule_id}`

**Critical Issue:**
- No client-side validation shown for `interval_seconds > 0`
- Must add validation to prevent invalid schedule creation
- Must catch 409 conflict and display helpful message

---

## AudioManager (Hook & Library)

**Files:**
- `frontend/src/hooks/useAudioManager.js`
- `frontend/src/lib/audioManager.js`

**No Direct API Calls**

**Responsibilities:**
- Singleton state management for 3 audio players
- Volume control (applies to all players)
- Queue management (next/previous track)
- Fade in/out animations
- Event emission for state changes
- Subscription pattern for React components

**State Structure:**
```javascript
{
  current: "radio" | "media_audio" | "spot" | "silent",
  isPlaying: boolean,
  currentTime: number,
  duration: number,
  volume: 0.0 - 1.0,
  fadeMs: 200,
  radioMode: "sequential" | "shuffle" | "loop",
  radioQueue: Array<Track>,
  radioIndex: number
}
```

**No Schema Validation:** Manager doesn't validate backend responses.
- Frontend must validate before passing to manager
- No type checking on track objects

---

## playbackEventLogger (Event Logging)

**File:** `frontend/src/lib/playbackEventLogger.js`

**Endpoint:** `POST /api/v1/audio/events`

**Batching Logic:**
- Queue events in memory
- Send when batch reaches 10 events OR 5 seconds elapsed
- On page unload: `beforeunload` → `flushEvents()`

**Events Logged:**

### Track Started
- `logTrackStarted(deviceId, trackId, playlistId)`
- Payload: `{device_id, track_id, playlist_id, event_type: "track_started", result: "success"}`

### Track Ended
- `logTrackEnded(deviceId, trackId, durationSeconds, playlistId)`
- Payload: `{device_id, track_id, playlist_id, event_type: "track_ended", result: "success", duration_seconds}`

### Spot Started
- `logSpotStarted(deviceId, spotId, playlistId)`
- Payload: `{device_id, spot_id, playlist_id, event_type: "spot_started", result: "success"}`

### Spot Ended
- `logSpotEnded(deviceId, spotId, durationSeconds, playlistId)`
- Payload: `{device_id, spot_id, playlist_id, event_type: "spot_ended", result: "success", duration_seconds}`

### Error
- `logPlaybackError(deviceId, errorMessage, trackId, spotId)`
- Payload: `{device_id, track_id, spot_id, event_type: "error", result: "failed", error_message}`

**Missing from Current Implementation:**
- No `started_at` timestamp sent to backend
- Backend expects ISO 8601 timestamp
- **FIX:** Add timestamp field to all events

**Current Missing Field:**
```javascript
// CURRENT:
{device_id, track_id, event_type, result}

// SHOULD BE:
{device_id, track_id, event_type, result, started_at: "2026-05-23T14:30:00Z"}
```

**Error Handling:**
- Network errors caught, events re-queued
- Silent retry on failure (logs to console)
- No exponential backoff or max retry limit defined

---

## Integration Testing Checklist

### Before Testing

- [ ] Backend `/api/v1/audio/playlists` returns objects with `?include=all` parameter
- [ ] Backend returns empty arrays for `errors` in upload response (never null)
- [ ] Backend returns folder tracks via separate endpoint `/api/v1/audio/folders/{id}/tracks`
- [ ] Backend returns 409 Conflict when duplicate spot_id added to playlist
- [ ] Folder schedules accept either (start_time + days_of_week) OR (starts_at + ends_at)
- [ ] Playback events include timestamps

### During Testing

- [ ] PlayerAudio page loads playlist successfully
- [ ] Track list displays with correct duration formatting
- [ ] Upload dialog handles partial failures (some files OK, some error)
- [ ] Folder schedule form prevents submission if start_time >= end_time
- [ ] Spot schedule form prevents interval_seconds <= 0
- [ ] Duplicate spot schedule shows helpful 409 error
- [ ] Playback events are batched and sent to backend
- [ ] Events resume batching after page reload (if events in queue)

### Critical Paths

1. **Load & Play**
   - Load playlist
   - Load folder schedules
   - Load spot schedules
   - Start playback
   - Log events

2. **Upload & Add**
   - Upload audio files
   - Create folder
   - Add tracks to folder
   - Verify track_count updated

3. **Schedule & Play**
   - Create folder schedule (recurring daily)
   - Create spot schedule
   - Verify schedules render correctly
   - Verify no duplicate spots allowed

---

**Last Updated:** 2026-05-23  
**Status:** Ready for Integration Testing
