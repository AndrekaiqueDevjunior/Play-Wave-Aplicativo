/**
 * Testes SPEC 007 Fase E — playbackEventLogger (lib/playbackEventLogger.js)
 *
 * Cobre: validação de eventos, flush em lote, helpers logTrackStarted/logTrackEnded.
 *
 * ATENÇÃO: o módulo usa estado de módulo (eventQueue, batchTimer).
 * vi.resetModules() + re-import em cada teste garante isolamento.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock apiFetch antes de qualquer import do logger
vi.mock("@/api/http", () => ({
  apiFetch: vi.fn().mockResolvedValue(null),
}));

// Cada describe-block re-importa o módulo para garantir estado limpo
beforeEach(() => {
  vi.resetModules();
  vi.clearAllMocks();
});

// ── Validação de eventos ──────────────────────────────────────────────────────

describe("logPlaybackEvent — validação", () => {
  it("descarta evento sem device_id (não chama apiFetch)", async () => {
    const { logPlaybackEvent } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await logPlaybackEvent({ event_type: "track_started" });

    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("descarta evento sem event_type (não chama apiFetch)", async () => {
    const { logPlaybackEvent } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await logPlaybackEvent({ device_id: "dev-1" });

    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("aceita evento com device_id + event_type — enfileira sem chamar apiFetch (abaixo do BATCH_SIZE)", async () => {
    const { logPlaybackEvent } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await logPlaybackEvent({ device_id: "dev-1", event_type: "track_started" });

    // Com apenas 1 evento (< BATCH_SIZE=10), não deve ter enviado ainda
    expect(apiFetch).not.toHaveBeenCalled();
  });
});

// ── Flush em lote ─────────────────────────────────────────────────────────────

describe("flushEvents — batch", () => {
  it("flushEvents com fila vazia não chama apiFetch", async () => {
    const { flushEvents } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await flushEvents();

    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("flushEvents envia array completo em UM único POST para /audio/events", async () => {
    const { logPlaybackEvent, flushEvents } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await logPlaybackEvent({ device_id: "dev-1", event_type: "track_started" });
    await logPlaybackEvent({ device_id: "dev-1", event_type: "track_ended" });
    await logPlaybackEvent({ device_id: "dev-1", event_type: "track_started" });

    await flushEvents();

    expect(apiFetch).toHaveBeenCalledOnce();
    expect(apiFetch).toHaveBeenCalledWith(
      "/audio/events",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("o body enviado é JSON com array de eventos (não objetos individuais)", async () => {
    const { logPlaybackEvent, flushEvents } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await logPlaybackEvent({ device_id: "dev-1", event_type: "track_started" });
    await logPlaybackEvent({ device_id: "dev-2", event_type: "track_ended" });

    await flushEvents();

    expect(apiFetch).toHaveBeenCalledOnce();
    const [, callOptions] = apiFetch.mock.calls[0];
    const parsedBody = JSON.parse(callOptions.body);
    expect(Array.isArray(parsedBody)).toBe(true);
    expect(parsedBody).toHaveLength(2);
  });
});

// ── Helpers logTrackStarted / logTrackEnded ───────────────────────────────────

describe("logTrackStarted / logTrackEnded helpers", () => {
  it("logTrackStarted(deviceId, trackId, playlistId) enfileira evento com event_type='track_started'", async () => {
    const { logTrackStarted, flushEvents } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await logTrackStarted("dev-1", "track-42", "playlist-7");
    await flushEvents();

    expect(apiFetch).toHaveBeenCalledOnce();
    const [, callOptions] = apiFetch.mock.calls[0];
    const parsedBody = JSON.parse(callOptions.body);
    expect(parsedBody[0]).toMatchObject({
      device_id: "dev-1",
      track_id: "track-42",
      playlist_id: "playlist-7",
      event_type: "track_started",
    });
  });

  it("logTrackEnded(deviceId, trackId, durationSeconds, playlistId) enfileira com event_type='track_ended', duration_seconds e ended_at", async () => {
    const { logTrackEnded, flushEvents } = await import("@/lib/playbackEventLogger");
    const { apiFetch } = await import("@/api/http");

    await logTrackEnded("dev-1", "track-99", 180, "playlist-3");
    await flushEvents();

    expect(apiFetch).toHaveBeenCalledOnce();
    const [, callOptions] = apiFetch.mock.calls[0];
    const parsedBody = JSON.parse(callOptions.body);
    expect(parsedBody[0]).toMatchObject({
      device_id: "dev-1",
      track_id: "track-99",
      playlist_id: "playlist-3",
      event_type: "track_ended",
      duration_seconds: 180,
    });
    expect(parsedBody[0].ended_at).toBeTruthy();
  });
});
