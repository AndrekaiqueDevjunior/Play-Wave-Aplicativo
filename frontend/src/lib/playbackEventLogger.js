/**
 * Playback Event Logger — Registra eventos de reprodução no backend
 *
 * POST /audio/events espera List[AudioPlaybackEventCreate] (array JSON).
 * Os eventos são acumulados e enviados em um único request a cada BATCH_DELAY ms
 * ou quando BATCH_SIZE é atingido.
 */

import { apiFetch } from "@/api/http";

const BATCH_DELAY = 5000;
const BATCH_SIZE = 10;

let eventQueue = [];
let batchTimer = null;

/**
 * Enfileira um evento. Aceita campos do schema AudioPlaybackEventCreate:
 *   device_id, event_type, playlist_id?, track_id?, spot_id?,
 *   result?, started_at?, ended_at?, duration_seconds?, error_message?, metadata?
 */
export async function logPlaybackEvent(event) {
  if (!event.device_id || !event.event_type) {
    console.warn("[playbackLogger] evento inválido ignorado:", event);
    return;
  }

  // started_at obrigatório pelo backend mas opcional no schema — preenche se ausente
  const entry = {
    started_at: new Date().toISOString(),
    ...event,
  };

  eventQueue.push(entry);

  if (eventQueue.length >= BATCH_SIZE) {
    await flushEvents();
  } else if (!batchTimer) {
    batchTimer = setTimeout(flushEvents, BATCH_DELAY);
  }
}

/**
 * Envia todos os eventos acumulados em UM único POST com array JSON.
 * Em caso de falha, re-enfileira para a próxima tentativa.
 */
export async function flushEvents() {
  if (eventQueue.length === 0) return;

  const batch = [...eventQueue];
  eventQueue = [];

  if (batchTimer) {
    clearTimeout(batchTimer);
    batchTimer = null;
  }

  try {
    await apiFetch("/audio/events", {
      method: "POST",
      body: JSON.stringify(batch),
    });
  } catch (err) {
    console.warn("[playbackLogger] flush falhou, re-enfileirando:", err);
    eventQueue.push(...batch);
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

export async function logTrackStarted(deviceId, trackId, playlistId = null, startedAt = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    track_id: trackId,
    playlist_id: playlistId,
    event_type: "track_started",
    result: "success",
    started_at: startedAt || new Date().toISOString(),
  });
}

export async function logTrackEnded(deviceId, trackId, durationSeconds = null, playlistId = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    track_id: trackId,
    playlist_id: playlistId,
    event_type: "track_ended",
    result: "success",
    ended_at: new Date().toISOString(),
    duration_seconds: durationSeconds,
  });
}

export async function logSpotStarted(deviceId, spotId, playlistId = null, startedAt = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    spot_id: spotId,
    playlist_id: playlistId,
    event_type: "spot_started",
    result: "success",
    started_at: startedAt || new Date().toISOString(),
  });
}

export async function logSpotEnded(deviceId, spotId, durationSeconds = null, playlistId = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    spot_id: spotId,
    playlist_id: playlistId,
    event_type: "spot_ended",
    result: "success",
    ended_at: new Date().toISOString(),
    duration_seconds: durationSeconds,
  });
}

export async function logPlaybackError(deviceId, errorMessage, trackId = null, spotId = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    track_id: trackId,
    spot_id: spotId,
    event_type: "error",
    result: "failed",
    error_message: errorMessage,
    started_at: new Date().toISOString(),
  });
}

// ── Flush ao sair da página ──────────────────────────────────────────────────
if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    flushEvents();
  });
}
