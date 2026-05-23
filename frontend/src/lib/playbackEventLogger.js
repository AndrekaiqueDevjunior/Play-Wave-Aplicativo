/**
 * Playback Event Logger — Registra eventos de reprodução no backend
 *
 * Chamadas assíncronas para registrar:
 * - track_started
 * - track_ended
 * - spot_started
 * - spot_ended
 * - error
 */

import { apiFetch } from "@/api/http";

const BATCH_DELAY = 5000; // Agrupa eventos a cada 5s
const BATCH_SIZE = 10;   // Max eventos antes de enviar

let eventQueue = [];
let batchTimer = null;

/**
 * Registra evento de playback
 */
export async function logPlaybackEvent(event) {
  // Validar evento
  if (!event.device_id || !event.event_type) {
    console.warn("Invalid playback event", event);
    return;
  }

  eventQueue.push({
    timestamp: new Date().toISOString(),
    ...event,
  });

  // Enviar se batch cheio
  if (eventQueue.length >= BATCH_SIZE) {
    await flushEvents();
  } else {
    // Agendar flush
    if (!batchTimer) {
      batchTimer = setTimeout(flushEvents, BATCH_DELAY);
    }
  }
}

/**
 * Envia eventos acumulados
 */
export async function flushEvents() {
  if (eventQueue.length === 0) return;

  const events = [...eventQueue];
  eventQueue = [];

  if (batchTimer) {
    clearTimeout(batchTimer);
    batchTimer = null;
  }

  try {
    // Enviar em lote para otimizar
    await Promise.all(
      events.map(event =>
        apiFetch("/audio/events", {
          method: "POST",
          body: JSON.stringify(event),
        }).catch(err => {
          console.error("Failed to log playback event:", err);
          // Re-queue se falhar
          eventQueue.push(event);
        })
      )
    );
  } catch (error) {
    console.error("Error flushing playback events:", error);
  }
}

/**
 * Helpers de convenience
 */

export async function logTrackStarted(deviceId, trackId, playlistId = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    track_id: trackId,
    playlist_id: playlistId,
    event_type: "track_started",
    result: "success",
  });
}

export async function logTrackEnded(deviceId, trackId, durationSeconds = null, playlistId = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    track_id: trackId,
    playlist_id: playlistId,
    event_type: "track_ended",
    result: "success",
    duration_seconds: durationSeconds,
  });
}

export async function logSpotStarted(deviceId, spotId, playlistId = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    spot_id: spotId,
    playlist_id: playlistId,
    event_type: "spot_started",
    result: "success",
  });
}

export async function logSpotEnded(deviceId, spotId, durationSeconds = null, playlistId = null) {
  await logPlaybackEvent({
    device_id: deviceId,
    spot_id: spotId,
    playlist_id: playlistId,
    event_type: "spot_ended",
    result: "success",
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
  });
}

/**
 * Integração com AudioManager
 * Chama quando estado muda
 */
export function createAudioEventHandler(deviceId, playlistId) {
  const startTimes = {};

  return async (state) => {
    // Track started
    if (state.radioQueue && state.radioQueue.length > 0) {
      const currentTrack = state.radioQueue[state.radioIndex];
      if (currentTrack && !startTimes[currentTrack.id]) {
        startTimes[currentTrack.id] = Date.now();
        await logTrackStarted(deviceId, currentTrack.id, playlistId);
      }
    }

    // On track ended: log duration
    // (Chamado quando nextTrack é invocado)
  };
}

/**
 * Garante envio ao descarregar página
 */
if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    flushEvents();
  });
}
